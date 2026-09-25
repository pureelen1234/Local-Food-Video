"""LocalFoodFilm.blend 렌더.
  blender -b LocalFoodFilm.blend --python scripts/render.py -- preview          # 960x540 전체
  blender -b LocalFoodFilm.blend --python scripts/render.py -- final            # 1920x1080 전체
  blender -b LocalFoodFilm.blend --python scripts/render.py -- stills 5,13,30   # 지정 초 정지 이미지
  blender -b LocalFoodFilm.blend --python scripts/render.py -- preview 400 600  # 프레임 구간만 (이어 렌더)
프레임은 output/frames_<quality>/ 에 JPG 로 저장되고, 이미 있는 프레임은 건너뛴다(중단 후 이어하기 가능).
마지막에 ffmpeg 로 MP4 를 만든다 (ffmpeg 가 없으면 Blender 내장 인코더 사용).
"""
import bpy
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, 'config.json'), encoding='utf-8'))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['preview']
mode = argv[0]
scene = bpy.context.scene
r = scene.render
q = CFG['render']['final' if mode == 'final' else 'preview']
r.resolution_x, r.resolution_y = q['width'], q['height']
r.resolution_percentage = 100
if hasattr(scene.eevee, 'taa_render_samples'):
    scene.eevee.taa_render_samples = q['samples']
r.image_settings.file_format = 'JPEG'
r.image_settings.quality = 93
fps = scene.render.fps


def find_ffmpeg():
    if os.environ.get('FFMPEG'):
        return os.environ['FFMPEG']
    if shutil.which('ffmpeg'):
        return shutil.which('ffmpeg')
    try:
        return subprocess.check_output(['python3', '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())']).decode().strip()
    except Exception:
        return None


if mode == 'stills':
    d = os.path.join(ROOT, 'output', 'stills')
    os.makedirs(d, exist_ok=True)
    for sec in [float(x) for x in argv[1].split(',')]:
        f = 1 + round(sec * fps)
        scene.frame_set(f)
        r.filepath = os.path.join(d, 'still_%05.1fs.jpg' % sec)
        bpy.ops.render.render(write_still=True)
        print('STILL', r.filepath)
    sys.exit(0)

fdir = os.path.join(ROOT, 'output', 'frames_' + mode)
os.makedirs(fdir, exist_ok=True)
f0 = int(argv[1]) if len(argv) > 1 else scene.frame_start
f1 = int(argv[2]) if len(argv) > 2 else scene.frame_end
import time
t0 = time.time()
for f in range(f0, f1 + 1):
    path = os.path.join(fdir, 'f_%04d.jpg' % f)
    if os.path.exists(path):
        continue
    scene.frame_set(f)
    r.filepath = path
    bpy.ops.render.render(write_still=True)
    if f % 24 == 0:
        print('FRAME %d/%d  %.0fs' % (f, f1, time.time() - t0), flush=True)

missing = [f for f in range(scene.frame_start, scene.frame_end + 1) if not os.path.exists(os.path.join(fdir, 'f_%04d.jpg' % f))]
if missing:
    print('구간 렌더 완료, 남은 프레임 %d개' % len(missing))
    sys.exit(0)
out = os.path.join(ROOT, q['file'])
os.makedirs(os.path.dirname(out), exist_ok=True)
ff = find_ffmpeg()
if ff:
    subprocess.check_call([ff, '-y', '-loglevel', 'error', '-framerate', str(fps), '-start_number', str(scene.frame_start),
                           '-i', os.path.join(fdir, 'f_%04d.jpg'), '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p',
                           '-movflags', '+faststart', out])
else:
    # Blender 내장 인코더: 저장된 프레임을 시퀀서로 다시 읽어 MP4 로 출력
    se = scene.sequence_editor_create()
    strip = se.sequences.new_image('frames', os.path.join(fdir, 'f_%04d.jpg' % scene.frame_start), 1, scene.frame_start)
    for f in range(scene.frame_start + 1, scene.frame_end + 1):
        strip.elements.append('f_%04d.jpg' % f)
    r.use_sequencer = True
    r.image_settings.file_format = 'FFMPEG'
    r.ffmpeg.format = 'MPEG4'
    r.ffmpeg.codec = 'H264'
    r.filepath = out
    bpy.ops.render.render(animation=True)
print('VIDEO_OK', out)

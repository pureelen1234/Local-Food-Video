"""0단계: 언리얼 5.8 파이썬 기능 점검 (마스터 맥북에서 실행).
- 추측으로 API 를 쓰지 않도록, 실제로 쓸 기능이 있는지 하나씩 시험한다.
- 새로 만드는 것은 모두 /Game/LocalFoodFilm/_Test 아래 (기존 Main 레벨은 건드리지 않음).
- 결과는 창으로 보여 주고, 프로젝트 Saved/lff_check.txt 에도 저장한다.
"""
import sys
import unreal

R = []


def ok(k, v=''):
    R.append('[OK] %s %s' % (k, v))


def ng(k, e=''):
    R.append('[NG] %s %s' % (k, e))


def step(name, fn):
    try:
        v = fn()
        ok(name, '' if v is None else v)
        return v
    except Exception as e:  # noqa: BLE001
        ng(name, repr(e)[:160])
        return None


ok('엔진', unreal.SystemLibrary.get_engine_version())
ok('Python', sys.version.split()[0])

for n in ('EditorActorSubsystem', 'LevelEditorSubsystem', 'EditorAssetSubsystem', 'MoviePipelineQueueSubsystem'):
    step('서브시스템 ' + n, lambda n=n: 'OK' if unreal.get_editor_subsystem(getattr(unreal, n)) else 'None')

for c in ('LevelSequence', 'LevelSequenceFactoryNew', 'MovieScene3DTransformTrack', 'MovieSceneCameraCutTrack',
          'MovieSceneAudioTrack', 'MovieSceneFadeTrack', 'MovieSceneComponentMaterialTrack', 'CineCameraActor',
          'MoviePipelinePIEExecutor', 'MoviePipelineAppleProResOutput', 'MoviePipelineImageSequenceOutput_PNG',
          'MoviePipelineCommandLineEncoder', 'MaterialEditingLibrary', 'MaterialInstanceConstantFactoryNew',
          'AssetImportTask', 'DirectionalLight', 'SkyAtmosphere', 'ExponentialHeightFog', 'SkyLight'):
    (ok if hasattr(unreal, c) else ng)('클래스 ' + c, '있음' if hasattr(unreal, c) else '없음')

ROOT = '/Game/LocalFoodFilm/_Test'
step('폴더 생성', lambda: unreal.EditorAssetLibrary.make_directory(ROOT))
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
at = unreal.AssetToolsHelpers.get_asset_tools()
step('테스트 레벨 생성', lambda: les.new_level(ROOT + '/LFF_TestLevel'))

# 재질: 색 파라미터가 있는 기본 재질 + 인스턴스
def make_mat():
    mel = unreal.MaterialEditingLibrary
    m = at.create_asset('M_LFF_TestColor', ROOT, unreal.Material, unreal.MaterialFactoryNew())
    p = mel.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -400, 0)
    p.set_editor_property('parameter_name', 'Color')
    p.set_editor_property('default_value', unreal.LinearColor(1, 0.2, 0.1, 1))
    mel.connect_material_property(p, '', unreal.MaterialProperty.MP_BASE_COLOR)
    mel.recompile_material(m)
    mi = at.create_asset('MI_LFF_TestTomato', ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, m)
    mel.set_material_instance_vector_parameter_value(mi, 'Color', unreal.LinearColor(0.8, 0.05, 0.03, 1))
    return mi
mi = step('재질 생성', make_mat)

def spawn_tomato():
    a = eas.spawn_actor_from_object(unreal.load_asset('/Engine/BasicShapes/Sphere'), unreal.Vector(0, 0, 60), unreal.Rotator(roll=0, pitch=0, yaw=0))
    a.set_actor_label('LFF_TestTomato')
    if mi:
        a.static_mesh_component.set_material(0, mi)
    return a
tomato = step('도형 배치(토마토)', spawn_tomato)
step('햇빛 배치', lambda: eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(roll=0, pitch=-40, yaw=30)).get_actor_label())

seq = step('시퀀스 생성', lambda: at.create_asset('LS_LFF_Test', ROOT, unreal.LevelSequence, unreal.LevelSequenceFactoryNew()))
if seq:
    step('프레임레이트 24', lambda: (seq.set_display_rate(unreal.FrameRate(24, 1)), seq.set_playback_start(0), seq.set_playback_end(48)) and 'OK')
    if tomato:
        def key_tomato():
            b = seq.add_possessable(tomato)
            tr = b.add_track(unreal.MovieScene3DTransformTrack)
            sec = tr.add_section()
            sec.set_range(0, 48)
            info = [m for m in ('get_all_channels', 'get_channels_by_type') if hasattr(sec, m)]
            ch = sec.get_all_channels() if hasattr(sec, 'get_all_channels') else unreal.MovieSceneSectionExtensions.get_all_channels(sec)
            ch[2].add_key(unreal.FrameNumber(0), 60.0)
            ch[2].add_key(unreal.FrameNumber(48), 160.0)
            return '채널 %d개 (%s) 메서드 %s' % (len(ch), type(ch[0]).__name__, info)
        step('움직임 키프레임', key_tomato)

    def camera_cut():
        cam = eas.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(-400, 0, 120), unreal.Rotator(roll=0, pitch=-8, yaw=0))
        cam.set_actor_label('LFF_TestCam')
        cb = seq.add_possessable(cam)
        tr = seq.add_track(unreal.MovieSceneCameraCutTrack) if hasattr(seq, 'add_track') else seq.add_master_track(unreal.MovieSceneCameraCutTrack)
        cs = tr.add_section()
        cs.set_range(0, 48)
        try:
            bid = seq.get_binding_id(cb)
            how = 'get_binding_id'
        except Exception:
            bid = seq.make_binding_id(cb, unreal.MovieSceneObjectBindingSpace.LOCAL)
            how = 'make_binding_id'
        cs.set_camera_binding_id(bid)
        return how
    step('카메라 컷 트랙', camera_cut)
    step('페이드 트랙', lambda: (seq.add_track(unreal.MovieSceneFadeTrack) if hasattr(seq, 'add_track') else seq.add_master_track(unreal.MovieSceneFadeTrack)) and 'OK')
    step('시퀀스 저장', lambda: unreal.EditorAssetLibrary.save_loaded_asset(seq))
step('레벨 저장', lambda: les.save_current_level())

txt = '\n'.join(R)
print(txt)
try:
    out = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()) + 'lff_check.txt'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(txt)
    txt += '\n\n저장: ' + out
except Exception as e:  # noqa: BLE001
    txt += '\n\n파일 저장 실패: %r' % e
ngs = sum(1 for r in R if r.startswith('[NG]'))
unreal.EditorDialog.show_message('LocalFoodFilm 점검 결과 (문제 %d개)' % ngs, txt, unreal.AppMsgType.OK)

"""C안 전체 영상 조립 스크립트.
실행:  blender -b --factory-startup --python scripts/build.py
결과:  LocalFoodFilm.blend (세트·인물·카메라·자막·애니메이션 전부 포함)
장면 시간·자막·문구는 config.json 에서 수정한다.
"""
import bpy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lff_core as C          # noqa: E402
import lff_char as H          # noqa: E402
import lff_sets as S          # noqa: E402
from lff_sets import sky_key  # noqa: E402
from lff_core import rad, key, show, pop, visible_only, key_alpha, flat_mat, prim, text   # noqa: E402

ROOT = C.ROOT
CFG = json.load(open(os.path.join(ROOT, 'config.json'), encoding='utf-8'))
L = CFG['labels']
SLOGAN = '건강한 지역먹거리를 우리 식탁 위에'
assert L['slogan'] == SLOGAN and ' '.join(L['sloganLines']) == SLOGAN, '슬로건 문구가 원문과 다릅니다'
FPS = CFG['fps']

# ---------- 타임라인 ----------
SC = {}
acc = 0.0
for s in CFG['scenes']:
    SC[s['id']] = dict(start=1 + round(acc * FPS), dur=s['duration'], sub=s['subtitle'])
    acc += s['duration']
TOTAL = round(acc * FPS)
for k, v in SC.items():
    v['end'] = v['start'] + round(v['dur'] * FPS) - 1


def F(sid, sec):
    return SC[sid]['start'] + round(sec * FPS)


C.reset_scene()
scene = bpy.context.scene
scene.name = 'LocalFoodFilm'
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = TOTAL

# ---------- 공통 조명/하늘 ----------
C.collection('LFF_Common')
S.sky_world()
sun_d = bpy.data.lights.new('SUN', 'SUN')
sun = bpy.data.objects.new('SUN', sun_d)
scene.collection.objects.link(sun)
sun_d.angle = rad(3)
for attr, val in (('shadow_cascade_max_distance', 40.0), ('shadow_cascade_count', 4), ('shadow_buffer_bias', 0.6),
                  ('shadow_cascade_fade', 0.2)):
    if hasattr(sun_d, attr):
        setattr(sun_d, attr, val)


def sun_key(f, elev, azim, energy, color):
    key(sun, 'rotation_euler', f, (rad(90 - elev), 0, rad(azim)))
    sun_d.energy = energy
    sun_d.color = color
    sun_d.keyframe_insert('energy', frame=f)
    sun_d.keyframe_insert('color', frame=f)


# ---------- 세트 ----------
C.collection('SET_Field');  FIELD = S.build_field()
C.collection('SET_Map');    MAP = S.build_map(L)
C.collection('SET_Store');  STORE = S.build_store(L)
C.collection('SET_Street'); STREET = S.build_street(L)
C.collection('SET_Dining'); DIN = S.build_dining()
C.collection('SET_End');    END = S.build_end(L)
X = S.SET_X

# ---------- 인물 ----------
C.collection('CHARACTERS')
FX = FIELD['FX']
CHAR_NAMES = ('CH_Farmer', 'CH_Staff', 'CH_Consumer', 'CH_Family', 'CH_Child')
for n in CHAR_NAMES:
    H.build(n)
    H.rest(n, 0)

# 대기 위치(화면 밖)
PARK = {'CH_Farmer': (FX, 0, 0), 'CH_Staff': (X['store'], 0.9, 0), 'CH_Consumer': (X['street'], 0, 0.1),
        'CH_Family': (X['dining'] + 0.85, 1.1, -0.34), 'CH_Child': (X['dining'], 1.12, 0.02)}
for n, p in PARK.items():
    H.pose(n, 0, loc=p, rotz=0)

def teleport(name, f, loc, rotz):
    """f-1 까지는 이전 위치 유지, f 부터 새 위치 (장면 전환 시 순간 이동)."""
    o = bpy.data.objects[name]
    prev_loc = list(o.location)
    prev_rot = o.rotation_euler.z
    ad = o.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if fc.data_path == 'location':
                prev_loc[fc.array_index] = fc.evaluate(f - 1)
            if fc.data_path == 'rotation_euler' and fc.array_index == 2:
                prev_rot = fc.evaluate(f - 1)
    key(o, 'location', f - 1, prev_loc)
    key(o, 'rotation_euler', f - 1, (0, 0, prev_rot))
    key(o, 'location', f, loc)
    key(o, 'rotation_euler', f, (0, 0, rad(rotz)))


# ---------- 카메라 & 자막 ----------
C.collection('CAMERAS')
SHOTS = []   # (cam, f0, f1, scene_id)


def hangul_width(s, size):
    w = 0
    for ch in s:
        w += 0.3 if ch == ' ' else (0.35 if ch in ',.!?' else (1.0 if ord(ch) > 0x3000 else 0.6))
    return w * size


def shot(name, sid, f0, f1, pos0, tgt0, pos1=None, tgt1=None, lens=35):
    cam_d = bpy.data.cameras.new(name)
    cam_d.lens = lens
    cam_d.clip_end = 700 if sid in ('S1_dawn', 'S2_farmer') or name == 'CAM_S6c' else 120
    cam = bpy.data.objects.new(name, cam_d)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(cam)
    for f, p, t in ((f0, pos0, tgt0), (f1, pos1 or pos0, tgt1 or tgt0)):
        cam.location = p
        C.look_at(cam, t)
        cam.keyframe_insert('location', frame=f)
        cam.keyframe_insert('rotation_euler', frame=f)
    m = scene.timeline_markers.new(name, frame=f0)
    m.camera = cam
    SHOTS.append((cam, f0, f1, sid))
    return cam


def add_overlays():
    """각 카메라에 자막(띠+글자)과 장면 전환용 페이드 판을 붙인다."""
    first = {}
    last = {}
    for cam, f0, f1, sid in SHOTS:
        first.setdefault(sid, (cam, f0, f1))
        last[sid] = (cam, f0, f1)
    for cam, f0, f1, sid in SHOTS:
        sc = SC[sid]
        is_first = first[sid][0] == cam
        is_last = last[sid][0] == cam
        # 페이드 판
        fm = flat_mat(cam.name + '_fade', '#000000', alpha=0.0)
        fd = prim('plane', cam.name + '_fader', (0, 0, -0.3), (1.0, 0.6, 1), m=fm, parent=cam)
        fin = 24 if sid == 'S1_dawn' else 7
        if is_first:
            key_alpha(fm, f0, 1.0)
            key_alpha(fm, f0 + fin, 0.0)
        else:
            key_alpha(fm, f0, 0.0)
        if is_last and sid != 'S8_slogan':
            key_alpha(fm, f1 - 5, 0.0)
            key_alpha(fm, f1, 1.0)
        visible_only(fd, [(f0, f1)])
        # 자막
        if not sc['sub']:
            continue
        size = 0.034
        tm = flat_mat(cam.name + '_subm', '#ffffff', alpha=0.0)
        bm = flat_mat(cam.name + '_bandm', '#221c16', alpha=0.0)
        grp = C.empty(cam.name + '_subtitle', (0, -0.21, -1.0), cam)
        grp['base_scale'] = [1, 1, 1]
        to = text(cam.name + '_subt', sc['sub'], size, (0, 0, 0), (0, 0, 0), m=tm, parent=grp)
        bpy.context.view_layer.update()
        w = to.dimensions.x + 0.09
        prim('plane', cam.name + '_band', (0, 0.002, -0.002), (w, 0.058, 1), m=bm, parent=grp, bevel=0)
        a_in = sc['start'] + 12
        a_out = sc['end'] - 12
        for m, a in ((tm, 1.0), (bm, 0.55)):
            if is_first:
                key_alpha(m, f0, 0.0)
                key_alpha(m, max(f0, a_in) + 8, a)
            else:
                key_alpha(m, f0, a)
            if is_last:
                key_alpha(m, a_out, a)
                key_alpha(m, a_out + 8, 0.0)
        visible_only(grp, [(f0, f1)])


# ======================================================
# S1 새벽 밭
# ======================================================
s = SC['S1_dawn']
shot('CAM_S1', 'S1_dawn', s['start'], s['end'], (X['field'] + 0.5, -38, 3.2), (X['field'] + 6, 120, 9),
     (X['field'] + 0.5, -32, 3.6), (X['field'] + 6, 120, 13))
sky_key(s['start'], '#f2b08a', '#3d4f7c', 0.6)
sky_key(s['end'], '#ffe6c2', '#8ec3e6', 1.0)
sun_key(s['start'], 2, 180, 1.2, (1.0, 0.62, 0.42))
sun_key(s['end'], 12, 180, 3.0, (1.0, 0.86, 0.7))
key(FIELD['sun'], 'location', s['start'], (X['field'] + 40, 400, 30))
key(FIELD['sun'], 'location', s['end'], (X['field'] + 40, 400, 85))
for fm in FIELD['fogs']:
    n = fm.node_tree.nodes['STR'].inputs[1]
    n.default_value = 0.5; n.keyframe_insert('default_value', frame=s['start'])
    n.default_value = 0.12; n.keyframe_insert('default_value', frame=s['end'])
    n.default_value = 0.0; n.keyframe_insert('default_value', frame=s['end'] + 1)

# ======================================================
# S2 농부 수확 → 땀 → 미소
# ======================================================
s = SC['S2_farmer']
for _n in CHAR_NAMES:
    H.hold(_n, s['start'] - 1)
sid = 'S2_farmer'
sky_key(s['start'], '#fff1d0', '#86c4ec', 1.0)
sun_key(s['start'], 40, 20, 3.2, (1.0, 0.95, 0.85))
FR = 'CH_Farmer'
teleport(FR, s['start'], (FX, 0, 0), 50)
fp = F(sid, 0)
H.rest(FR, fp, armL=(0, 6, 12), armR=(10, 6, 10), smile=0.45, squint=0)
H.pose(FR, F(sid, 1.0), armR=(80, -10, 5), turn=-10, head=4)
H.pose(FR, F(sid, 2.0), armR=(35, -5, 20), turn=10, head=12)
H.pose(FR, F(sid, 2.8), armR=(95, -15, 0), turn=-12, head=-6)
H.pose(FR, F(sid, 3.8), armR=(35, -5, 20), turn=10, head=12)
H.pose(FR, F(sid, 4.4), armR=(8, 6, 10), turn=0, head=0, smile=0.4)
H.pose(FR, F(sid, 5.1), armR=(95, -5, 125), head=-6)
for i, t in enumerate((5.4, 5.7, 6.0, 6.3, 6.6)):
    H.pose(FR, F(sid, t), armR=(95 + (5 if i % 2 else -5), -5 + (10 if i % 2 else -10), 125))
H.pose(FR, F(sid, 6.9), armR=(95, -5, 125), smile=0.5, squint=0)
H.pose(FR, F(sid, 7.6), armR=(8, 6, 10), head=-10, smile=1.0, squint=0.9)
for i, t in enumerate((8.0, 8.4, 8.8, 9.2, 9.6)):
    H.pose(FR, F(sid, t), bend=(3 if i % 2 else -2), head=(-6 if i % 2 else -12))
# 토마토: 덩굴 → 손 → 바구니
O = bpy.data.objects
hand = O['CH_Farmer_handR']
vine_ts = [o for o in O if o.name.startswith('veg_tomato') and o.parent and o.parent.name.startswith('tomato_plant')]
vine_ts.sort(key=lambda o: (o.parent.name, o.location.z))
held = S.veg('tomato', (0, 0, 0), 1.0, hand, name='held_tomato')
basket_ts = []
for i, (x, y, z) in enumerate([(-0.07, -0.03, 0.2), (0.07, 0.03, 0.2), (0, 0.06, 0.21), (-0.04, 0.05, 0.25), (0.05, -0.04, 0.25)]):
    basket_ts.append(S.veg('tomato', (x, y, z), 1.0, FIELD['basket'], name='basket_tomato'))
for i, bt in enumerate(basket_ts):
    if i >= 3:
        show(bt, 0, False)
show(basket_ts[3], F(sid, 2.0), True)
show(basket_ts[4], F(sid, 3.8), True)
show(held, 0, False)
show(held, F(sid, 1.0), True); show(held, F(sid, 2.0), False)
show(held, F(sid, 2.8), True); show(held, F(sid, 3.8), False)
if len(vine_ts) >= 2:
    show(vine_ts[1], F(sid, 1.0), False)
    show(vine_ts[2], F(sid, 2.8), False)
# 땀방울
sweat = prim('sphere', 'sweat', (-0.08, -0.12, 0.25), (0.012, 0.012, 0.02), m=C.mat('sweat', '#9fd8ff', .05, emit=0.5), parent=O['CH_Farmer_head'], smooth=True)
visible_only(sweat, [(F(sid, 4.3), F(sid, 6.0))])
shot('CAM_S2a', sid, s['start'], F(sid, 4.4) - 1, (FX + 0.9, -3.3, 1.45), (FX + 0.3, 0, 1.2), (FX + 0.85, -2.9, 1.45), (FX + 0.3, 0, 1.2))
shot('CAM_S2b', sid, F(sid, 4.4), s['end'], (FX + 0.55, -2.2, 1.55), (FX + 0.05, 0, 1.42), (FX + 0.45, -1.8, 1.55), (FX + 0.05, 0, 1.45))

# ======================================================
# S3 짧은 이동 경로
# ======================================================
s = SC['S3_route']
for _n in CHAR_NAMES:
    H.hold(_n, s['start'] - 1)
sid = 'S3_route'
MX = X['map']
sky_key(s['start'], '#f5f0e1', '#f5f0e1', 0.9)
sun_key(s['start'], 55, 20, 2.6, (1.0, 0.97, 0.9))
far, near = MAP['far'].data, MAP['near'].data
far.bevel_factor_end = 0; far.keyframe_insert('bevel_factor_end', frame=s['start'])
far.bevel_factor_end = 1; far.keyframe_insert('bevel_factor_end', frame=F(sid, 2.0))
near.bevel_factor_end = 0; near.keyframe_insert('bevel_factor_end', frame=F(sid, 2.8))
near.bevel_factor_end = 1; near.keyframe_insert('bevel_factor_end', frame=F(sid, 3.8))
cf = MAP['tf'].constraints[0]
cf.offset_factor = 0; cf.keyframe_insert('offset_factor', frame=F(sid, 0.2))
cf.offset_factor = 0.4; cf.keyframe_insert('offset_factor', frame=F(sid, 2.4))
cn = MAP['tn'].constraints[0]
cn.offset_factor = 0; cn.keyframe_insert('offset_factor', frame=F(sid, 3.8))
cn.offset_factor = 1; cn.keyframe_insert('offset_factor', frame=F(sid, 5.8))
show(MAP['tf'], 0, True); show(MAP['tf'], F(sid, 2.6), False)
visible_only(MAP['far'], [(0, F(sid, 2.6))])
visible_only(MAP['far_t'], [(F(sid, 0.8), F(sid, 2.6))])
show(MAP['tn'], 0, False); show(MAP['tn'], F(sid, 3.8), True)
show(MAP['near_t'], 0, False); pop(MAP['near_t'], F(sid, 3.4))
key(MAP['foot'], 'scale', F(sid, 6.0), (1.25, 1.25, 1.25))
key(MAP['foot'], 'scale', F(sid, 7.4), (0.6, 0.6, 0.6))
cam3 = shot('CAM_S3', sid, s['start'], s['end'], (MX - 0.5, -10.5, 10.2), (MX - 0.3, 0.6, 0), (MX - 0.3, -9.4, 9.2), (MX - 0.3, 0.8, 0))
pn = MAP['panel']
pn.parent = cam3
pn.location = (0, 0.2, -1.0)
pn.rotation_euler = (rad(-90), 0, 0)
pn['base_scale'] = [0.1, 0.1, 0.1]
pn.scale = (0.1, 0.1, 0.1)
show(pn, 0, False); pop(pn, F(sid, 5.4), 10)

# ======================================================
# S4 직원이 정성껏 진열
# ======================================================
s = SC['S4_display']
for _n in CHAR_NAMES:
    H.hold(_n, s['start'] - 1)
sid = 'S4_display'
SX = X['store']
sun_key(s['start'], 50, 15, 1.5, (1.0, 0.95, 0.88))
sky_key(s['start'], '#fff1d0', '#9cd0ef', 0.9)
ST = 'CH_Staff'
teleport(ST, s['start'], (SX, 0.95, 0), 0)
H.rest(ST, F(sid, 0), armL=(55, 10, 70), armR=(55, 10, 70), smile=0.6, head=6)
H.pose(ST, F(sid, 1.2), bend=14, armL=(62, 5, 40), armR=(62, 5, 40), head=14)
H.pose(ST, F(sid, 2.2), bend=20, armL=(62, 0, 10), armR=(62, 0, 10), head=18)
H.pose(ST, F(sid, 3.0), bend=4, armL=(20, 8, 40), armR=(20, 8, 40), head=4, smile=0.8)
H.pose(ST, F(sid, 4.2), bend=10, armL=(10, 6, 20), armR=(60, -10, 40), head=10, turn=-14)
H.pose(ST, F(sid, 5.2), bend=18, armR=(62, -15, 10), head=16, turn=-18)
H.pose(ST, F(sid, 6.2), bend=0, armL=(30, -8, 70), armR=(30, -8, 70), head=0, turn=0, smile=0.8)
H.pose(ST, F(sid, 6.8), smile=1.0, squint=0.9, head=-4)
H.pose(ST, F(sid, 8.9), smile=1.0, squint=0.9, head=2)
held_c = S.veg('cabbage', (0.2, -0.05, 0.02), 1.2, O['CH_Staff_handR'], name='held_cabbage')
visible_only(held_c, [(s['start'] - 2, F(sid, 2.2))])
show(STORE['placed'], 0, False); show(STORE['placed'], F(sid, 2.2), True)
held_tag = S.name_tag(L, (0, -0.03, -0.02), O['CH_Staff_handR'], name='held_tag')
held_tag.scale = (0.8, 0.8, 0.8); held_tag['base_scale'] = [0.8, 0.8, 0.8]
visible_only(held_tag, [(F(sid, 3.6), F(sid, 5.2))])
show(STORE['tag'], 0, False); pop(STORE['tag'], F(sid, 5.2), 10)
shot('CAM_S4', sid, s['start'], s['end'], (SX + 0.2, -3.6, 1.7), (SX + 0.2, 0.4, 1.2), (SX + 0.45, -2.5, 1.45), (SX + 0.5, 0.2, 1.05))

# ======================================================
# S5 퇴근길
# ======================================================
s = SC['S5_walk']
for _n in CHAR_NAMES:
    H.hold(_n, s['start'] - 1)
sid = 'S5_walk'
TX = X['street']
sky_key(s['start'], '#ffd29a', '#f08c6a', 1.0)
sun_key(s['start'], 12, 330, 2.2, (1.0, 0.72, 0.5))
CO = 'CH_Consumer'
teleport(CO, s['start'], (TX, 0, 0.1), 90)
H.walk(CO, s['start'], s['end'], period=24, amp=22, bob=0.025, base_loc=(TX, 0, 0.1))
H.pose(CO, s['start'], smile=0.55, squint=0, head=0)
H.pose(CO, F(sid, 2.4), smile=0.6, head=-4)
H.pose(CO, F(sid, 3.2), smile=1.0, squint=0.85, head=-10)
city = STREET['city']
key(city, 'location', s['start'], (TX, 0, 0))
key(city, 'location', s['end'], (TX - 11, 0, 0))
for fc in city.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
th = STREET['thought']
show(th, 0, False); pop(th, F(sid, 2.2), 10)
for i, ic in enumerate(STREET['icons']):
    t0 = 2.7 + i * 1.8
    show(ic, 0, False)
    pop(ic, F(sid, t0), 6)
    if i < 2:
        show(ic, F(sid, t0 + 1.8), False)
shot('CAM_S5', sid, s['start'], s['end'], (TX + 0.2, -5.2, 1.0), (TX + 0.6, 0, 1.75), (TX + 0.5, -4.7, 1.05), (TX + 0.75, 0, 1.8), lens=28)

# ======================================================
# S6 매장에서 고르기, 인사, 이름표 속 농부와 교차
# ======================================================
s = SC['S6_choose']
for _n in CHAR_NAMES:
    H.hold(_n, s['start'] - 1)
sid = 'S6_choose'
sun_key(s['start'], 30, 15, 1.4, (1.0, 0.85, 0.7))
sky_key(s['start'], '#ffe0b0', '#f7a57a', 0.9)
teleport(CO, s['start'], (SX - 1.85, -0.15, 0), 65)
H.rest(CO, F(sid, 0), armL=(0, 6, 12), armR=(8, 6, 12), smile=0.8, squint=0, head=4, legL=0, legR=0)
H.pose(CO, F(sid, 1.2), armR=(70, -20, 10), bend=10, head=12)
H.pose(CO, F(sid, 2.0), armR=(70, -20, 10), bend=10)
H.pose(CO, F(sid, 2.8), armR=(55, -10, 85), bend=0, head=-4, smile=1.0, squint=0.9)
H.pose(CO, F(sid, 4.4), armR=(55, -10, 85), smile=0.9, squint=0.3, turn=-10)
H.pose(CO, F(sid, 5.2), smile=1.0, squint=0.9, head=6)
teleport(ST, s['start'], (SX + 1.85, -0.05, 0), -70)
H.rest(ST, F(sid, 0), smile=0.7, squint=0)
H.pose(ST, F(sid, 3.0), armL=(0, 6, 12))
for i, t in enumerate((3.4, 3.7, 4.0, 4.3, 4.6, 4.9)):
    H.pose(ST, F(sid, t), armL=(10, 125 + (18 if i % 2 else -12), 35), head=(8 if i == 1 else 0), smile=1.0, squint=0.9)
H.pose(ST, F(sid, 5.4), armL=(0, 6, 12), smile=0.9)
# 소비자가 집어 드는 토마토
bpy.context.view_layer.update()
tomato_crate = [o for o in O if o.name.startswith('veg_tomato') and o.parent and o.parent.name.startswith('crate')
                and abs(o.matrix_world.translation.x - (SX - 0.4)) < 0.4 and o.matrix_world.translation.z < 1.2]
if tomato_crate:
    show(tomato_crate[0], F(sid, 2.0), False)
held_t = S.veg('tomato', (0, -0.02, 0), 1.2, O['CH_Consumer_handR'], name='consumer_tomato')
visible_only(held_t, [(F(sid, 2.0), s['end'])])
b1 = S.bubble('bubble_staff', L['staffGreeting'], (SX + 1.15, -0.45, 2.1), 1.6)
b2 = S.bubble('bubble_consumer', L['consumerReply'], (SX - 1.25, -0.45, 2.05), 1.2)
for b, t0 in ((b1, 3.3), (b2, 4.4)):
    show(b, 0, False); pop(b, F(sid, t0), 8); pop(b, F(sid, 6.0), 6, on=False)
shot('CAM_S6a', sid, s['start'], F(sid, 6.2) - 1, (SX - 0.1, -5.0, 1.8), (SX, 0.3, 1.25), (SX - 0.1, -4.6, 1.75), (SX, 0.3, 1.25))
tg = STORE['tag'].location
shot('CAM_S6b', sid, F(sid, 6.2), F(sid, 8.2) - 1, (tg.x - 0.25, tg.y - 1.1, tg.z + 0.25), (tg.x, tg.y, tg.z + 0.06),
     (tg.x - 0.1, tg.y - 0.75, tg.z + 0.16), (tg.x, tg.y, tg.z + 0.07))
# 이름표 속 농부 (밭 세트 재사용)
f8 = F(sid, 8.2)
sky_key(f8, '#fff1d0', '#86c4ec', 1.0)
sun_key(f8, 40, 20, 3.2, (1.0, 0.95, 0.85))
teleport(FR, f8, (FX, 0, 0), 20)
H.rest(FR, f8, smile=1.0, squint=0.9, head=-4, armL=(0, 6, 10))
for i, t in enumerate((8.4, 8.7, 9.0, 9.3, 9.6, 9.9, 10.2, 10.5)):
    H.pose(FR, F(sid, t), armR=(10, 125 + (18 if i % 2 else -12), 35))
shot('CAM_S6c', sid, f8, s['end'], (FX + 0.3, -2.4, 1.5), (FX + 0.1, 0, 1.45), (FX + 0.25, -2.0, 1.55), (FX + 0.1, 0, 1.5))
sky_key(s['end'], '#fff1d0', '#86c4ec', 1.0)

# ======================================================
# S7 따뜻한 식탁
# ======================================================
s = SC['S7_table']
for _n in CHAR_NAMES:
    H.hold(_n, s['start'] - 1)
sid = 'S7_table'
DX = X['dining']
sun_key(s['start'], 5, 180, 0.0, (0.5, 0.5, 0.8))
sky_key(s['start'], '#34406e', '#1e2548', 0.25)
seats = {'CH_Consumer': (DX - 0.85, 1.12, -0.34), 'CH_Family': (DX + 0.85, 1.12, -0.34), 'CH_Child': (DX, 1.14, 0.02)}
spoon_m = C.mat('spoon', '#d9d4c8', .3)
for idx, (n, p) in enumerate(seats.items()):
    teleport(n, s['start'], p, 0)
    H.rest(n, s['start'], legL=85, legR=85, armL=(40, 6, 50), armR=(40, 6, 50), smile=1.0, squint=0.9, head=0, turn=0)
    sp = prim('cube', n + '_spoon', (0, -0.05, -0.02), (0.02, 0.15, 0.012), rot=(0, 0, 0), m=spoon_m, parent=O[n + '_handR'])
    visible_only(sp, [(s['start'] - 1, s['end'])])
    off = [0.0, 1.2, 2.2][idx]
    t = 0.4 + off
    while t < s['dur'] - 0.6:
        H.pose(n, F(sid, t), armR=(40, 6, 50), smile=1.0, squint=0.9, head=0)
        H.pose(n, F(sid, t + 0.6), armR=(75, 25, 125), smile=0.6, squint=0.2, head=4)
        H.pose(n, F(sid, t + 1.2), armR=(75, 25, 125), smile=0.7, squint=0.2, head=2)
        H.pose(n, F(sid, t + 1.8), armR=(40, 6, 50), smile=1.0, squint=0.9, head=-4, turn=(12 if idx == 0 else -12))
        t += 3.4
for i, st in enumerate(DIN['steam']):
    base = st.location.copy()
    key(st, 'location', 1, (base.x, base.y, 1.0))
    key(st, 'location', 49, (base.x + 0.03, base.y, 1.45))
    key(st, 'scale', 1, (0.04, 0.04, 0.06))
    key(st, 'scale', 49, (0.09, 0.09, 0.14))
    C.cycle_fcurves(st)
    ad = st.animation_data.action
    for fc in ad.fcurves:
        for kp in fc.keyframe_points:
            kp.co.x += i * 16
            kp.handle_left.x += i * 16
            kp.handle_right.x += i * 16
shot('CAM_S7', sid, s['start'], s['end'], (DX, -4.2, 1.7), (DX, 0.5, 1.05), (DX, -3.4, 1.55), (DX, 0.5, 1.1))

# ======================================================
# S8 슬로건
# ======================================================
s = SC['S8_slogan']
for _n in CHAR_NAMES:
    H.hold(_n, s['start'] - 1)
sid = 'S8_slogan'
EX = X['end']
sun_key(s['start'], 50, 20, 1.0, (1.0, 0.97, 0.9))
sky_key(s['start'], '#fbf5e6', '#fbf5e6', 1.0)
for i, v in enumerate(END['vegs']):
    show(v, 0, False); pop(v, F(sid, 0.1 + i * 0.12), 8)
for o, t0 in ((END['l1'], 1.2), (END['l2'], 1.8), (END['store'], 3.2)):
    show(o, 0, False); pop(o, F(sid, t0), 12)
for i, c in enumerate(END['chips']):
    show(c, 0, False); pop(c, F(sid, 4.4 + i * 0.2), 8)
shot('CAM_S8', sid, s['start'], s['end'], (EX, -8.6, 1.5), (EX, 0, 1.45), (EX, -8.2, 1.5), (EX, 0, 1.45))

add_overlays()

# ---------- 렌더 설정 ----------
r = scene.render
try:
    r.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    r.engine = 'BLENDER_EEVEE'
scene.view_settings.view_transform = 'Standard'
ee = scene.eevee
for attr, val in (('use_gtao', True), ('gtao_distance', 0.6), ('use_soft_shadows', False), ('shadow_cube_size', '1024'),
                  ('shadow_cascade_size', '2048'), ('use_shadow_high_bitdepth', True), ('taa_render_samples', 8)):
    if hasattr(ee, attr):
        try:
            setattr(ee, attr, val)
        except Exception:
            pass
scene.frame_set(1)
out = os.path.join(ROOT, 'LocalFoodFilm.blend')
bpy.ops.wm.save_as_mainfile(filepath=out)
print('BUILD_OK', out, 'frames', TOTAL, 'shots', len(SHOTS))

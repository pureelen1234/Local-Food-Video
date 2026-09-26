"""30초판 전체 조립 (언리얼 5.8, 마스터 맥북에서 실행).
- 새 레벨 /Game/LocalFoodFilm/Maps/LFF_Main30 과 시퀀스 LS_LocalFood30 을 만든다 (기존 Main 레벨은 건드리지 않음).
- 다시 실행하면 이 스크립트가 만든 것(LFF_/CH_/CAM_ 로 시작)만 지우고 새로 만든다.
- 컷 구성은 작업일지의 "30초판 컷 구성(클로즈업 · 토마토)"을 따른다. 자막 없음, 내레이션 음성은 있으면 자동으로 넣는다.
"""
import os
import sys
import unreal

HERE = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + 'Scripts/LocalFoodFilm/'
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import importlib  # noqa: E402
import lff_common as C  # noqa: E402
importlib.reload(C)
from lff_common import F, log, shape, root, camera  # noqa: E402

# ------------------------------------------------------------------
# 설정 (여기 숫자만 고쳐도 됨)
# ------------------------------------------------------------------
TOTAL = F(30)
# 이름표·슬로건 판의 방향 보정 (roll, pitch, yaw). 글자가 돌아가 보이면 이 값만 바꾼다.
CARD_ROT = (-90.0, 0.0, 90.0)
NARRATION_DIR = os.path.expanduser('~/Desktop/내레이션')
NARRATION_START = [0, 9, 14, 20, 25.5]  # 초
SX = {'farm': 0, 'face': 3000, 'store': 6000, 'street': 9000, 'dining': 12000}

# ------------------------------------------------------------------
# 0. 레벨 · 재질 · 에셋
# ------------------------------------------------------------------
for d in ('', '/Maps', '/Sequences', '/Materials', '/Textures', '/Audio'):
    C.ensure_dir(C.ROOT + d)
LEVEL = C.ROOT + '/Maps/LFF_Main30'
if C.eal.does_asset_exist(LEVEL):
    C.les.load_level(LEVEL)
    log('기존 레벨 열기, 이전 결과 %d개 삭제' % C.clear_actors())
else:
    C.les.new_level(LEVEL)
    log('새 레벨 생성 ' + LEVEL)

MPC_PATH = C.ROOT + '/Materials/MPC_LFF'
if C.eal.does_asset_exist(MPC_PATH):
    mpc = unreal.load_asset(MPC_PATH)
else:
    mpc = C.at.create_asset('MPC_LFF', C.ROOT + '/Materials', unreal.MaterialParameterCollection,
                            unreal.MaterialParameterCollectionFactoryNew())
    ps = []
    for n in ('Dim', 'Slogan'):
        p = unreal.CollectionScalarParameter()
        p.set_editor_property('parameter_name', n)
        p.set_editor_property('default_value', 0.0)
        ps.append(p)
    mpc.set_editor_property('scalar_parameters', ps)
    C.eal.save_loaded_asset(mpc)
    log('MPC_LFF 생성 (Dim, Slogan)')
BASE, TEXT, STEAM = C.build_materials(mpc)


def M(name, hexcol, rough=0.6, emissive=0.0):
    return C.mi_color(BASE, name, hexcol, rough, emissive)


tag_tex = C.import_file(HERE + 'assets/T_LFF_NameTag.png', C.ROOT + '/Textures')
slogan_tex = C.import_file(HERE + 'assets/T_LFF_Slogan.png', C.ROOT + '/Textures')
MI_TAG = C.mi_texture(TEXT, 'NameTag', tag_tex, 1.0) if tag_tex else None
MI_SLOGAN = C.mi_texture(TEXT, 'Slogan', slogan_tex, 0.0) if slogan_tex else None
log('이미지 가져오기: 이름표 %s, 슬로건 %s' % (bool(tag_tex), bool(slogan_tex)))

# 자주 쓰는 색
TOMATO = M('Tomato', '#d8342a', 0.3)
CALYX = M('Calyx', '#3f8a3a')
LEAF = M('Leaf', '#4f9a41', 0.7)
DEW = M('Dew', '#e6f6ff', 0.03)
SOIL = M('Soil', '#7a5b3c', 0.95)
GRASS = M('Grass', '#6fa84e', 0.9)
WOOD = M('Wood', '#c8894f', 0.8)
WOOD2 = M('WoodDark', '#9c6636', 0.8)
WHITE = M('White', '#f4f1e8', 0.6)
DARK = M('EyeDark', '#2b211c', 0.3)
LIP = M('Lip', '#a8443a', 0.5)
BLUSH = M('Blush', '#ee8f82', 0.9)

# ------------------------------------------------------------------
# 1. 하늘 · 해 (컷마다 해 각도 변경)
# ------------------------------------------------------------------
sun = C.eas.spawn_actor_from_class(unreal.DirectionalLight, C.vec(0, 0, 1000), C.rot(0, -30, 180))
sun.set_actor_label('LFF_Sun')
try:
    sun.light_component.set_editor_property('atmosphere_sun_light', True)
    sun.light_component.set_editor_property('intensity', 8.0)
except Exception as e:  # noqa: BLE001
    log('해 설정 일부 건너뜀 %r' % e)
C.eas.spawn_actor_from_class(unreal.SkyAtmosphere, C.vec(0, 0, 0), C.rot()).set_actor_label('LFF_Sky')
sky = C.eas.spawn_actor_from_class(unreal.SkyLight, C.vec(0, 0, 500), C.rot())
sky.set_actor_label('LFF_SkyLight')
try:
    sky.light_component.set_editor_property('real_time_capture', True)
except Exception as e:  # noqa: BLE001
    log('하늘빛 실시간 캡처 설정 건너뜀 %r' % e)
fog = C.eas.spawn_actor_from_class(unreal.ExponentialHeightFog, C.vec(0, 0, 0), C.rot())
fog.set_actor_label('LFF_Fog')


# ------------------------------------------------------------------
# 도우미: 토마토, 얼굴
# ------------------------------------------------------------------
def tomato(label, loc, parent=None, dew=False, size=1.0):
    r = root(label, loc)
    if parent:
        r.attach_to_actor(parent, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, False)
    x, y, z = loc
    s = 0.08 * size
    shape('sphere', label + '_Body', (x, y, z), (s, s, s * 0.9), TOMATO, parent=r)
    shape('cone', label + '_Calyx', (x, y, z + 3.4 * size), (0.035 * size, 0.035 * size, 0.012 * size), CALYX, parent=r)
    shape('cyl', label + '_Stem', (x, y, z + 4.6 * size), (0.006, 0.006, 0.02), CALYX, parent=r)
    if dew:
        for i, (dy, dz) in enumerate(((-1.4, 1.6), (1.1, 0.4), (-0.5, -1.3), (1.8, -0.8), (0.3, 2.3))):
            dx = -((3.9 ** 2 - dy ** 2 - dz ** 2) ** 0.5)
            shape('sphere', '%s_Dew%d' % (label, i), (x + dx, y + dy, z + dz), (0.007, 0.007, 0.008), DEW, parent=r, shadow=False)
    return r


def face(prefix, center, radius, skin, hair, style='short', hat=False):
    """-X 방향을 보는 머리. 반환: dict(head=머리 기준점, mouth, eyes)."""
    cx, cy, cz = center
    SK = M(prefix + 'Skin', skin, 0.7)
    HR = M(prefix + 'Hair', hair, 0.85)
    h = root(prefix + '_Head', center)
    k = radius / 12.0
    shape('sphere', prefix + '_Skull', center, (radius / 50.0,) * 3, SK, parent=h)
    shape('sphere', prefix + '_HairCap', (cx + 3 * k, cy, cz + 4 * k), (radius / 47.0, radius / 48.0, radius / 58.0), HR, parent=h)
    eyes = []
    for sy in (-1, 1):
        e = shape('sphere', '%s_Eye%s' % (prefix, 'L' if sy > 0 else 'R'), (cx - 11.2 * k, cy + sy * 4 * k, cz + 1.5 * k),
                  (0.022 * k, 0.022 * k, 0.028 * k), DARK, parent=h)
        eyes.append(e)
        shape('cube', prefix + '_Brow', (cx - 11.4 * k, cy + sy * 4 * k, cz + 5.2 * k), (0.01 * k, 0.045 * k, 0.008 * k), HR, parent=h)
        shape('sphere', prefix + '_Cheek', (cx - 10.2 * k, cy + sy * 6.6 * k, cz - 2.8 * k), (0.012 * k, 0.045 * k, 0.03 * k), BLUSH, parent=h)
        shape('sphere', prefix + '_Ear', (cx, cy + sy * 11.8 * k, cz), (0.04 * k, 0.025 * k, 0.05 * k), SK, parent=h)
    shape('sphere', prefix + '_Nose', (cx - 12.2 * k, cy, cz - 0.6 * k), (0.035 * k,) * 3, SK, parent=h)
    mouth = shape('sphere', prefix + '_Mouth', (cx - 11.2 * k, cy, cz - 5.2 * k), (0.012 * k, 0.05 * k, 0.012 * k), LIP, parent=h)
    if style == 'bun':
        shape('sphere', prefix + '_Bun', (cx + 11 * k, cy, cz + 8 * k), (0.12 * k,) * 3, HR, parent=h)
    if style == 'pony':
        shape('sphere', prefix + '_Pony', (cx + 13 * k, cy, cz - 3 * k), (0.08 * k, 0.08 * k, 0.2 * k), HR, parent=h)
    if style == 'bob':
        shape('sphere', prefix + '_Bob', (cx + 2 * k, cy, cz - 1 * k), (radius / 46.0, radius / 45.0, radius / 50.0), HR, parent=h)
    if hat:
        straw = M('Straw', '#e2c070', 0.85)
        shape('cyl', prefix + '_Brim', (cx, cy, cz + 9 * k), (0.56 * k, 0.56 * k, 0.012 * k), straw, parent=h)
        shape('cyl', prefix + '_Crown', (cx, cy, cz + 15.5 * k), (0.27 * k, 0.27 * k, 0.13 * k), straw, parent=h)
        shape('cyl', prefix + '_Band', (cx, cy, cz + 10.8 * k), (0.275 * k, 0.275 * k, 0.03 * k), M('HatBand', '#a4553d'), parent=h)
    return dict(head=h, mouth=mouth, eyes=eyes, k=k)


def smile(S, fc, f, amount):
    """amount 0~1: 입 크기와 눈웃음."""
    k = fc['k']
    S.key(fc['mouth'], f, scale=(0.012 * k, (0.05 + 0.03 * amount) * k, (0.012 + 0.022 * amount) * k))
    for e in fc['eyes']:
        S.key(e, f, scale=(0.022 * k, 0.022 * k, (0.028 - 0.019 * amount) * k))


def hand(label, loc, skin, sleeve, sleeve_dir=(0, -1, 0), parent=None):
    """손(기준점) + 소매. sleeve_dir 방향으로 소매가 뻗는다."""
    h = root(label, loc)
    if parent:
        h.attach_to_actor(parent, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, False)
    x, y, z = loc
    shape('sphere', label + '_Palm', loc, (0.075, 0.065, 0.08), M(label + 'Skin', skin, 0.7), parent=h)
    shape('sphere', label + '_Thumb', (x - 3, y + 3, z + 2), (0.03, 0.03, 0.04), M(label + 'Skin', skin, 0.7), parent=h)
    dx, dy, dz = sleeve_dir
    r = (90, 0, 0) if dy else ((0, 90, 0) if dx else (0, 0, 0))
    shape('cyl', label + '_Sleeve', (x + dx * 16, y + dy * 16, z + dz * 16), (0.065, 0.065, 0.24), M(label + 'Sleeve', sleeve), r=r, parent=h)
    return h


# ------------------------------------------------------------------
# 세트 A: 새벽 토마토 밭 (컷 1, 2)
# ------------------------------------------------------------------
A = SX['farm']
shape('plane', 'LFF_A_Ground', (A, 0, 0), (60, 60, 1), SOIL)
for i in range(-6, 7):
    for j in range(1, 14):
        shape('sphere', 'LFF_A_Crop', (A + j * 120 + (i % 2) * 60, i * 90, 12), (0.4, 0.4, 0.25), GRASS)
shape('cyl', 'LFF_A_StakeStem', (A + 2, 3, 55), (0.02, 0.02, 1.1), CALYX)
for i, (dx, dy, dz) in enumerate(((4, 10, 92), (-3, -12, 74), (6, -6, 104), (5, 14, 66), (8, 0, 118), (3, -16, 96))):
    shape('sphere', 'LFF_A_Leaf', (A + dx, dy, dz), (0.16, 0.11, 0.04), LEAF, r=(20 * (i % 3 - 1), 15, 30 * i))
for i, (dx, dy, dz) in enumerate(((6, 11, 97), (5, -10, 70), (8, 14, 108))):
    tomato('LFF_A_Tomato%d' % i, (A + dx, dy, dz))
HERO_A = tomato('LFF_HeroTomato_A', (A, 0, 82), dew=True)
FARMER_HAND = hand('CH_Farmer_Hand', (A - 8, -46, 96), '#d9a27c', '#7aa0c8')

# ------------------------------------------------------------------
# 세트 B: 농부 얼굴 (컷 3, 4)
# ------------------------------------------------------------------
B = SX['face']
shape('plane', 'LFF_B_Ground', (B, 0, 0), (60, 60, 1), GRASS)
for j in range(2, 12):
    for i in range(-4, 5):
        shape('sphere', 'LFF_B_Crop', (B + j * 110, i * 100 + (j % 2) * 50, 20), (0.5, 0.5, 0.4), LEAF)
farmer = root('CH_Farmer', (B, 0, 0))
FSHIRT = M('FarmerShirt', '#7aa0c8')
shape('sphere', 'CH_Farmer_Torso', (B + 4, 0, 116), (0.42, 0.56, 0.56), FSHIRT, parent=farmer)
shape('cyl', 'CH_Farmer_Neck', (B, 0, 146), (0.1, 0.1, 0.12), M('FarmerSkin', '#d9a27c'), parent=farmer)
shape('cube', 'CH_Farmer_Towel', (B - 10, 0, 141), (0.04, 0.34, 0.07), WHITE, parent=farmer)
shape('cube', 'CH_Farmer_TowelEnd', (B - 13, -9, 128), (0.03, 0.08, 0.24), WHITE, parent=farmer)
FF = face('CH_Farmer', (B, 0, 160), 12, '#d9a27c', '#8a8178', hat=True)
FF['head'].attach_to_actor(farmer, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                           unreal.AttachmentRule.KEEP_WORLD, False)
sweat = shape('sphere', 'LFF_Sweat', (B - 12.2, 5, 167), (0.014, 0.014, 0.02), M('Sweat', '#9fd8ff', 0.05), shadow=False)
WIPE_HAND = hand('CH_Farmer_WipeHand', (B - 20, 26, 148), '#d9a27c', '#7aa0c8', sleeve_dir=(0, 1, 0))
shape('cube', 'LFF_WipeTowel', (B - 22, 22, 150), (0.02, 0.1, 0.12), WHITE, parent=WIPE_HAND)
HOLD_HAND = hand('CH_Farmer_HoldHand', (B - 24, -18, 108), '#d9a27c', '#7aa0c8', sleeve_dir=(0, 0, -1))
HERO_B = tomato('LFF_HeroTomato_B', (B - 26, -18, 116))

# ------------------------------------------------------------------
# 세트 C: 직매장 매대 (컷 5, 6, 8)
# ------------------------------------------------------------------
Cx = SX['store']
shape('plane', 'LFF_C_Floor', (Cx, 0, 0), (30, 30, 1), M('StoreFloor', '#c9a07a', 0.7))
shape('cube', 'LFF_C_Wall', (Cx + 190, 0, 175), (0.04, 8, 3.5), M('StoreWall', '#f6e4c8', 0.9))
for z in (120, 175):
    shape('cube', 'LFF_C_Shelf', (Cx + 170, 0, z), (0.35, 6, 0.04), WOOD2)
    for i in range(-5, 6):
        shape('cube', 'LFF_C_ShelfCrate', (Cx + 170, i * 55, z + 9), (0.3, 0.45, 0.14), WOOD)
        shape('sphere', 'LFF_C_ShelfVeg', (Cx + 165, i * 55, z + 18), (0.14, 0.3, 0.1), [LEAF, TOMATO, M('Carrot', '#f08a2c', 0.5)][i % 3])
shape('cube', 'LFF_C_Table', (Cx + 20, 0, 45), (1.2, 2.8, 0.9), WOOD)
for y, col in ((-85, M('Carrot', '#f08a2c', 0.5)), (85, M('Cabbage', '#8fcf6a', 0.6))):
    shape('cube', 'LFF_C_Crate', (Cx + 20, y, 97), (0.4, 0.55, 0.14), WOOD)
    for i in range(3):
        for j in range(2):
            shape('sphere', 'LFF_C_Veg', (Cx + 11 + j * 18, y - 16 + i * 16, 108), (0.09, 0.07, 0.07), col)
crate = root('LFF_HeroCrate', (Cx + 10, 0, 130))
shape('cube', 'LFF_HeroCrate_Box', (Cx + 10, 0, 137), (0.4, 0.55, 0.14), WOOD, parent=crate)
shape('cube', 'LFF_HeroCrate_Slat', (Cx - 10.2, 0, 137), (0.01, 0.55, 0.03), WOOD2, parent=crate)
HERO_C = None
for i, y in enumerate((-16, 0, 16)):
    for j, dx in enumerate((-9, 9)):
        lbl = 'LFF_HeroTomato_C' if (y == 16 and dx == -9) else 'LFF_CrateTomato%d%d' % (i, j)
        t = tomato(lbl, (Cx + 10 + dx, y, 146), parent=crate)
        if lbl == 'LFF_HeroTomato_C':
            HERO_C = t
STAFF_HANDS = root('CH_Staff_Hands', (Cx + 10, 0, 137))
for sy in (-1, 1):
    hand('CH_Staff_Hand%s' % ('L' if sy > 0 else 'R'), (Cx + 10, sy * 31, 137), '#f1c6a3', '#f6f2e8',
         sleeve_dir=(-1, 0, 0), parent=STAFF_HANDS)
if MI_TAG:
    tag = shape('plane', 'LFF_NameTag', (Cx - 12, 30, 100), (0.2, 0.1, 1), MI_TAG, r=CARD_ROT, shadow=False)
    shape('cyl', 'LFF_NameTag_Stick', (Cx - 11, 30, 88), (0.01, 0.01, 0.2), WOOD2)
staff = root('CH_Staff', (Cx + 110, 0, 0))
shape('sphere', 'CH_Staff_Torso', (Cx + 112, 0, 112), (0.4, 0.5, 0.52), WHITE, parent=staff)
shape('cube', 'CH_Staff_Apron', (Cx + 92, 0, 104), (0.02, 0.36, 0.5), M('Apron', '#3f8f5a'), parent=staff)
shape('cube', 'CH_Staff_Badge', (Cx + 90.5, -8, 118), (0.01, 0.07, 0.035), WHITE, parent=staff)
SF = face('CH_Staff', (Cx + 110, 0, 150), 11, '#f1c6a3', '#3a2a20', style='bun')
SF['head'].attach_to_actor(staff, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                           unreal.AttachmentRule.KEEP_WORLD, False)
CONS_HAND = hand('CH_Consumer_Hand', (Cx - 50, -42, 115), '#f4cdb0', '#d9587a')
pl = C.eas.spawn_actor_from_class(unreal.PointLight, C.vec(Cx - 20, -40, 230), C.rot())
pl.set_actor_label('LFF_C_Lamp')
try:
    pl.light_component.set_editor_property('light_color', unreal.Color(r=255, g=224, b=180, a=255))
except Exception:  # noqa: BLE001
    pass

# ------------------------------------------------------------------
# 세트 D: 퇴근길 (컷 7, 뒤에서 따라가는 카메라)
# ------------------------------------------------------------------
D = SX['street']
shape('cube', 'LFF_D_Sidewalk', (D + 500, 0, 5), (16, 2.6, 0.1), M('Sidewalk', '#dcc6aa', 0.9))
shape('plane', 'LFF_D_Road', (D + 500, -320, 0), (16, 3.6, 1), M('Road', '#6b6670', 0.8))
shape('plane', 'LFF_D_Grass', (D + 500, 300, 1), (16, 3.4, 1), GRASS)
for i in range(8):
    x = D + 150 + i * 200
    shape('cyl', 'LFF_D_Trunk', (x, 190, 90), (0.1, 0.1, 1.8), M('Trunk', '#7a5a44'))
    shape('sphere', 'LFF_D_Crown', (x, 190, 230), (1.3, 1.3, 1.2), M('Tree', '#7fb45c', 0.8))
    shape('cube', 'LFF_D_Building', (D + 100 + i * 230, 700, 300), (2.1, 2.5, 3 + (i % 3) * 1.4),
          M('Bld%d' % (i % 3), ['#e2a88c', '#c98a78', '#e9b89a'][i % 3], 0.9))
cons = root('CH_Consumer', (D, 0, 10))
PANTS = M('ConsumerPants', '#3f4a63')
CSHIRT = M('ConsumerShirt', '#d9587a')
CSKIN = M('ConsumerSkin', '#f4cdb0', 0.7)
CHAIR = M('ConsumerHair', '#2e2019', 0.85)
shape('sphere', 'CH_Consumer_Pelvis', (D, 0, 100), (0.3, 0.36, 0.22), PANTS, parent=cons)
legs = {}
for side, sy in (('L', 1), ('R', -1)):
    lg = root('CH_Consumer_Leg' + side, (D, sy * 10, 98))
    lg.attach_to_actor(cons, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    shape('cyl', 'CH_Consumer_Thigh' + side, (D, sy * 10, 56), (0.12, 0.12, 0.84), PANTS, parent=lg)
    shape('cube', 'CH_Consumer_Shoe' + side, (D + 5, sy * 10, 16), (0.26, 0.11, 0.08), M('Shoe', '#2d2a33', 0.5), parent=lg)
    legs[side] = lg
shape('sphere', 'CH_Consumer_Torso', (D, 0, 132), (0.36, 0.42, 0.55), CSHIRT, parent=cons)
shape('sphere', 'CH_Consumer_HeadBack', (D, 0, 174), (0.21, 0.21, 0.22), CSKIN, parent=cons)
shape('sphere', 'CH_Consumer_HairBack', (D - 2, 0, 176), (0.23, 0.23, 0.22), CHAIR, parent=cons)
pony = root('CH_Consumer_Ponytail', (D - 11, 0, 178))
pony.attach_to_actor(cons, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
shape('sphere', 'CH_Consumer_PonyHair', (D - 15, 0, 166), (0.08, 0.08, 0.2), CHAIR, parent=pony)
armL = root('CH_Consumer_ArmL', (D, 22, 152))
armL.attach_to_actor(cons, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
shape('cyl', 'CH_Consumer_UpperL', (D, 23, 128), (0.08, 0.08, 0.46), CSHIRT, parent=armL)
shape('sphere', 'CH_Consumer_HandL', (D, 23, 103), (0.06, 0.06, 0.07), CSKIN, parent=armL)
armR = root('CH_Consumer_ArmR', (D, -22, 152))
armR.attach_to_actor(cons, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
shape('cyl', 'CH_Consumer_UpperR', (D, -23, 136), (0.08, 0.08, 0.32), CSHIRT, parent=armR)
shape('cyl', 'CH_Consumer_ForeR', (D + 12, -24, 120), (0.07, 0.07, 0.26), CSKIN, r=(0, 90, 0), parent=armR)
shape('sphere', 'CH_Consumer_HandR', (D + 26, -24, 120), (0.06, 0.06, 0.07), CSKIN, parent=armR)
bag = root('LFF_EcoBag', (D + 8, -26, 121))
bag.attach_to_actor(armR, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
shape('cube', 'LFF_EcoBag_Body', (D + 8, -29, 98), (0.28, 0.08, 0.34), M('EcoBag', '#eadcbf', 0.9), parent=bag)
shape('cube', 'LFF_EcoBag_Handle', (D + 8, -27, 113), (0.02, 0.02, 0.16), M('Strap', '#c7ab80'), parent=bag)
shape('sphere', 'LFF_EcoBag_Leaf', (D + 8, -33.5, 100), (0.05, 0.004, 0.08), M('BagLeaf', '#6fae5a'), r=(0, 30, 0), parent=bag)

# ------------------------------------------------------------------
# 세트 E: 저녁 식탁 (컷 9, 10, 11)
# ------------------------------------------------------------------
E = SX['dining']
shape('plane', 'LFF_E_Floor', (E, 0, 0), (20, 20, 1), M('DinFloor', '#b98a5a', 0.7))
shape('cube', 'LFF_E_Wall', (E + 220, 0, 170), (0.04, 7, 3.4), M('DinWall', '#e7b98c', 0.9))
shape('cube', 'LFF_E_Window', (E + 217, -150, 190), (0.02, 1.1, 1.0), M('Night', '#23305e', 0.2, 1.5))
shape('cube', 'LFF_E_Table', (E + 40, 0, 37), (1.3, 2.6, 0.74), WOOD2)
shape('cube', 'LFF_E_Cloth', (E + 40, 0, 74.5), (1.32, 2.0, 0.01), M('Cloth', '#f4efe3', 0.9))
shape('cyl', 'LFF_E_Plate', (E, 0, 76), (0.32, 0.32, 0.02), WHITE)
EGG = M('Egg', '#f6d34a', 0.5)
for i, (dx, dy) in enumerate(((-5, -6), (4, 7), (7, -4), (-6, 6), (0, 0))):
    shape('sphere', 'LFF_E_Egg', (E + dx, dy, 78.5), (0.1, 0.08, 0.035), EGG, r=(0, 0, 40 * i))
for i, (dx, dy) in enumerate(((-2, -9), (6, 2), (-8, 1), (2, 9), (9, -9), (-4, 4))):
    shape('sphere', 'LFF_E_TomatoChunk', (E + dx, dy, 80), (0.045, 0.04, 0.03), TOMATO, r=(0, 0, 30 * i))
for i, (dx, dy) in enumerate(((1, -3), (-3, 8), (5, 5), (-7, -3))):
    shape('sphere', 'LFF_E_Onion', (E + dx, dy, 81.5), (0.012, 0.012, 0.008), CALYX)
for y in (-55, 0, 55):
    shape('sphere', 'LFF_E_Bowl', (E + 45, y, 80), (0.14, 0.14, 0.08), WHITE)
steam = [shape('sphere', 'LFF_Steam%d' % i, (E + (i - 1.5) * 3, (i % 2) * 3 - 1.5, 84), (0.03, 0.03, 0.04), STEAM, shadow=False) for i in range(4)]
family = []
for lbl, y, z, rad, skin, hair, style, shirt in (('CH_Consumer_Family', -55, 128, 11, '#f4cdb0', '#2e2019', 'pony', '#d9587a'),
                                                  ('CH_Family', 55, 132, 11.5, '#efc3a0', '#2a2420', 'short', '#7c9b6d'),
                                                  ('CH_Child', 0, 114, 9, '#f6d2b6', '#3a2a20', 'bob', '#f2c14e')):
    body = root(lbl, (E + 110, y, 0))
    shape('sphere', lbl + '_Torso', (E + 112, y, z - 36), (0.38 * rad / 11, 0.46 * rad / 11, 0.5 * rad / 11), M(lbl + 'Shirt', shirt), parent=body)
    fc = face(lbl, (E + 110, y, z), rad, skin, hair, style=style)
    fc['head'].attach_to_actor(body, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    family.append(fc)
SPOON_HAND = hand('CH_Consumer_SpoonHand', (E + 80, -40, 88), '#f4cdb0', '#d9587a', sleeve_dir=(1, 0, 0))
shape('cube', 'LFF_Spoon', (E + 78, -40, 98), (0.012, 0.02, 0.16), M('Spoon', '#d9d4c8', 0.25), parent=SPOON_HAND)
for pos, inten in (((E - 10, 0, 190), 1.0), ((E + 60, 0, 230), 0.6)):
    lamp = C.eas.spawn_actor_from_class(unreal.PointLight, C.vec(*pos), C.rot())
    lamp.set_actor_label('LFF_E_Lamp')
    try:
        lamp.light_component.set_editor_property('light_color', unreal.Color(r=255, g=196, b=140, a=255))
        lamp.light_component.set_editor_property('intensity', 8000.0 * inten)
    except Exception:  # noqa: BLE001
        pass
log('세트 5곳, 인물(농부·직원·소비자·가족) 배치 완료')

# ------------------------------------------------------------------
# 2. 시퀀스와 컷
# ------------------------------------------------------------------
SEQ_PATH = C.ROOT + '/Sequences/LS_LocalFood30'
if C.eal.does_asset_exist(SEQ_PATH):
    C.eal.delete_asset(SEQ_PATH)
seq = C.at.create_asset('LS_LocalFood30', C.ROOT + '/Sequences', unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(24, 1))
seq.set_playback_start(0)
seq.set_playback_end(TOTAL)
S = C.Seq(seq, TOTAL)
cuts = []


def cam(label, f0, f1, p0, t0, p1=None, t1=None, focal=50, fstop=2.8, interp='auto'):
    c = camera(label, p0, t0, focal, fstop)
    S.key(c, f0, loc=p0, r=C.look(p0, t0), interp=interp)
    S.key(c, f1, loc=p1 or p0, r=C.look(p1 or p0, t1 or t0), interp=interp)
    cuts.append((c, f0, f1))
    return c


def sun_at(f, pitch, yaw):
    S.key(sun, f, r=(0, pitch, yaw), interp='const')


# 컷 1 (0~3초) 이슬 맺힌 토마토, 해돋이
sun_at(0, -4, 180)
cam('CAM_C01', 0, F(3), (A - 24, 7, 85), (A, 0, 82), (A - 16, 4, 83), (A, 0, 82), focal=50, fstop=2.0)
# 컷 2 (3~5초) 농부 손이 토마토를 딴다
sun_at(F(3), -18, 170)
S.key(FARMER_HAND, F(3), loc=(A - 8, -46, 96))
S.key(FARMER_HAND, F(4), loc=(A - 3, -7, 84))
S.key(FARMER_HAND, F(5), loc=(A - 12, -30, 72))
S.key(HERO_A, F(4), loc=(A, 0, 82))
S.key(HERO_A, F(5), loc=(A - 9, -24, 70))
cam('CAM_C02', F(3), F(5), (A - 46, 22, 96), (A - 4, -10, 82), focal=40)
# 컷 3 (5~7초) 이마 땀방울 → 수건으로 닦음
sun_at(F(5), -40, 150)
S.key(sweat, F(5), loc=(B - 12.2, 5, 167), scale=(0.014, 0.014, 0.02))
S.key(sweat, F(6.2), loc=(B - 12.2, 5, 162.5))
S.show(sweat, F(6.5), False, (0.014, 0.014, 0.02))
S.key(WIPE_HAND, F(5.3), loc=(B - 20, 26, 148))
S.key(WIPE_HAND, F(6.0), loc=(B - 15, 10, 166))
S.key(WIPE_HAND, F(6.5), loc=(B - 15, -8, 167))
S.key(WIPE_HAND, F(7.0), loc=(B - 22, -26, 146))
S.key(FF['head'], F(5), r=(0, -4, 0))
S.key(FF['head'], F(6.2), r=(0, -8, 0))
smile(S, FF, F(5), 0.1)
cam('CAM_C03', F(5), F(7), (B - 50, 12, 166), (B, 0, 164), (B - 44, 10, 165), (B, 0, 164), focal=70)
# 컷 4 (7~9초) 토마토를 들고 활짝 웃는 농부
smile(S, FF, F(7.2), 0.1)
smile(S, FF, F(7.8), 1.0)
S.key(FF['head'], F(7.8), r=(0, -2, 0))
S.key(FF['head'], F(8.3), r=(3, 4, 0))
S.key(FF['head'], F(8.8), r=(0, -1, 0))
S.key(HOLD_HAND, F(7), loc=(B - 24, -18, 108))
S.key(HOLD_HAND, F(7.8), loc=(B - 24, -16, 136))
S.key(HERO_B, F(7), loc=(B - 26, -18, 116))
S.key(HERO_B, F(7.8), loc=(B - 26, -16, 144))
cam('CAM_C04', F(7), F(9), (B - 62, -8, 156), (B, -5, 152), (B - 54, -6, 157), (B, -5, 152), focal=50)
# 컷 5 (9~11.5초) 직원이 두 손으로 토마토 상자를 내려놓음
S.key(crate, F(9), loc=(Cx + 10, 0, 130))
S.key(crate, F(10.5), loc=(Cx + 10, 0, 90))
S.key(STAFF_HANDS, F(9), loc=(Cx + 10, 0, 137))
S.key(STAFF_HANDS, F(10.5), loc=(Cx + 10, 0, 97))
S.key(STAFF_HANDS, F(11.3), loc=(Cx - 50, 0, 120))
cam('CAM_C05', F(9), F(11.5), (Cx - 78, -36, 128), (Cx + 10, 0, 105), focal=40)
# 컷 6 (11.5~14초) 토마토 상자 위 생산자 이름표
cam('CAM_C06', F(11.5), F(14), (Cx - 52, 8, 104), (Cx - 5, 22, 101), (Cx - 40, 10, 103), (Cx - 5, 22, 101), focal=50, fstop=2.0)
# 컷 7 (14~17초) 뒤에서 따라가는 발걸음, 팔에 걸친 에코백이 살짝 흔들림
sun_at(F(14), -7, 180)
f0, f1 = F(14), F(17)
S.key(cons, f0, loc=(D, 0, 10), interp='linear')
S.key(cons, f1, loc=(D + 390, 0, 10), interp='linear')
i = 0
for f in range(f0, f1 + 1, 6):
    sw = (0, 1, 0, -1)[i % 4]
    S.key(legs['L'], f, r=(0, 22 * sw, 0))
    S.key(legs['R'], f, r=(0, -22 * sw, 0))
    S.key(armL, f, r=(0, -12 * sw, 0))
    S.key(bag, f, r=(3 * sw, 5 * sw, 0))
    S.key(pony, f, r=(0, 6 * sw, 0))
    i += 1
cam('CAM_C07', f0, f1, (D - 190, -38, 106), (D + 60, -8, 66), (D + 200, -38, 106), (D + 450, -8, 66), focal=35, interp='linear')
# 컷 8 (17~20초) 이름표 옆 토마토를 집는 손 → 직원과 눈인사
sun_at(F(17), -40, 150)
S.key(CONS_HAND, F(17), loc=(Cx - 50, -42, 115))
S.key(CONS_HAND, F(17.9), loc=(Cx - 4, 22, 108))
S.key(CONS_HAND, F(18.5), loc=(Cx - 30, -12, 126))
if HERO_C:
    S.key(HERO_C, F(17.9), loc=(-9, 16, 16))
    S.key(HERO_C, F(18.5), loc=(-35, -12, 34))
cam('CAM_C08a', F(17), F(18.5), (Cx - 48, -32, 120), (Cx + 1, 16, 106), focal=45)
for t, p in ((18.5, 0), (18.9, 12), (19.3, 0), (19.6, 9), (20, 0)):
    S.key(SF['head'], F(t), r=(0, p, 0))
smile(S, SF, F(18.5), 0.4)
smile(S, SF, F(18.9), 1.0)
cam('CAM_C08b', F(18.5), F(20), (Cx - 10, -12, 150), (Cx + 110, 0, 150), focal=85, fstop=2.0)
# 컷 9 (20~22초) 김이 오르는 토마토 달걀볶음
sun_at(F(20), 12, 180)
for n, st in enumerate(steam):
    base = st.get_actor_location()
    for c0 in range(F(20) - n * 10, TOTAL, 40):
        S.key(st, c0, loc=(base.x, base.y, 84), scale=(0.03, 0.03, 0.04), interp='linear')
        S.key(st, c0 + 39, loc=(base.x + 2, base.y, 122), scale=(0.1, 0.1, 0.13), interp='linear')
cam('CAM_C09', F(20), F(22), (E - 40, -10, 100), (E, 0, 78), (E - 33, -8, 96), (E, 0, 78), focal=50, fstop=2.0)
# 컷 10 (22~25.5초) 숟가락을 드는 가족 미소
S.key(SPOON_HAND, F(22), loc=(E + 80, -40, 88))
S.key(SPOON_HAND, F(23.2), loc=(E + 94, -50, 118))
S.key(SPOON_HAND, F(24.4), loc=(E + 80, -40, 88))
for n, fc in enumerate(family):
    smile(S, fc, F(22), 0.7)
    for t, p in ((22.4 + n * 0.3, 0), (22.8 + n * 0.3, 8), (23.3 + n * 0.3, -3), (23.8 + n * 0.3, 5), (24.6, 0)):
        S.key(fc['head'], F(t), r=(4 * (n - 1), p, 0))
    smile(S, fc, F(23 + n * 0.3), 1.0)
cam('CAM_C10', F(22), F(25.5), (E - 150, 0, 124), (E + 110, 0, 118), (E - 132, 0, 122), (E + 110, 0, 118), focal=40)
# 컷 11 (25.5~30초) 식탁 위 토마토 요리 → 어두워지며 슬로건
c11 = cam('CAM_C11', F(25.5), TOTAL, (E - 40, 12, 106), (E, 0, 78), (E - 34, 8, 97), (E, 0, 78), focal=50, fstop=2.2)
S.key(c11, F(28), loc=(E - 34, 8, 97), r=C.look((E - 34, 8, 97), (E, 0, 78)))
if MI_SLOGAN:
    sl = shape('plane', 'LFF_SloganCard', (0, 0, 0), (0.19, 0.107, 1), MI_SLOGAN, shadow=False)
    sl.attach_to_actor(c11, '', unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE,
                       unreal.AttachmentRule.KEEP_RELATIVE, False)
    sl.set_actor_relative_location(C.vec(40, 0, 0), False, True)
    sl.set_actor_relative_rotation(C.rot(*CARD_ROT), False, True)
    sl.set_actor_relative_scale3d(C.vec(0.19, 0.107, 1))
S.mpc_keys(mpc, {'Dim': [(0, 0), (F(26.5), 0), (F(28), 0.82), (TOTAL, 0.82)],
                 'Slogan': [(0, 0), (F(27.3), 0), (F(28.5), 1), (TOTAL, 1)]})
S.camera_cuts(cuts)
log('컷 %d개, 카메라 컷 트랙 완료' % len(cuts))

# 내레이션
n_ok = 0
for i, t in enumerate(NARRATION_START):
    wav = os.path.join(NARRATION_DIR, 'nar_%02d.wav' % (i + 1))
    if os.path.exists(wav):
        snd = C.import_file(wav, C.ROOT + '/Audio')
        if snd:
            S.audio(snd, F(t))
            n_ok += 1
log('내레이션 %d/5개 넣음 (폴더: %s)' % (n_ok, NARRATION_DIR))

C.eal.save_loaded_asset(seq)
C.les.save_current_level()
try:
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)
except Exception as e:  # noqa: BLE001
    log('시퀀서 자동 열기 실패 %r' % e)
unreal.EditorDialog.show_message('LocalFoodFilm 30초판 조립 완료', '\n'.join(C.LOG), unreal.AppMsgType.OK)

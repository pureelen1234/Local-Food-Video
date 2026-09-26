"""공통 도우미 (언리얼 5.8 에서 lff_00_check.py 로 동작 확인한 API 만 사용).
단위: cm, Z 위쪽. 인물·소품은 -X 방향(카메라 쪽)을 바라본다.
"""
import os
import unreal

ROOT = '/Game/LocalFoodFilm'
FPS = 24
LOG = []

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
at = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary

SHAPES = {k: '/Engine/BasicShapes/' + v for k, v in
          (('cube', 'Cube'), ('sphere', 'Sphere'), ('cyl', 'Cylinder'), ('cone', 'Cone'), ('plane', 'Plane'))}
_MESH = {}
_MI = {}


def log(msg):
    LOG.append(msg)
    unreal.log('[LFF] ' + msg)


def F(sec):
    return int(round(sec * FPS))


def lin(h):
    """#RRGGBB(sRGB) → LinearColor."""
    h = h.lstrip('#')
    c = []
    for i in (0, 2, 4):
        v = int(h[i:i + 2], 16) / 255.0
        c.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return unreal.LinearColor(c[0], c[1], c[2], 1.0)


def rot(roll=0.0, pitch=0.0, yaw=0.0):
    return unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw)


def vec(x, y, z):
    return unreal.Vector(x, y, z)


# ---------------- 에셋 ----------------
def ensure_dir(p):
    if not eal.does_directory_exist(p):
        eal.make_directory(p)


def fresh_asset(name, path, cls, factory):
    full = path + '/' + name
    if eal.does_asset_exist(full):
        return unreal.load_asset(full)
    return at.create_asset(name, path, cls, factory)


def build_materials(mpc):
    """M_LFF_Base: Color·Roughness·Emissive 파라미터 + MPC 'Dim'(화면 어둡게).
    M_LFF_Text: 투명 무광 이미지(Tex) + Always / MPC 'Slogan' 으로 불투명도.
    M_LFF_Steam: 반투명 흰 김."""
    p = ROOT + '/Materials'
    ensure_dir(p)
    base = fresh_asset('M_LFF_Base', p, unreal.Material, unreal.MaterialFactoryNew())
    if mel.get_num_material_expressions(base) == 0:
        col = mel.create_material_expression(base, unreal.MaterialExpressionVectorParameter, -800, -100)
        col.set_editor_property('parameter_name', 'Color')
        col.set_editor_property('default_value', unreal.LinearColor(0.8, 0.8, 0.8, 1))
        rough = mel.create_material_expression(base, unreal.MaterialExpressionScalarParameter, -800, 200)
        rough.set_editor_property('parameter_name', 'Roughness')
        rough.set_editor_property('default_value', 0.6)
        emis = mel.create_material_expression(base, unreal.MaterialExpressionScalarParameter, -800, 350)
        emis.set_editor_property('parameter_name', 'Emissive')
        emis.set_editor_property('default_value', 0.0)
        dim = mel.create_material_expression(base, unreal.MaterialExpressionCollectionParameter, -800, 500)
        dim.set_editor_property('collection', mpc)
        dim.set_editor_property('parameter_name', 'Dim')
        onem = mel.create_material_expression(base, unreal.MaterialExpressionOneMinus, -550, 500)
        mel.connect_material_expressions(dim, '', onem, '')
        mul = mel.create_material_expression(base, unreal.MaterialExpressionMultiply, -350, -50)
        mel.connect_material_expressions(col, '', mul, 'A')
        mel.connect_material_expressions(onem, '', mul, 'B')
        mul2 = mel.create_material_expression(base, unreal.MaterialExpressionMultiply, -200, 300)
        mel.connect_material_expressions(mul, '', mul2, 'A')
        mel.connect_material_expressions(emis, '', mul2, 'B')
        mel.connect_material_property(mul, '', unreal.MaterialProperty.MP_BASE_COLOR)
        mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
        mel.connect_material_property(mul2, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        mel.recompile_material(base)
        eal.save_loaded_asset(base)
        log('재질 M_LFF_Base 생성')

    text = fresh_asset('M_LFF_Text', p, unreal.Material, unreal.MaterialFactoryNew())
    if mel.get_num_material_expressions(text) == 0:
        text.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
        text.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
        text.set_editor_property('two_sided', True)
        tex = mel.create_material_expression(text, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0)
        tex.set_editor_property('parameter_name', 'Tex')
        always = mel.create_material_expression(text, unreal.MaterialExpressionScalarParameter, -700, 300)
        always.set_editor_property('parameter_name', 'Always')
        always.set_editor_property('default_value', 1.0)
        sl = mel.create_material_expression(text, unreal.MaterialExpressionCollectionParameter, -700, 450)
        sl.set_editor_property('collection', mpc)
        sl.set_editor_property('parameter_name', 'Slogan')
        mx = mel.create_material_expression(text, unreal.MaterialExpressionMax, -450, 350)
        mel.connect_material_expressions(always, '', mx, 'A')
        mel.connect_material_expressions(sl, '', mx, 'B')
        op = mel.create_material_expression(text, unreal.MaterialExpressionMultiply, -250, 250)
        mel.connect_material_expressions(tex, 'A', op, 'A')
        mel.connect_material_expressions(mx, '', op, 'B')
        mel.connect_material_property(tex, 'RGB', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        mel.connect_material_property(op, '', unreal.MaterialProperty.MP_OPACITY)
        mel.recompile_material(text)
        eal.save_loaded_asset(text)
        log('재질 M_LFF_Text 생성')

    steam = fresh_asset('M_LFF_Steam', p, unreal.Material, unreal.MaterialFactoryNew())
    if mel.get_num_material_expressions(steam) == 0:
        steam.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
        steam.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
        c = mel.create_material_expression(steam, unreal.MaterialExpressionConstant3Vector, -400, 0)
        c.set_editor_property('constant', unreal.LinearColor(0.9, 0.9, 0.9, 1))
        o = mel.create_material_expression(steam, unreal.MaterialExpressionConstant, -400, 200)
        o.set_editor_property('r', 0.28)
        mel.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        mel.connect_material_property(o, '', unreal.MaterialProperty.MP_OPACITY)
        mel.recompile_material(steam)
        eal.save_loaded_asset(steam)
        log('재질 M_LFF_Steam 생성')
    return base, text, steam


def mi_color(base, name, hexcol, rough=0.6, emissive=0.0):
    key = name
    if key in _MI:
        return _MI[key]
    p = ROOT + '/Materials/Instances'
    ensure_dir(p)
    mi = fresh_asset('MI_' + name, p, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, base)
    mel.set_material_instance_vector_parameter_value(mi, 'Color', lin(hexcol))
    mel.set_material_instance_scalar_parameter_value(mi, 'Roughness', rough)
    mel.set_material_instance_scalar_parameter_value(mi, 'Emissive', emissive)
    eal.save_loaded_asset(mi)
    _MI[key] = mi
    return mi


def mi_texture(text_mat, name, texture, always):
    p = ROOT + '/Materials/Instances'
    ensure_dir(p)
    mi = fresh_asset('MI_' + name, p, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, text_mat)
    mel.set_material_instance_texture_parameter_value(mi, 'Tex', texture)
    mel.set_material_instance_scalar_parameter_value(mi, 'Always', always)
    eal.save_loaded_asset(mi)
    return mi


def import_file(filename, dest):
    ensure_dir(dest)
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', filename)
    t.set_editor_property('destination_path', dest)
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    at.import_asset_tasks([t])
    paths = t.get_editor_property('imported_object_paths')
    return unreal.load_asset(paths[0]) if paths else None


# ---------------- 액터 ----------------
def mesh(kind):
    if kind not in _MESH:
        _MESH[kind] = unreal.load_asset(SHAPES[kind])
    return _MESH[kind]


def clear_actors(prefixes=('LFF_', 'CH_', 'CAM_')):
    n = 0
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith(prefixes):
            eas.destroy_actor(a)
            n += 1
    return n


def root(label, loc=(0, 0, 0)):
    """보이지 않는 기준점(자식을 붙여 한꺼번에 움직일 때 사용)."""
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, vec(*loc), rot())
    a.set_actor_label(label)
    return a


def shape(kind, label, loc, scale, mi, r=(0, 0, 0), parent=None, shadow=True):
    """scale 은 기본 도형(100cm) 대비 배율. r=(roll, pitch, yaw)."""
    a = eas.spawn_actor_from_object(mesh(kind), vec(*loc), rot(*r))
    a.set_actor_label(label)
    a.set_actor_scale3d(vec(*scale))
    smc = a.static_mesh_component
    if mi:
        smc.set_material(0, mi)
    if not shadow:
        smc.set_cast_shadow(False)
    if parent:
        a.attach_to_actor(parent, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, False)
    return a


def camera(label, loc, target, focal=50.0, fstop=2.8):
    r = unreal.MathLibrary.find_look_at_rotation(vec(*loc), vec(*target))
    c = eas.spawn_actor_from_class(unreal.CineCameraActor, vec(*loc), r)
    c.set_actor_label(label)
    comp = c.get_cine_camera_component()
    try:
        comp.set_editor_property('current_focal_length', focal)
        comp.set_editor_property('current_aperture', fstop)
        d = (vec(*target) - vec(*loc)).length()
        fs = unreal.CameraFocusSettings()
        fs.set_editor_property('focus_method', unreal.CameraFocusMethod.MANUAL)
        fs.set_editor_property('manual_focus_distance', d)
        comp.set_editor_property('focus_settings', fs)
    except Exception as e:  # noqa: BLE001
        log('카메라 초점 설정 건너뜀: %r' % e)
    return c


def look(loc, target):
    r = unreal.MathLibrary.find_look_at_rotation(vec(*loc), vec(*target))
    return (r.roll, r.pitch, r.yaw)


# ---------------- 시퀀스 ----------------
class Seq:
    def __init__(self, seq, end_frame):
        self.seq = seq
        self.end = end_frame
        self.bind = {}
        self.sec = {}

    def _section(self, actor):
        key = actor.get_path_name()
        if key not in self.sec:
            b = self.seq.add_possessable(actor)
            tr = b.add_track(unreal.MovieScene3DTransformTrack)
            s = tr.add_section()
            s.set_range(0, self.end)
            self.bind[key] = b
            self.sec[key] = s
            # 키가 없는 채널은 현재 위치·회전·크기를 기본값으로 (0 으로 튀지 않게)
            rc = actor.get_editor_property('root_component')
            l = rc.get_editor_property('relative_location')
            r = rc.get_editor_property('relative_rotation')
            sc = rc.get_editor_property('relative_scale3d')
            for c, v in zip(self._channels(s)[:9], (l.x, l.y, l.z, r.roll, r.pitch, r.yaw, sc.x, sc.y, sc.z)):
                c.set_default(float(v))
        return self._channels(self.sec[key])

    @staticmethod
    def _channels(s):
        return s.get_all_channels() if hasattr(s, 'get_all_channels') else unreal.MovieSceneSectionExtensions.get_all_channels(s)

    def key(self, actor, f, loc=None, r=None, scale=None, interp='auto'):
        """상대 변환 키 (주어진 항목만). r=(roll, pitch, yaw)."""
        ch = self._section(actor)
        mode = {'auto': unreal.MovieSceneKeyInterpolation.AUTO,
                'linear': unreal.MovieSceneKeyInterpolation.LINEAR,
                'const': unreal.MovieSceneKeyInterpolation.CONSTANT}[interp]
        for off, vals in ((0, loc), (3, r), (6, scale)):
            if vals is None:
                continue
            for i, v in enumerate(vals):
                ch[off + i].add_key(unreal.FrameNumber(int(f)), float(v), interpolation=mode)

    def show(self, actor, f, on, base_scale):
        self.key(actor, f, scale=(base_scale if on else (0.0001, 0.0001, 0.0001)), interp='const')

    def camera_cuts(self, cuts):
        tr = self.seq.add_track(unreal.MovieSceneCameraCutTrack)
        for cam, f0, f1 in cuts:
            b = self.seq.add_possessable(cam)
            s = tr.add_section()
            s.set_range(f0, f1)
            s.set_camera_binding_id(self.seq.get_binding_id(b))

    def mpc_keys(self, mpc, keys):
        """keys = {'Dim': [(frame, value), ...], 'Slogan': [...]}"""
        tr = self.seq.add_track(unreal.MovieSceneMaterialParameterCollectionTrack)
        try:
            tr.set_editor_property('mpc', mpc)
        except Exception:  # noqa: BLE001
            tr.set_editor_property('MPC', mpc)
        s = tr.add_section()
        s.set_range(0, self.end)
        tick = self.seq.get_tick_resolution()
        ratio = tick.numerator / float(tick.denominator) / FPS
        for name, kv in keys.items():
            for f, v in kv:
                s.add_scalar_parameter_key(name, unreal.FrameNumber(int(round(f * ratio))), float(v))

    def audio(self, sound, start_frame):
        tr = self.seq.add_track(unreal.MovieSceneAudioTrack)
        s = tr.add_section()
        s.set_sound(sound)
        dur = max(1, F(sound.get_editor_property('duration')))
        s.set_range(start_frame, start_frame + dur)

"""공통 도우미: 컬렉션, 재질, 기본 도형, 글자, 곡선, 키프레임.
Blender 4.0 ~ 4.2 이상에서 동작하도록 버전 차이를 감쌌다.
"""
import bpy
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, 'assets', 'fonts')
_MATS = {}
_FONTS = {}
FONT_K = 2.8  # Noto Sans KR 은 size 1 일 때 한글 높이가 약 0.33 이라 보정


# ---------- 기본 ----------
def rad(d):
    return math.radians(d)


def lerp(a, b, t):
    return a + (b - a) * t


def srgb(h):
    h = h.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()
    _FONTS.clear()


def collection(name, parent=None):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    par = parent or bpy.context.scene.collection
    if col.name not in [c.name for c in par.children]:
        par.children.link(col)
    lc = _find_layer_collection(bpy.context.view_layer.layer_collection, col.name)
    bpy.context.view_layer.active_layer_collection = lc
    return col


def _find_layer_collection(lc, name):
    if lc.collection.name == name:
        return lc
    for c in lc.children:
        r = _find_layer_collection(c, name)
        if r:
            return r
    return None


def _link(o):
    bpy.context.view_layer.active_layer_collection.collection.objects.link(o)


# ---------- 재질 ----------
def _bsdf_input(b, *names):
    for n in names:
        if n in b.inputs:
            return b.inputs[n]
    return None


def set_blend(m):
    if hasattr(m, 'surface_render_method'):
        m.surface_render_method = 'BLENDED'
    if hasattr(m, 'blend_method'):
        m.blend_method = 'BLEND'
    if hasattr(m, 'shadow_method'):
        m.shadow_method = 'NONE'
    if hasattr(m, 'show_transparent_back'):
        m.show_transparent_back = False


def mat(name, color, rough=0.65, emit=0.0, alpha=None, unique=False):
    """Principled 재질. emit>0 이면 같은 색으로 자체발광."""
    if not unique and name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(color)
    b.inputs['Roughness'].default_value = rough
    spec = _bsdf_input(b, 'Specular IOR Level', 'Specular')
    if spec:
        spec.default_value = 0.25
    if emit:
        ec = _bsdf_input(b, 'Emission Color', 'Emission')
        ec.default_value = srgb(color)
        b.inputs['Emission Strength'].default_value = emit
    if alpha is not None:
        b.inputs['Alpha'].default_value = alpha
        set_blend(m)
    m.diffuse_color = srgb(color)
    if not unique:
        _MATS[name] = m
    return m


def flat_mat(name, color, strength=1.0, alpha=1.0):
    """조명 영향을 받지 않는 단색(자막·글자용). alpha 키프레임 가능."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = srgb(color)
    em.inputs['Strength'].default_value = strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.name = 'ALPHA'
    mix.inputs[0].default_value = alpha
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    set_blend(m)
    return m


def key_alpha(m, f, a):
    node = m.node_tree.nodes['ALPHA']
    node.inputs[0].default_value = a
    node.inputs[0].keyframe_insert('default_value', frame=f)


# ---------- 도형 ----------
def empty(name, loc=(0, 0, 0), parent=None, rot=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    o.empty_display_size = 0.1
    _link(o)
    o.parent = parent
    o.location = loc
    o.rotation_euler = rot
    return o


def prim(kind, name, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), m=None, parent=None, smooth=False, **kw):
    if kind == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=1)
    elif kind == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=kw.get('seg', 24), ring_count=kw.get('rings', 12), radius=1)
    elif kind == 'ico':
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=kw.get('sub', 2), radius=1)
    elif kind == 'cyl':
        bpy.ops.mesh.primitive_cylinder_add(vertices=kw.get('verts', 20), radius=1, depth=1)
    elif kind == 'cone':
        bpy.ops.mesh.primitive_cone_add(vertices=kw.get('verts', 8), radius1=1, radius2=kw.get('r2', 0), depth=1)
    elif kind == 'plane':
        bpy.ops.mesh.primitive_plane_add(size=1)
    elif kind == 'torus':
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=kw.get('minor', 0.25),
                                         major_segments=kw.get('maj', 32), minor_segments=kw.get('mins', 10))
    o = bpy.context.active_object
    o.name = name
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    o.scale = scale
    o['base_scale'] = list(scale)
    if kw.get('bevel'):
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        o['base_scale'] = [1, 1, 1]
        mod = o.modifiers.new('bevel', 'BEVEL')
        mod.width = kw['bevel']
        mod.segments = 3
    o.parent = parent
    o.location = loc
    o.rotation_euler = [rad(r) for r in rot]
    if m:
        o.data.materials.append(m)
    return o


def get_font(weight=800):
    if weight not in _FONTS:
        _FONTS[weight] = bpy.data.fonts.load(os.path.join(FONT_DIR, 'NotoSansKR-%d-korean.ttf' % weight))
    return _FONTS[weight]


def text(name, body, size, loc=(0, 0, 0), rot=(90, 0, 0), m=None, parent=None, align='CENTER', extrude=0.0, weight=800):
    """기본은 세워서(-Y 방향을 바라봄) 배치."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.font = get_font(weight)
    cu.size = size * FONT_K  # 한글 글자 높이 ≈ size 가 되도록 보정
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.extrude = extrude
    o = bpy.data.objects.new(name, cu)
    _link(o)
    o.parent = parent
    o.location = loc
    o.rotation_euler = [rad(r) for r in rot]
    if m:
        cu.materials.append(m)
    o['base_scale'] = [1, 1, 1]
    return o


def curve(name, pts, bevel, m=None, parent=None, loc=(0, 0, 0)):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(pts) - 1)
    for bp, co in zip(sp.bezier_points, pts):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cu.bevel_depth = bevel
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    o = bpy.data.objects.new(name, cu)
    _link(o)
    o.parent = parent
    o.location = loc
    if m:
        cu.materials.append(m)
    o['base_scale'] = [1, 1, 1]
    return o


# ---------- 키프레임 ----------
def key(o, attr, f, val):
    setattr(o, attr, val)
    o.keyframe_insert(attr, frame=f)


def _set_interp(o, data_path, mode):
    ad = o.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        if fc.data_path == data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = mode


def show(o, f, on):
    """scale 을 0/원래값으로 바꿔 보이기·숨기기 (자식까지 함께 숨겨짐)."""
    base = o.get('base_scale', [1, 1, 1])
    o.scale = base if on else (0, 0, 0)
    o.keyframe_insert('scale', frame=f)
    _set_interp(o, 'scale', 'CONSTANT')


def visible_only(o, ranges):
    """ranges=[(f0,f1),...] 구간에서만 보이게."""
    show(o, 0, False)
    for f0, f1 in ranges:
        show(o, f0, True)
        show(o, f1 + 1, False)


def pop(o, f, dur=8, on=True):
    """튀어나오듯 등장(또는 사라짐)."""
    base = list(o.get('base_scale', [1, 1, 1]))
    if on:
        o.scale = (0, 0, 0); o.keyframe_insert('scale', frame=f)
        o.scale = [b * 1.12 for b in base]; o.keyframe_insert('scale', frame=f + int(dur * 0.7))
        o.scale = base; o.keyframe_insert('scale', frame=f + dur)
    else:
        o.scale = base; o.keyframe_insert('scale', frame=f)
        o.scale = (0, 0, 0); o.keyframe_insert('scale', frame=f + dur)


def cycle_fcurves(o):
    ad = o.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            fc.modifiers.new('CYCLES')


def look_at(o, target):
    from mathutils import Vector
    d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

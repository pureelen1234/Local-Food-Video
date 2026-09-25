"""배경 세트와 소품. 세트마다 X 위치를 떨어뜨려 한 장면(Scene) 안에 모두 배치한다."""
import bpy
import math
import random
from lff_core import prim, empty, mat, flat_mat, text, curve, rad, srgb, set_blend

SET_X = {'field': 0, 'map': 300, 'store': 600, 'street': 900, 'dining': 1200, 'end': 1500}


# ---------- 농산물 ----------
def veg(kind, loc, s=1.0, parent=None, name=None, rot=(0, 0, 0)):
    n = name or ('veg_' + kind)
    g = empty(n, loc, parent, [rad(r) for r in rot])
    g.scale = (s, s, s)
    g['base_scale'] = [s, s, s]
    if kind == 'tomato':
        prim('sphere', n + '_b', (0, 0, 0), (0.07, 0.07, 0.062), m=mat('tomato', '#e34b3b', .35), parent=g, smooth=True, seg=16, rings=10)
        prim('cone', n + '_c', (0, 0, 0.06), (0.04, 0.04, 0.012), m=mat('calyx', '#3f8a3a'), parent=g, verts=5)
    elif kind == 'cabbage':
        prim('sphere', n + '_b', (0, 0, 0), (0.12, 0.12, 0.11), m=mat('cabbage', '#8fcf6a', .6), parent=g, smooth=True, seg=16, rings=10)
        prim('sphere', n + '_l', (0, -0.02, 0.01), (0.13, 0.1, 0.09), rot=(20, 0, 0), m=mat('cabbage2', '#5faa48', .6), parent=g, smooth=True, seg=16, rings=10)
    elif kind == 'lettuce':
        prim('ico', n + '_b', (0, 0, 0), (0.13, 0.13, 0.09), m=mat('lettuce', '#7cc36a', .7), parent=g, sub=1)
    elif kind == 'carrot':
        prim('cone', n + '_b', (0, 0, 0), (0.035, 0.035, 0.2), rot=(90, 0, 0), m=mat('carrot', '#f08a2c', .5), parent=g, verts=10)
        prim('cone', n + '_l', (0, 0.12, 0.02), (0.03, 0.03, 0.08), rot=(-90, 0, 0), m=mat('leaf', '#6fae5a'), parent=g, verts=5)
    elif kind == 'potato':
        prim('sphere', n + '_b', (0, 0, 0), (0.07, 0.055, 0.05), m=mat('potato', '#c9a06a', .8), parent=g, smooth=True, seg=12, rings=8)
    elif kind == 'corn':
        prim('cyl', n + '_b', (0, 0, 0), (0.04, 0.04, 0.2), rot=(90, 0, 0), m=mat('corn', '#f4cf45', .5), parent=g, verts=12)
        prim('cone', n + '_h', (0, 0.1, 0), (0.045, 0.045, 0.1), rot=(-90, 0, 0), m=mat('husk', '#7cc36a'), parent=g, verts=8)
    elif kind == 'eggplant':
        prim('sphere', n + '_b', (0, 0, 0), (0.05, 0.1, 0.05), m=mat('eggplant', '#6d3b86', .3), parent=g, smooth=True, seg=14, rings=8)
        prim('cone', n + '_c', (0, 0.1, 0), (0.035, 0.035, 0.04), rot=(-90, 0, 0), m=mat('calyx', '#3f8a3a'), parent=g, verts=6)
    return g


VEGS = ['cabbage', 'tomato', 'carrot', 'potato', 'corn', 'eggplant', 'lettuce']


def crate(loc, w=0.7, d=0.4, h=0.22, items=(), s=1.0, parent=None, seed=0):
    g = empty('crate', loc, parent)
    wood, wood2 = mat('wood', '#c8894f', .8), mat('wood2', '#a86d3a', .8)
    prim('cube', 'crate_box', (0, 0, h / 2), (w, d, h), m=wood, parent=g)
    prim('cube', 'crate_slat', (0, -d / 2 - 0.004, h * 0.5), (w, 0.01, 0.025), m=wood2, parent=g)
    rnd = random.Random(seed)
    n = len(items)
    for i, k in enumerate(items):
        x = -w / 2 + w * (i + 0.5) / n
        veg(k, (x + rnd.uniform(-.03, .03), rnd.uniform(-.08, .08), h + 0.05 * s), s, g, rot=(0, 0, rnd.uniform(-40, 40)))
    return g


def basket(loc, parent=None, name='basket'):
    g = empty(name, loc, parent)
    prim('cyl', name + '_body', (0, 0, 0.1), (0.2, 0.15, 0.2), m=mat('wicker', '#c99a5a', .9), parent=g, verts=20)
    prim('torus', name + '_rim', (0, 0, 0.2), (0.2, 0.15, 0.3), m=mat('wicker2', '#a87a3e', .9), parent=g, minor=0.1)
    return g


def truck(name, col, parent=None):
    g = empty(name, (0, 0, 0), parent)
    body = mat(name + '_col', col, .5)
    prim('cube', name + '_bed', (-0.12, 0, 0.16), (0.36, 0.26, 0.18), m=body, parent=g, bevel=0.01)
    prim('cube', name + '_cab', (0.16, 0, 0.17), (0.18, 0.24, 0.2), m=body, parent=g, bevel=0.02)
    prim('cube', name + '_win', (0.25, 0, 0.21), (0.01, 0.2, 0.08), m=mat('glass', '#d8eef7', .1), parent=g)
    for x in (-0.18, 0.15):
        for y in (-0.13, 0.13):
            prim('cyl', name + '_wheel', (x, y, 0.06), (0.06, 0.06, 0.04), rot=(90, 0, 0), m=mat('tire', '#333333'), parent=g, verts=12)
    for i, k in enumerate(['cabbage', 'tomato', 'carrot']):
        veg(k, (-0.22 + i * 0.1, 0, 0.3), 0.55, g)
    return g


def sky_world():
    w = bpy.data.worlds.new('LFF_World')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = -0.05
    mr.inputs['From Max'].default_value = 0.5
    mix = nt.nodes.new('ShaderNodeMixRGB')
    mix.name = 'SKY'
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.name = 'BG'
    out = nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], mix.inputs['Fac'])
    nt.links.new(mix.outputs[0], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], out.inputs[0])
    return w


def sky_key(f, horizon, zenith, strength):
    nt = bpy.context.scene.world.node_tree
    mix, bg = nt.nodes['SKY'], nt.nodes['BG']
    mix.inputs['Color1'].default_value = srgb(horizon)
    mix.inputs['Color2'].default_value = srgb(zenith)
    bg.inputs['Strength'].default_value = strength
    mix.inputs['Color1'].keyframe_insert('default_value', frame=f)
    mix.inputs['Color2'].keyframe_insert('default_value', frame=f)
    bg.inputs['Strength'].keyframe_insert('default_value', frame=f)


def fog_mat(name, color='#f4efe9'):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (2, 2, 2)
    gr = nt.nodes.new('ShaderNodeTexGradient')
    gr.gradient_type = 'SPHERICAL'
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.name = 'STR'
    mul.inputs[1].default_value = 0.6
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = srgb(color)
    em.inputs['Strength'].default_value = 1.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], gr.inputs['Vector'])
    nt.links.new(gr.outputs['Fac'], mul.inputs[0])
    nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    set_blend(m)
    return m


# ---------- A. 밭 ----------
def build_field():
    X = SET_X['field']
    prim('plane', 'field_ground', (X, 60, 0), (420, 600, 1), m=mat('field_ground', '#86b85c', .9))
    soil = mat('soil', '#8a6a44', .95)
    lettuce = mat('lettuce', '#7cc36a', .7)
    for k in range(-12, 13):
        x = X + 3.6 * k - 1.8
        prim('cube', 'ridge', (x, 30, 0.06), (1.0, 180, 0.12), m=soil)
        c = prim('ico', 'crops', (x, -58, 0.18), (0.3, 0.3, 0.22), m=lettuce, sub=1)
        arr = c.modifiers.new('arr', 'ARRAY')
        arr.use_relative_offset = False
        arr.use_constant_offset = True
        arr.constant_offset_displace = (0, 1.5 / 0.3, 0)
        arr.count = 110
    # 먼 산, 호수(춘천 호반)
    rnd = random.Random(3)
    for i in range(14):
        x = X - 260 + i * 40 + rnd.uniform(-10, 10)
        h = rnd.uniform(35, 70)
        prim('cone', 'mountain', (x, 330 + rnd.uniform(-30, 30), h / 2 - 5), (rnd.uniform(45, 70), 40, h),
             m=mat('mount%d' % (i % 3), ['#7f9bb8', '#8aa6c0', '#6f8fa6'][i % 3], .95), verts=7)
    for i in range(10):
        x = X - 200 + i * 45 + rnd.uniform(-10, 10)
        prim('cone', 'hill', (x, 230 + rnd.uniform(-10, 10), 8), (rnd.uniform(30, 45), 25, 22), m=mat('hill', '#6f9e7e', .95), verts=8)
    prim('plane', 'lake', (X, 185, 0.05), (420, 60, 1), m=mat('lake', '#a9cfe3', .08))
    # 해 (자체발광 원판)
    sun = prim('sphere', 'sun_disc', (X + 40, 400, 10), (12, 12, 12), m=mat('sun_disc', '#ffe29a', emit=3.0), smooth=True)
    # 안개 (부드러운 반투명 판)
    fogs = []
    for i, (y, z, sx, sz) in enumerate([(15, 2.5, 140, 10), (45, 4, 200, 14), (95, 6, 280, 20)]):
        fm = fog_mat('fog%d' % i)
        fogs.append(fm)
        prim('plane', 'fog', (X + rnd.uniform(-10, 10), y, z), (sx, sz, 1), rot=(90, 0, 0), m=fm)
    # 농부 작업 구역
    FX = X + 7.2
    for j, y in enumerate((-0.35, 0.55, 1.45)):
        g = empty('tomato_plant', (FX + 0.95, y, 0))
        prim('cyl', 'stake', (0, 0, 0.8), (0.018, 0.018, 1.6), m=mat('stake', '#9a7650'), parent=g, verts=6)
        for k in range(6):
            prim('ico', 'tleaf', ((k % 2 - .5) * 0.18, 0, 0.45 + k * 0.2), (0.2, 0.16, 0.14), m=mat('tleaf', '#4f9a41', .8), parent=g, sub=1)
        for k in range(4):
            veg('tomato', ((k % 2 - .5) * 0.3, -0.12, 0.6 + k * 0.22), 1.0, g)
    prim('cube', 'farm_crate', (FX + 0.35, -0.65, 0.3), (0.5, 0.4, 0.6), m=mat('wood', '#c8894f', .8))
    b = basket((FX + 0.35, -0.65, 0.6), name='farm_basket')
    return dict(fogs=fogs, sun=sun, FX=FX, basket=b)


# ---------- B. 지도(디오라마) ----------
def build_map(L):
    X = SET_X['map']
    prim('plane', 'map_floor', (X, 0, -0.6), (80, 80, 1), m=mat('map_floor', '#f5f0e1', .9))
    prim('cube', 'map_board', (X, 0, -0.05), (34, 24, 0.1), m=mat('map_board', '#d7eac0', .9))
    rnd = random.Random(7)
    prim('cyl', 'map_lake', (X + 5.2, -2.6, 0.01), (1.9, 1.2, 0.02), m=mat('map_lake', '#9fd0ea', .15), verts=32)
    text('map_lake_t', '호수', 0.32, (X + 5.2, -2.6, 0.04), (0, 0, 0), m=flat_mat('map_lake_m', '#4f88a8'), weight=400)
    for i in range(9):
        prim('cone', 'map_mount', (X - 7 + i * 1.75, 4.3 + rnd.uniform(-.3, .3), 0.5), (0.8, 0.6, 1.0), m=mat('map_mount', '#b9d49a', .9), verts=6)
    tree_m, trunk_m = mat('tree', '#7fb45c', .8), mat('trunk', '#8a6a44')
    for i in range(90):
        x, y = rnd.uniform(-15, 15), rnd.uniform(-10, 3.8)
        if (-5.8 < x < 3.5 and -2.2 < y < 1.8) or (x > 3 and y < -1):
            continue
        prim('cone', 'map_tree', (X + x, y, 0.3), (0.18, 0.18, 0.5), m=tree_m, verts=6)
    farm = (X - 4, -1.0)
    store = (X + 2.2, 0.8)
    # 농가
    fg = empty('map_farm', (farm[0], farm[1], 0))
    for i in range(3):
        prim('cube', 'plot', (-1.3 + i * 0.55, 0.1, 0.03), (0.48, 0.8, 0.06), m=mat('plot', '#9fd06e', .9), parent=fg)
    prim('cube', 'house', (0.55, 0.2, 0.25), (0.6, 0.5, 0.5), m=mat('house', '#fff4dc'), parent=fg)
    prim('cone', 'roof', (0.55, 0.2, 0.68), (0.5, 0.42, 0.35), rot=(0, 0, 45), m=mat('roof', '#d9603f'), parent=fg, verts=4)
    text('map_farm_t', L['farmLabel'], 0.34, (-0.3, -0.85, 0.03), (0, 0, 0), m=flat_mat('lbl_dark', '#4a3b2c'), parent=fg)
    # 직매장
    sg = empty('map_store', (store[0], store[1], 0))
    prim('cube', 'mstore', (0, 0, 0.35), (1.3, 0.8, 0.7), m=mat('mstore', '#fffaf0'), parent=sg)
    for i in range(6):
        prim('cube', 'awning', (-0.55 + i * 0.22, -0.45, 0.62), (0.22, 0.2, 0.05), rot=(-25, 0, 0),
             m=mat('awn%d' % (i % 2), ['#5fae4c', '#ffffff'][i % 2]), parent=sg)
    prim('cube', 'mstore_win', (0, -0.405, 0.28), (0.9, 0.01, 0.3), m=mat('glass', '#c9e6f2', .1), parent=sg)
    text('map_store_sign', L['storeShort'], 0.3, (0, -0.1, 0.95), (60, 0, 0), m=flat_mat('lbl_green', '#3f7d4c'), parent=sg)
    text('map_store_t', L['storeName'], 0.3, (0, -0.9, 0.03), (0, 0, 0), m=flat_mat('lbl_dark2', '#4a3b2c'), parent=sg)
    # 경로
    far_pts = [(farm[0], farm[1], .06), (X - 7.5, 1.5, .06), (X - 5, 6.5, .06), (X + 3, 7.5, .06), (X + 9.5, 3.5, .06),
               (X + 8.5, -4.5, .06), (X + 5, 1.5, .06), (store[0], store[1], .06)]
    far = curve('route_far', far_pts, 0.07, mat('route_far', '#9a9a9a', .6))
    near = curve('route_near', [(farm[0], farm[1], .07), (X - 1.0, 0.5, .07), (store[0], store[1], .07)], 0.09, mat('route_near', '#4fae3c', .5))
    far_t = text('map_far_t', L['farLabel'], 0.5, (X + 6.2, 5.2, 0.05), (0, 0, 0), m=flat_mat('lbl_grey', '#8a8a8a'))
    near_t = text('map_near_t', L['nearLabel'], 0.46, (X - 1.0, 1.25, 0.05), (0, 0, 0), m=flat_mat('lbl_ngreen', '#2f7d2a'))
    tf = truck('truck_far', '#9a9a9a')
    tn = truck('truck_near', '#5f9c50')
    for t, c in ((tf, far), (tn, near)):
        con = t.constraints.new('FOLLOW_PATH')
        con.target = c
        con.use_fixed_location = True
        con.use_curve_follow = True
        con.forward_axis = 'FORWARD_X'
        con.up_axis = 'UP_Z'
    # 탄소발자국 패널 (카메라를 향해 기울임)
    panel = empty('carbon_panel', (0, 0, 0))
    prim('cube', 'panel_bd', (0, 0.05, 0), (6.5, 0.02, 1.6), m=flat_mat('panel_bd', '#cfe3bf'), parent=panel, bevel=0.5)
    prim('cube', 'panel_bg', (0, 0.02, 0), (6.4, 0.04, 1.5), m=flat_mat('panel_bg', '#fffdf6'), parent=panel, bevel=0.45)
    foot = empty('footprint', (-2.3, -0.05, 0), panel)
    gm = flat_mat('foot_m', '#7a7a7a')
    prim('cyl', 'sole', (0, 0, -0.08), (0.32, 0.45, 0.02), rot=(90, 0, 0), m=gm, parent=foot, verts=24)
    for i, (x, z, r) in enumerate([(-0.22, 0.52, .1), (-0.06, 0.6, .09), (0.09, 0.57, .08), (0.22, 0.5, .07)]):
        prim('cyl', 'toe', (x, 0, z), (r, r, 0.02), rot=(90, 0, 0), m=gm, parent=foot, verts=14)
    text('co2', 'CO2', 0.22, (0, -0.02, -0.1), (90, 0, 0), m=flat_mat('co2_m', '#ffffff'), parent=foot)
    arrow = empty('carbon_arrow', (-1.25, -0.05, 0), panel)
    am = flat_mat('arrow_m', '#5fae4c')
    prim('cube', 'arrow_shaft', (0, 0, 0.15), (0.12, 0.02, 0.5), m=am, parent=arrow)
    prim('cone', 'arrow_head', (0, 0, -0.22), (0.26, 0.02, 0.3), rot=(180, 0, 0), m=am, parent=arrow, verts=24)
    text('carbon_t', L['carbonLabel'], 0.5, (0.9, -0.05, -0.02), (90, 0, 0), m=flat_mat('lbl_cgreen', '#2f7d2a'), parent=panel)
    return dict(far=far, near=near, far_t=far_t, near_t=near_t, tf=tf, tn=tn, panel=panel, foot=foot)


# ---------- C. 직매장 ----------
def name_tag(L, loc, parent=None, name='name_tag', rot=(0, 0, 0)):
    g = empty(name, loc, parent, [rad(r) for r in rot])
    prim('cyl', name + '_stick', (0, 0.01, -0.12), (0.01, 0.01, 0.22), m=mat('stake', '#9a7650'), parent=g, verts=6)
    prim('cube', name + '_border', (0, 0.006, 0.07), (0.55, 0.012, 0.25), m=flat_mat(name + '_bm', '#5f9c50'), parent=g)
    prim('cube', name + '_card', (0, 0, 0.07), (0.52, 0.012, 0.22), m=flat_mat(name + '_cm', '#fffdf4'), parent=g)
    prim('cyl', name + '_icon', (-0.19, -0.008, 0.07), (0.055, 0.055, 0.005), rot=(90, 0, 0), m=flat_mat(name + '_im', '#e6f2da'), parent=g, verts=20)
    prim('cyl', name + '_iconhat', (-0.19, -0.011, 0.095), (0.05, 0.05, 0.003), rot=(90, 0, 0), m=flat_mat(name + '_ihm', '#dcb65a'), parent=g, verts=3)
    prim('cyl', name + '_iconface', (-0.19, -0.012, 0.065), (0.022, 0.022, 0.003), rot=(90, 0, 0), m=flat_mat(name + '_ifm', '#d9a27c'), parent=g, verts=16)
    text(name + '_t1', L['producerTitle'], 0.034, (-0.115, -0.008, 0.13), (90, 0, 0), m=flat_mat(name + '_t1m', '#5f9c50'), parent=g, align='LEFT')
    text(name + '_t2', L['producerName'], 0.038, (-0.115, -0.008, 0.075), (90, 0, 0), m=flat_mat(name + '_t2m', '#3b2e22'), parent=g, align='LEFT')
    text(name + '_t3', L['producerArea'], 0.03, (-0.115, -0.008, 0.02), (90, 0, 0), m=flat_mat(name + '_t3m', '#7a6a58'), parent=g, align='LEFT', weight=400)
    g['base_scale'] = [1, 1, 1]
    return g


def build_store(L):
    X = SET_X['store']
    prim('plane', 'store_floor', (X, 0, 0), (30, 30, 1), m=mat('store_floor', '#c9a07a', .7))
    wall = mat('store_wall', '#f6e4c8', .9)
    prim('plane', 'store_wall', (X, 4, 4), (30, 8, 1), rot=(90, 0, 0), m=wall)
    for i in range(-24, 25):
        prim('cube', 'plank', (X + i * 0.55, 3.98, 4), (0.02, 0.01, 8), m=mat('plank', '#e6caa2', .9))
    shelf = mat('shelf', '#b07a48', .8)
    rnd = random.Random(11)
    for r, z in enumerate((1.0, 1.75)):
        prim('cube', 'shelf', (X, 3.75, z), (11, 0.5, 0.05), m=shelf)
        for i in range(12):
            crate((X - 5.0 + i * 0.9, 3.75, z + 0.025), 0.7, 0.35, 0.18,
                  [VEGS[(i + r * 3) % 7], VEGS[(i + r * 3 + 2) % 7], VEGS[(i + r * 3 + 4) % 7]], 0.8, seed=i + r * 20)
    prim('cube', 'sign', (X, 3.9, 2.75), (3.8, 0.05, 0.62), m=mat('sign', '#3f7d4c', .7), bevel=0.04)
    text('sign_t', L['storeSign'], 0.24, (X, 3.86, 2.74), (90, 0, 0), m=flat_mat('sign_tm', '#fff8e6'))
    for x in (-2.8, 2.8):
        prim('cyl', 'cord', (X + x, 1.5, 3.5), (0.01, 0.01, 1.2), m=mat('cord', '#5a4a3a'))
        prim('cone', 'shade', (X + x, 1.5, 2.85), (0.3, 0.3, 0.25), m=mat('shade', '#e7b24c', .5), verts=16)
        l = bpy.data.lights.new('pend', 'POINT')
        l.energy = 120
        l.color = (1.0, 0.85, 0.65)
        lo = bpy.data.objects.new('pend_light', l)
        bpy.context.view_layer.active_layer_collection.collection.objects.link(lo)
        lo.location = (X + x, 1.5, 2.65)
    al = bpy.data.lights.new('store_fill', 'AREA')
    al.energy = 900
    al.size = 6
    al.color = (1.0, 0.95, 0.88)
    ao = bpy.data.objects.new('store_fill', al)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(ao)
    ao.location = (X - 1, -5, 4.5)
    ao.rotation_euler = (rad(55), 0, rad(-10))
    # 진열대
    prim('cube', 'table', (X, 0.2, 0.42), (3.4, 1.0, 0.84), m=mat('table', '#b9804c', .8), bevel=0.02)
    prim('cube', 'table_edge', (X, -0.305, 0.8), (3.42, 0.02, 0.06), m=mat('wood2', '#a86d3a', .8))
    items = [['carrot'] * 4, ['tomato'] * 5, ['potato', 'corn', 'potato'], ['eggplant'] * 3]
    for i, it in enumerate(items):
        crate((X - 1.2 + i * 0.8, 0.2, 0.84), 0.72, 0.8, 0.14, it, 1.3, seed=40 + i)
    placed = veg('cabbage', (X + 0.05, 0.02, 1.08), 1.3, name='placed_cabbage')
    tag = name_tag(L, (X + 0.7, -0.33, 0.97), name='name_tag', rot=(0, 0, -4))
    return dict(placed=placed, tag=tag)


def bubble(name, body, loc, w, parent=None, size=0.12):
    g = empty(name, loc, parent)
    prim('cyl', name + '_bd', (0, 0.02, 0), (w / 2 + 0.03, 0.19, 0.01), rot=(90, 0, 0), m=flat_mat(name + '_bdm', '#c9b48f'), parent=g, verts=32)
    prim('cyl', name + '_bg', (0, 0.01, 0), (w / 2, 0.16, 0.01), rot=(90, 0, 0), m=flat_mat(name + '_bm', '#ffffff'), parent=g, verts=32)
    prim('cone', name + '_tail', (-w * 0.2, 0.01, -0.17), (0.07, 0.07, 0.12), rot=(90, 0, 0), m=flat_mat(name + '_tm', '#ffffff'), parent=g, verts=3)
    text(name + '_t', body, size, (0, -0.005, 0), (90, 0, 0), m=flat_mat(name + '_txm', '#3b2e22'), parent=g)
    g['base_scale'] = [1, 1, 1]
    return g


# ---------- D. 퇴근길 거리 ----------
def build_street(L):
    X = SET_X['street']
    city = empty('city', (X, 0, 0))
    prim('cube', 'sidewalk', (10, 0, 0.05), (90, 2.4, 0.1), m=mat('sidewalk', '#dcc6aa', .9), parent=city)
    for i in range(-40, 60):
        prim('cube', 'tile', (i * 1.0, 0, 0.101), (0.02, 2.4, 0.002), m=mat('tile', '#c7ae90'), parent=city)
    prim('plane', 'road', (10, -3, 0.0), (90, 3.6, 1), m=mat('road', '#6b6670', .8), parent=city)
    prim('plane', 'grass_back', (10, 5.5, 0.02), (90, 9, 1), m=mat('grass', '#8fbf6e', .9), parent=city)
    rnd = random.Random(5)
    x = -35.0
    wall_cols = ['#e2a88c', '#c98a78', '#e9b89a', '#d49a86']
    while x < 55:
        w = rnd.uniform(3, 5)
        h = rnd.uniform(2.5, 5.5)
        m = building_mat('bld%d' % (int(x) % 4), wall_cols[int(abs(x)) % 4])
        prim('cube', 'building', (x + w / 2, 15.0, h / 2), (w - 0.2, 3, h), m=m, parent=city)
        x += w
    for i in range(-6, 10):
        tx = i * 6.0
        prim('cyl', 'trunk', (tx, 2.6, 0.8), (0.08, 0.08, 1.6), m=mat('trunk', '#7a5a44'), parent=city, verts=8)
        prim('ico', 'crown', (tx, 2.6, 2.0), (0.8, 0.8, 0.8), m=mat('tree', '#7fb45c', .8), parent=city, sub=2)
        prim('cyl', 'lamp', (tx + 3, -1.1, 1.6), (0.04, 0.04, 3.2), m=mat('lamp', '#5a5a66'), parent=city, verts=8)
        prim('sphere', 'lamp_head', (tx + 3, -1.1, 3.25), (0.16, 0.16, 0.1), m=mat('lamp_glow', '#fff2b8', emit=2), parent=city, seg=12, rings=6)
    sun = prim('sphere', 'street_sun', (X + 25, 80, 7), (6, 6, 6), m=mat('sun_evening', '#ffc46b', emit=3.0), smooth=True)
    # 생각 풍선
    th = empty('thought', (X + 1.15, -0.25, 2.45))
    white = flat_mat('cloud_m', '#ffffff')
    for (x, z, r) in [(0, 0, .42), (-.38, -.05, .3), (.38, -.05, .3), (-.2, .25, .3), (.22, .25, .32), (0, -.2, .3)]:
        prim('sphere', 'cloud', (x, 0.1, z), (r, 0.12, r), m=white, parent=th, smooth=True, seg=20, rings=10)
    prim('sphere', 'cloud_s1', (-0.55, 0.1, -0.5), (0.07, 0.05, 0.07), m=white, parent=th, smooth=True)
    prim('sphere', 'cloud_s2', (-0.72, 0.1, -0.68), (0.045, 0.03, 0.045), m=white, parent=th, smooth=True)
    th['base_scale'] = [1, 1, 1]
    icons = []
    for i, lbl in enumerate(L['menuIdeas']):
        g = empty('menu%d' % i, (0, -0.1, 0.08), th)
        if i == 0:
            prim('cyl', 'pot', (0, 0, 0), (0.2, 0.2, 0.14), m=mat('pot', '#6b4a36', .5), parent=g, verts=24)
            prim('cyl', 'stew', (0, 0, 0.071), (0.18, 0.18, 0.005), m=mat('stew', '#d9763c', .4), parent=g, verts=24)
            veg('potato', (-0.06, 0, 0.08), 0.8, g)
            veg('lettuce', (0.07, 0, 0.08), 0.4, g)
        elif i == 1:
            prim('sphere', 'bowl', (0, 0, 0.02), (0.22, 0.22, 0.12), m=mat('dish', '#fdfaf2', .3), parent=g, smooth=True)
            veg('lettuce', (-0.06, 0, 0.12), 0.6, g)
            veg('tomato', (0.08, -0.02, 0.13), 0.8, g)
            veg('carrot', (0, -0.05, 0.14), 0.5, g, rot=(0, 0, 60))
        else:
            prim('cyl', 'plate', (0, 0, 0), (0.24, 0.24, 0.02), m=mat('dish', '#fdfaf2', .3), parent=g, verts=24)
            prim('sphere', 'egg', (-0.05, 0, 0.03), (0.12, 0.1, 0.03), m=mat('egg', '#f6d34a', .5), parent=g, smooth=True)
            veg('tomato', (0.08, -0.03, 0.05), 0.7, g)
            veg('tomato', (0.02, 0.06, 0.05), 0.6, g)
        g.rotation_euler = (rad(70), 0, 0)
        text('menu_t%d' % i, lbl, 0.1, (0, -0.02, -0.27), (90, 0, 0), m=flat_mat('menu_tm%d' % i, '#6b4a36'), parent=g)
        g['base_scale'] = [1, 1, 1]
        icons.append(g)
    return dict(city=city, thought=th, icons=icons, sun=sun)


def building_mat(name, wall):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.offset = 0
    br.squash = 1
    br.inputs['Color1'].default_value = srgb('#ffe3a0')
    br.inputs['Color2'].default_value = srgb('#ffd98a')
    br.inputs['Mortar'].default_value = srgb(wall)
    br.inputs['Scale'].default_value = 0.6
    br.inputs['Mortar Size'].default_value = 0.35
    br.inputs['Brick Width'].default_value = 1.2
    br.inputs['Row Height'].default_value = 1.4
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    inv = nt.nodes.new('ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs['Fac'], inv.inputs[1])
    ec = b.inputs['Emission Color'] if 'Emission Color' in b.inputs else b.inputs['Emission']
    nt.links.new(br.outputs['Color'], ec)
    nt.links.new(inv.outputs[0], b.inputs['Emission Strength'])
    b.inputs['Roughness'].default_value = 0.9
    return m


# ---------- E. 저녁 식탁 ----------
def build_dining():
    X = SET_X['dining']
    prim('plane', 'din_floor', (X, 0, 0), (20, 20, 1), m=mat('din_floor', '#b98a5a', .7))
    prim('plane', 'din_wall', (X, 2.2, 3), (20, 6, 1), rot=(90, 0, 0), m=mat('din_wall', '#f3d6ab', .9))
    # 창문 (밤하늘)
    prim('plane', 'window', (X - 2.3, 2.18, 2.0), (1.4, 1.5, 1), rot=(90, 0, 0), m=mat('night', '#2f3f73', emit=1.0))
    fr = mat('frame', '#c79a6a', .8)
    for (dx, dz, sx, sz) in [(0, 0.78, 1.55, 0.08), (0, -0.78, 1.55, 0.08), (-0.74, 0, 0.08, 1.6), (0.74, 0, 0.08, 1.6), (0, 0, 0.05, 1.5), (0, 0, 1.4, 0.05)]:
        prim('cube', 'wframe', (X - 2.3 + dx, 2.15, 2.0 + dz), (sx, 0.05, sz), m=fr)
    prim('cyl', 'moon', (X - 2.0, 2.16, 2.45), (0.14, 0.14, 0.01), rot=(90, 0, 0), m=mat('moon', '#fff4c8', emit=2.5), verts=24)
    rnd = random.Random(2)
    for i in range(10):
        prim('sphere', 'star', (X - 2.3 + rnd.uniform(-.6, .6), 2.16, 2.0 + rnd.uniform(-.6, .6)), (0.012, 0.012, 0.012), m=mat('star', '#ffffff', emit=3), seg=6, rings=4)
    prim('cube', 'curtain', (X - 3.15, 2.1, 2.0), (0.35, 0.06, 1.9), m=mat('curtain', '#e98a6b', .9))
    # 액자
    prim('cube', 'pframe', (X + 2.3, 2.17, 2.2), (0.9, 0.04, 0.65), m=fr)
    prim('cube', 'pinner', (X + 2.3, 2.14, 2.2), (0.78, 0.02, 0.53), m=mat('paper', '#fff8e8'))
    for i, k in enumerate(['tomato', 'carrot', 'cabbage']):
        veg(k, (X + 2.05 + i * 0.25, 2.1, 2.2), 1.0, rot=(0, 0, 0))
    # 조명
    prim('cyl', 'dcord', (X, 0.4, 2.9), (0.01, 0.01, 1.3), m=mat('cord', '#5a4a3a'))
    prim('cone', 'dshade', (X, 0.4, 2.2), (0.35, 0.35, 0.28), m=mat('shade', '#e7b24c', .5), verts=20)
    prim('sphere', 'dbulb', (X, 0.4, 2.05), (0.08, 0.08, 0.08), m=mat('bulb', '#fff4c8', emit=5))
    l = bpy.data.lights.new('dinner_lamp', 'POINT')
    l.energy = 280
    l.color = (1.0, 0.8, 0.55)
    l.shadow_soft_size = 0.3
    lo = bpy.data.objects.new('dinner_lamp', l)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(lo)
    lo.location = (X, 0.4, 1.95)
    al = bpy.data.lights.new('din_fill', 'AREA')
    al.energy = 250
    al.size = 5
    al.color = (1.0, 0.85, 0.7)
    ao = bpy.data.objects.new('din_fill', al)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(ao)
    ao.location = (X, -4, 3)
    ao.rotation_euler = (rad(60), 0, 0)
    # 의자
    for x in (-0.85, 0, 0.85):
        prim('cube', 'chair', (X + x, 1.45, 0.65), (0.55, 0.08, 1.3), m=mat('chair', '#9c6a40', .8), bevel=0.04)
    # 식탁
    prim('cube', 'dtable', (X, 0.3, 0.38), (2.9, 1.2, 0.76), m=mat('dtable', '#a86d3a', .8))
    prim('cube', 'dcloth', (X, 0.3, 0.765), (2.2, 1.22, 0.02), m=mat('cloth', '#f4efe3', .9))
    prim('cube', 'dcloth_front', (X, -0.31, 0.6), (2.2, 0.01, 0.35), m=mat('cloth', '#f4efe3', .9))
    prim('cube', 'dcloth_stripe', (X, -0.318, 0.7), (2.2, 0.005, 0.03), m=mat('stripe', '#e98a6b'))
    dish = mat('dish', '#fdfaf2', .3)
    for x in (-0.85, 0.85, 0.0):
        y = 0.62 if x == 0 else 0.55
        prim('sphere', 'bowl', (X + x, y, 0.8), (0.1, 0.1, 0.06), m=dish, smooth=True)
        prim('cyl', 'rice', (X + x, y, 0.84), (0.085, 0.085, 0.015), m=mat('rice', '#ffffff', .6), verts=16)
    prim('cyl', 'dpot', (X, 0.08, 0.84), (0.2, 0.2, 0.14), m=mat('pot', '#6b4a36', .5), verts=24)
    prim('cyl', 'dstew', (X, 0.08, 0.912), (0.18, 0.18, 0.005), m=mat('stew', '#d9763c', .4), verts=24)
    veg('potato', (X - 0.06, 0.06, 0.93), 0.8)
    veg('cabbage', (X + 0.07, 0.1, 0.93), 0.4)
    for x, ks in ((-0.45, ['lettuce', 'tomato', 'tomato']), (0.45, ['corn', 'potato'])):
        prim('cyl', 'dplate', (X + x, 0.05, 0.79), (0.2, 0.2, 0.015), m=dish, verts=24)
        for j, k in enumerate(ks):
            veg(k, (X + x - 0.07 + j * 0.08, 0.05, 0.83), 0.7)
    steam = []
    sm = mat('steam', '#ffffff', emit=0.3, alpha=0.35)
    for i in range(3):
        steam.append(prim('sphere', 'steam', (X - 0.05 + i * 0.05, 0.08, 1.0), (0.05, 0.05, 0.08), m=sm, smooth=True, seg=12, rings=8))
    return dict(steam=steam)


# ---------- F. 엔딩 ----------
def build_end(L):
    X = SET_X['end']
    bg = bpy.data.materials.new('end_bg')
    bg.use_nodes = True
    nt = bg.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (2, 2, 2)
    gr = nt.nodes.new('ShaderNodeTexGradient')
    gr.gradient_type = 'SPHERICAL'
    mix = nt.nodes.new('ShaderNodeMixRGB')
    mix.inputs['Color1'].default_value = srgb('#f3e3bd')
    mix.inputs['Color2'].default_value = srgb('#fffaf0')
    em = nt.nodes.new('ShaderNodeEmission')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], gr.inputs['Vector'])
    nt.links.new(gr.outputs['Fac'], mix.inputs['Fac'])
    nt.links.new(mix.outputs[0], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs[0])
    prim('plane', 'end_backdrop', (X, 3, 1.8), (22, 13, 1), rot=(90, 0, 0), m=bg)
    prim('plane', 'end_floor', (X, 0, -0.95), (22, 8, 1), m=mat('end_floor', '#f1e2bf', .9))
    l1 = text('slogan1', L['sloganLines'][0], 0.78, (X, 0, 2.85), (90, 0, 0), m=flat_mat('slogan_g', '#2f6b3a'), extrude=0.02)
    l2 = text('slogan2', L['sloganLines'][1], 0.78, (X, 0, 1.85), (90, 0, 0), m=flat_mat('slogan_o', '#d9692f'), extrude=0.02)
    store = empty('end_store', (X, 0, 1.0))
    text('end_store_t', L['storeName'], 0.4, (0, 0, 0), (90, 0, 0), m=flat_mat('end_store_m', '#4a3b2c'), parent=store)
    lm = flat_mat('line_m', '#b9a684')
    prim('cube', 'end_line', (-2.75, 0, 0), (0.9, 0.01, 0.025), m=lm, parent=store)
    prim('cube', 'end_line', (2.75, 0, 0), (0.9, 0.01, 0.025), m=lm, parent=store)
    prim('sphere', 'end_leaf', (-2.15, -0.02, 0.12), (0.06, 0.01, 0.12), rot=(0, -40, 0), m=flat_mat('leaf_f', '#5fae4c'), parent=store)
    store['base_scale'] = [1, 1, 1]
    chips = []
    themes = ['#' + t.replace(' ', '') for t in L['themes']]
    widths = [0.35 + len(t) * 0.27 for t in themes]
    gap = 0.2
    total = sum(widths) + gap * (len(themes) - 1)
    cx = X - total / 2
    for i, t in enumerate(themes):
        w = widths[i]
        g = empty('chip%d' % i, (cx + w / 2, -0.1, 0.25))
        prim('cube', 'chip_bg', (0, 0.02, 0), (w, 0.03, 0.42), m=flat_mat('chip_bgm', '#ffffff'), parent=g, bevel=0.2)
        prim('cube', 'chip_bd', (0, 0.04, 0), (w + 0.05, 0.02, 0.47), m=flat_mat('chip_bdm', '#9cc98a'), parent=g, bevel=0.22)
        text('chip_t%d' % i, t, 0.24, (0, -0.005, 0), (90, 0, 0), m=flat_mat('chip_tm', '#3f7d4c'), parent=g)
        g['base_scale'] = [1, 1, 1]
        chips.append(g)
        cx += w + gap
    row = ['cabbage', 'carrot', 'tomato', 'corn', 'potato', 'lettuce', 'tomato', 'eggplant', 'carrot', 'cabbage', 'tomato', 'corn', 'lettuce']
    vs = []
    for i, k in enumerate(row):
        x = X - 4.2 + i * 0.7
        z = -0.55 + 0.22 * math.sin(math.pi * i / (len(row) - 1))
        vs.append(veg(k, (x, -0.6, z), 2.4, rot=(10, 0, (i * 37) % 50 - 25)))
    al = bpy.data.lights.new('end_light', 'AREA')
    al.energy = 600
    al.size = 8
    ao = bpy.data.objects.new('end_light', al)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(ao)
    ao.location = (X, -6, 4)
    ao.rotation_euler = (rad(55), 0, 0)
    return dict(l1=l1, l2=l2, store=store, chips=chips, vegs=vs)

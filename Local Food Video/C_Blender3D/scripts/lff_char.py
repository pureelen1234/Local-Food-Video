"""임시 3D 캐릭터 (기본 도형 조립).
- 루트 Empty 이름이 CH_Farmer / CH_Staff / CH_Consumer 이므로,
  나중에 실제 캐릭터(MetaHuman 대체 에셋, Mixamo 등)로 바꿀 때 루트만 교체하면 된다.
- 정면은 -Y 방향.
"""
from lff_core import prim, empty, mat, curve, key, rad, lerp

SPECS = {
    'CH_Farmer': dict(skin='#d9a27c', hair='#8a8178', shirt='#7aa0c8', fore='#d9a27c', pants='#6b5b45', shoe='#4a3b2c',
                      hat=True, towel=True),
    'CH_Staff': dict(skin='#f1c6a3', hair='#3a2a20', shirt='#f6f2e8', fore='#f1c6a3', pants='#5b5046', shoe='#3b302a',
                     apron='#3f8f5a', bun=True),
    'CH_Consumer': dict(skin='#f4cdb0', hair='#2e2019', shirt='#d9587a', fore='#f4cdb0', pants='#3f4a63', shoe='#2d2a33',
                        ponytail=True, bag=True),
    'CH_Family': dict(skin='#efc3a0', hair='#2a2420', shirt='#7c9b6d', fore='#efc3a0', pants='#4a4a52', shoe='#333333'),
    'CH_Child': dict(skin='#f6d2b6', hair='#3a2a20', shirt='#f2c14e', fore='#f6d2b6', pants='#6a7fa8', shoe='#c0504d',
                     bob=True, scale=0.68),
}
CHARS = {}


def build(name, loc=(0, 0, 0), rotz=0):
    sp = SPECS[name]
    n = name
    M = lambda k, c, r=0.7: mat(n + '_' + k, c, r)
    skin, hair, shirt = M('skin', sp['skin']), M('hair', sp['hair'], .8), M('shirt', sp['shirt'])
    fore, pants, shoe = M('fore', sp['fore']), M('pants', sp['pants']), M('shoe', sp['shoe'], .5)
    dark = mat('eye_dark', '#2b211c', .3)
    lip = mat('lip', '#b84a40', .5)
    blush = mat('blush', '#f08c7e', .9)

    root = empty(n, loc)
    root.rotation_euler = (0, 0, rad(rotz))
    s = sp.get('scale', 0.93)
    root.scale = (s, s, s)
    root['base_scale'] = [s, s, s]
    pelvis = empty(n + '_pelvis', (0, 0, 0.92), root)
    spine = empty(n + '_spine', (0, 0, 0.92), root)
    # 몸통
    prim('sphere', n + '_torso', (0, 0, 0.3), (0.2, 0.135, 0.34), m=shirt, parent=spine, smooth=True)
    prim('sphere', n + '_waist', (0, 0, 0.02), (0.185, 0.13, 0.13), m=pants, parent=spine, smooth=True)
    prim('cyl', n + '_neck', (0, 0, 0.64), (0.05, 0.05, 0.1), m=skin, parent=spine)
    # 머리
    head = empty(n + '_head', (0, 0, 0.67), spine)
    prim('sphere', n + '_skull', (0, 0, 0.14), (0.14, 0.135, 0.147), m=skin, parent=head, smooth=True)
    prim('sphere', n + '_hair', (0, 0.03, 0.19), (0.15, 0.157, 0.128), m=hair, parent=head, smooth=True)
    for sx in (1, -1):
        prim('sphere', n + '_ear', (sx * 0.138, 0.01, 0.14), (0.028, 0.02, 0.036), m=skin, parent=head, smooth=True)
        e = prim('sphere', n + '_eye', (sx * 0.05, -0.127, 0.155), (0.017, 0.012, 0.022), m=dark, parent=head, smooth=True, seg=12, rings=8)
        e.name = n + ('_eyeL' if sx > 0 else '_eyeR')
        prim('cube', n + '_brow', (sx * 0.05, -0.128, 0.198), (0.04, 0.01, 0.009), rot=(0, sx * -6, 0), m=hair, parent=head)
        prim('sphere', n + '_blush', (sx * 0.083, -0.112, 0.11), (0.025, 0.008, 0.016), rot=(0, 0, sx * -35), m=blush, parent=head, smooth=True, seg=12, rings=6)
    prim('sphere', n + '_nose', (0, -0.142, 0.125), (0.018, 0.018, 0.02), m=skin, parent=head, smooth=True, seg=12, rings=8)
    mouth = empty(n + '_mouth', (0, -0.136, 0.085), head)
    curve(n + '_lips', [(-0.036, 0, 0.004), (0, -0.004, -0.016), (0.036, 0, 0.004)], 0.0055, lip, mouth)
    # 머리 장식
    if sp.get('hat'):
        hm, bm = mat('straw', '#e2c070', .8), mat('hatband', '#a4553d')
        prim('cyl', n + '_brim', (0, 0, 0.25), (0.27, 0.27, 0.014), m=hm, parent=head, verts=32)
        prim('cyl', n + '_crown', (0, 0, 0.315), (0.14, 0.14, 0.12), m=hm, parent=head, verts=24)
        prim('cyl', n + '_band', (0, 0, 0.275), (0.143, 0.143, 0.03), m=bm, parent=head, verts=24)
    if sp.get('bun'):
        prim('sphere', n + '_bun', (0, 0.1, 0.29), (0.07, 0.07, 0.07), m=hair, parent=head, smooth=True)
    if sp.get('bob'):
        prim('sphere', n + '_bobhair', (0, 0.035, 0.13), (0.158, 0.15, 0.16), m=hair, parent=head, smooth=True)
    if sp.get('ponytail'):
        tail = empty(n + '_tail', (0, 0.12, 0.23), head)
        prim('sphere', n + '_tailhair', (0, 0.04, -0.12), (0.05, 0.05, 0.14), m=hair, parent=tail, smooth=True)
    if sp.get('towel'):
        tm = mat('towel', '#f6f4ea', .9)
        prim('torus', n + '_towel', (0, 0, 0.6), (0.12, 0.1, 0.12), m=tm, parent=spine, minor=0.28)
        prim('cube', n + '_towelend', (0.08, -0.125, 0.45), (0.07, 0.02, 0.24), m=tm, parent=spine)
    if sp.get('apron'):
        am = mat(n + '_apron', sp['apron'])
        prim('cube', n + '_apronbody', (0, -0.137, 0.12), (0.34, 0.02, 0.62), m=am, parent=spine, bevel=0.02)
        prim('cube', n + '_pocket', (0, -0.15, 0.08), (0.18, 0.012, 0.1), m=mat(n + '_apron2', '#357a4c'), parent=spine)
        prim('cube', n + '_badge', (0.1, -0.15, 0.38), (0.07, 0.01, 0.035), m=mat('badge', '#fffbef'), parent=spine)
    if sp.get('bag'):
        bgm = mat('ecobag', '#eadcbf', .9)
        prim('cube', n + '_bag', (0.27, 0.03, -0.06), (0.07, 0.25, 0.3), m=bgm, parent=spine, bevel=0.02)
        prim('sphere', n + '_bagleaf', (0.31, 0.03, -0.04), (0.005, 0.06, 0.035), rot=(35, 0, 0), m=mat('leaf', '#6fae5a'), parent=spine)
        prim('cube', n + '_strap', (0.12, -0.02, 0.29), (0.025, 0.02, 0.62), rot=(0, 28, 0), m=mat('strap', '#c7ab80'), parent=spine)
    # 팔
    for side, sx in (('L', 1), ('R', -1)):
        sh = empty(n + '_sh' + side, (sx * 0.215, 0, 0.5), spine)
        prim('sphere', n + '_shoulder' + side, (0, 0, 0), (0.06, 0.06, 0.06), m=shirt, parent=sh, smooth=True, seg=16, rings=8)
        prim('cyl', n + '_upper' + side, (0, 0, -0.15), (0.052, 0.052, 0.3), m=shirt, parent=sh, verts=14)
        el = empty(n + '_el' + side, (0, 0, -0.3), sh)
        prim('cyl', n + '_fore' + side, (0, 0, -0.135), (0.045, 0.045, 0.27), m=fore, parent=el, verts=14)
        prim('sphere', n + '_handm' + side, (0, 0, -0.3), (0.052, 0.052, 0.055), m=skin, parent=el, smooth=True, seg=14, rings=8)
        empty(n + '_hand' + side, (0, -0.02, -0.34), el)
    # 다리
    for side, sx in (('L', 1), ('R', -1)):
        lg = empty(n + '_leg' + side, (sx * 0.095, 0, 0), pelvis)
        prim('cyl', n + '_thigh' + side, (0, 0, -0.43), (0.068, 0.068, 0.86), m=pants, parent=lg, verts=14)
        prim('sphere', n + '_shoe' + side, (0, -0.05, -0.885), (0.075, 0.135, 0.05), m=shoe, parent=lg, smooth=True, seg=16, rings=8)
    CHARS[name] = root
    return root


def part(name, p):
    import bpy
    return bpy.data.objects[name + '_' + p]


def pose(name, f, armL=None, armR=None, legL=None, legR=None, bend=None, head=None, turn=None,
         smile=None, squint=None, loc=None, rotz=None, tail=None, tilt=None):
    """팔 (앞으로 든 각도, 옆으로 벌린 각도, 팔꿈치 굽힘), 다리 앞뒤 각도, 몸 숙임, 고개 끄덕임/돌림, 미소 0~1."""
    import bpy
    O = bpy.data.objects
    for side, sx, a in (('L', 1, armL), ('R', -1, armR)):
        if a is not None:
            fwd, out, elb = a
            key(O[name + '_sh' + side], 'rotation_euler', f, (rad(-fwd), rad(-out * sx), 0))
            key(O[name + '_el' + side], 'rotation_euler', f, (rad(-elb), 0, 0))
    for side, a in (('L', legL), ('R', legR)):
        if a is not None:
            key(O[name + '_leg' + side], 'rotation_euler', f, (rad(-a), 0, 0))
    if bend is not None or tilt is not None:
        key(O[name + '_spine'], 'rotation_euler', f, (rad(-(bend or 0)), rad(tilt or 0), 0))
    if head is not None or turn is not None:
        key(O[name + '_head'], 'rotation_euler', f, (rad(-(head or 0)), 0, rad(turn or 0)))
    if smile is not None:
        key(O[name + '_mouth'], 'scale', f, (lerp(0.85, 1.2, smile), 1, lerp(0.35, 1.9, smile)))
    if squint is not None:
        for e in ('_eyeL', '_eyeR'):
            key(O[name + e], 'scale', f, (0.017, 0.012, lerp(0.022, 0.006, squint)))
    if loc is not None:
        key(O[name], 'location', f, loc)
    if rotz is not None:
        key(O[name], 'rotation_euler', f, (0, 0, rad(rotz)))
    if tail is not None and (name + '_tail') in O:
        key(O[name + '_tail'], 'rotation_euler', f, (rad(tail), 0, 0))


def rest(name, f, **kw):
    base = dict(armL=(0, 6, 8), armR=(0, 6, 8), legL=0, legR=0, bend=0, head=0, turn=0)
    base.update(kw)
    pose(name, f, **base)


def walk(name, f0, f1, period=24, amp=24, bob=0.03, base_loc=None):
    """제자리 걷기 (배경이 움직이는 방식)."""
    import bpy
    root = bpy.data.objects[name]
    L = list(base_loc or root.location)
    q = period // 4
    i = 0
    for f in range(f0, f1 + 1, q):
        ph = i % 4
        sw = (0, 1, 0, -1)[ph]
        pose(name, f, legL=amp * sw, legR=-amp * sw, armL=(-amp * .8 * sw, 6, 14), armR=(amp * .8 * sw, 6, 14),
             loc=(L[0], L[1], L[2] + (bob if sw == 0 else 0)), tail=8 * sw)
        i += 1


def hold(name, f):
    """장면 경계에서 현재 자세를 고정 (다음 장면 키와 섞이지 않게)."""
    import bpy
    for o in bpy.data.objects:
        if not (o.name == name or o.name.startswith(name + '_')):
            continue
        ad = o.animation_data
        if not ad or not ad.action:
            continue
        for fc in ad.action.fcurves:
            fc.keyframe_points.insert(f, fc.evaluate(f))

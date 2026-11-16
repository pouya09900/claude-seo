"""
Parametric rose with fully SEPARATE petals  --  Blender 5.x   (v2)
Run: Scripting tab > Open > rose_petals.py > Run Script (Alt+P)

Structure (inside to outside):
  - center bud + inner petals  : golden-angle spiral (natural)
  - two outer rings of 8 petals: evenly spaced, tidy and round
Every petal is its own object, inside collection "Rose", parented to "Rose_Root".
Petal thickness: thick at the base, thin at the tip (vertex group + Solidify).
"""
import bpy
import bmesh
import math
import random

# ============================ PARAMETERS ============================
INNER_PETALS = 14      # petals of the spiral center
RING_COUNT   = 8       # petals per outer ring (2 rings are built)
SEED         = 7       # different seed = different organic variation
SIZE         = 1.0     # overall scale
RES_U        = 30      # resolution along petal length
RES_V        = 26      # resolution across petal width

CUP          = 1.0     # outer petals: 1 = default bowl shape, >1 = tighter/closed, <1 = more open
LIP          = 1.0     # how much the petal tips curl back outward
RUFFLE       = 1.0     # wavy rim strength (0 = smooth rim)
ORGANIC      = 1.0     # bumps / dents / center groove strength (0 = smooth)
ORDER        = 1.0     # 1 = outer rings perfectly tidy, 0 = a bit irregular

THICK_BASE   = 1.0     # thickness at the petal base (multiplier)
THICK_TIP    = 0.12    # tip thickness as a fraction of base thickness (0.05 = very thin)
SUBSURF      = True
BASE_COLOR   = (0.42, 0.42, 0.42, 1.0)   # e.g. (0.35, 0.02, 0.05, 1) = burgundy
ROUGHNESS    = 0.6
GOLDEN_ANGLE = math.radians(137.508)
# ====================================================================


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def shape_from_t(t):
    """Common shape curve: t=0 center bud ... t=1 outermost petals."""
    return {
        "t": t,
        "r0": 0.04 + 0.34 * t ** 1.1,
        "z0": 0.55 * (1.0 - t) ** 1.2 + 0.10 * (1.0 - t),
        "L": lerp(0.42, 0.88, t ** 0.9),
        "a0": math.radians(lerp(0.0, 10.0 * CUP, t ** 1.1)),
        "a1": math.radians(lerp(-7.0, 46.0 / max(CUP, 0.3), t ** 1.3)),
        "span": math.radians(lerp(215.0, 82.0, t ** 0.8)),
        "roll": math.radians(lerp(3.0, 30.0, t) * LIP),
        "lip": math.radians(lerp(0.0, 24.0, t ** 1.5) * LIP),
        "bump": lerp(0.004, 0.013, t) * ORGANIC,
        "rim": lerp(0.004, 0.020, t) * RUFFLE,
        "ruf": lerp(0.015, 0.060, t) * RUFFLE,
        "thick": lerp(0.008, 0.016, t) * THICK_BASE,
    }


def add_random(p, rnd, tidy):
    k = 1.0 - ORDER * tidy          # 0 = no randomness
    p["ph1"] = rnd.uniform(0, 6.28) * k
    p["ph2"] = rnd.uniform(0, 6.28)
    p["f1"] = lerp(rnd.uniform(3.5, 5.5), 4.5, tidy * ORDER)
    p["f2"] = lerp(rnd.uniform(7.0, 10.0), 9.0, tidy * ORDER)
    p["w2"] = lerp(0.4, 0.15, tidy * ORDER)          # weight of irregular wave
    for n in (3, 4, 5, 6):
        p[f"ph{n}"] = rnd.uniform(0, 6.28)
    p["jit_a"] = rnd.uniform(-1.0, 1.0) * k
    return p


def all_petal_params(rnd):
    petals = []
    # --- inner spiral (golden angle) ---
    for i in range(INNER_PETALS):
        t = 0.62 * i / max(1, INNER_PETALS - 1)
        p = add_random(shape_from_t(t), rnd, tidy=0.0)
        p["phi"] = i * GOLDEN_ANGLE + rnd.uniform(-0.08, 0.08)
        p["L"] *= rnd.uniform(0.97, 1.04)
        p["a0"] += math.radians(rnd.uniform(-1.5, 1.5))
        p["a1"] += math.radians(rnd.uniform(-2.0, 2.0))
        petals.append(p)
    # --- two tidy outer rings ---
    for ring, (t, offset) in enumerate(((0.78, 0.5), (1.0, 0.0))):
        for k in range(RING_COUNT):
            p = add_random(shape_from_t(t), rnd, tidy=1.0)
            p["phi"] = (k + offset) * 2.0 * math.pi / RING_COUNT + 0.3 * ring
            p["span"] += math.radians(9.0)
            # alternate petals sit on two tiers so neighbours never collide
            p["r0"] += 0.028 * (k % 2)
            p["z0"] += 0.015 * (k % 2)
            p["a1"] += math.radians(2.0 * (k % 2)) * 0  # keep identical flare
            p["L"] *= 1.0 + (0.02 * (k % 2)) * (1.0 - ORDER) + 0.0
            petals.append(p)
    return petals


def build_petal_geometry(p, nu=RES_U, nv=RES_V):
    """Returns (verts, faces, weights). Pure math, no bpy."""
    L = p["L"]
    cols = []
    wts = []
    for j in range(nv + 1):
        v = -1.0 + 2.0 * j / nv
        av = abs(v)
        wave = (math.sin(v * p["f1"] + p["ph1"]) * (1.0 - p["w2"])
                + math.sin(v * p["f2"] + p["ph2"]) * p["w2"])
        # round outline: wide rounded top, shorter at the sides
        s_max = L * math.sqrt(max(0.0, 1.0 - 0.72 * av ** 2.5)) * (1.0 + p["ruf"] * wave)
        ds = s_max / nu

        def ang(wm):
            return (p["a0"] + (p["a1"] - p["a0"]) * min(wm, 1.2) ** 1.6
                    + p["roll"] * av ** 2 * wm ** 3
                    + p["lip"] * smoothstep(0.75, 1.0, wm))

        r_int = 0.0
        z = p["z0"]
        col = []
        wcol = []
        for i in range(nu + 1):
            s = i * ds
            w = s / L
            if i > 0:
                wm = (s - 0.5 * ds) / L
                a = ang(wm)
                r_int += math.sin(a) * ds
                z += math.cos(a) * ds
            a_here = ang(w)

            pinch = 0.4 + 0.6 * smoothstep(0.0, 0.5, w)
            r = p["r0"] * pinch + r_int
            zz = z

            # organic surface: bumps, dents, center groove, rim ripples
            b = (0.6 * math.sin(2.2 * v + 3.0 * w + p["ph3"]) * math.sin(3.4 * w + p["ph4"])
                 + 0.4 * math.sin(4.3 * v + p["ph5"]) * math.sin(2.1 * w + p["ph6"]))
            groove = -0.7 * math.exp(-(v / 0.4) ** 2) * smoothstep(0.15, 0.8, w)
            d = (p["bump"] * (b * smoothstep(0.1, 0.45, w) + 0.6 * groove)
                 + p["rim"] * wave * smoothstep(0.65, 1.0, w))
            r += d * math.cos(a_here)
            zz -= d * math.sin(a_here)
            r = max(r, 0.005)

            bw = 0.55 + 0.45 * smoothstep(0.0, 0.45, w)
            theta = p["phi"] + v * 0.5 * p["span"] * bw
            col.append((r * math.cos(theta) * SIZE,
                        r * math.sin(theta) * SIZE,
                        zz * SIZE))
            wcol.append((1.0 - i / nu) ** 1.2)     # 1 at base -> 0 at tip
        cols.append(col)
        wts.append(wcol)

    flat, weights, index = [], [], {}
    for j in range(nv + 1):
        for i in range(nu + 1):
            index[(i, j)] = len(flat)
            flat.append(cols[j][i])
            weights.append(wts[j][i])

    faces = []
    for j in range(nv):
        for i in range(nu):
            faces.append((index[(i, j)], index[(i, j + 1)],
                          index[(i + 1, j + 1)], index[(i + 1, j)]))
    return flat, faces, weights


def make_material():
    mat = bpy.data.materials.get("Rose_Material")
    if mat is None:
        mat = bpy.data.materials.new("Rose_Material")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = BASE_COLOR
    bsdf.inputs["Roughness"].default_value = ROUGHNESS
    return mat


def main():
    rnd = random.Random(SEED)

    old = bpy.data.collections.get("Rose")
    if old:
        for ob in list(old.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(old)

    col = bpy.data.collections.new("Rose")
    bpy.context.scene.collection.children.link(col)
    root = bpy.data.objects.new("Rose_Root", None)
    col.objects.link(root)
    mat = make_material()

    params = all_petal_params(rnd)
    for i, p in enumerate(params):
        verts, faces, weights = build_petal_geometry(p)

        name = f"Petal_{i:03d}"
        mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmverts = [bm.verts.new(v) for v in verts]
        for f in faces:
            face = bm.faces.new([bmverts[k] for k in f])
            face.smooth = True
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(mat)

        ob = bpy.data.objects.new(name, mesh)
        col.objects.link(ob)
        ob.parent = root

        vg = ob.vertex_groups.new(name="Thickness")
        for idx, wgt in enumerate(weights):
            vg.add([idx], wgt, 'REPLACE')

        sol = ob.modifiers.new("Thickness", 'SOLIDIFY')
        sol.thickness = p["thick"] * SIZE
        sol.offset = 0.0
        sol.vertex_group = "Thickness"
        sol.thickness_vertex_group = THICK_TIP     # factor used where weight = 0 (tip)
        if SUBSURF:
            sub = ob.modifiers.new("Smooth", 'SUBSURF')
            sub.levels = 1
            sub.render_levels = 2

    print(f"Rose built: {len(params)} separate petals")


if __name__ == "__main__":
    main()

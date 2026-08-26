#!/usr/bin/env python3
"""
C6：穹顶 + 鼓座圆柱 + 基座环梁（战役三，2026-08-17）

几何：
  1. 穹顶：旋转母线变厚度（z≥0，内面 R=22.03 / 外面厚 1.5→5.9m），Oculus 开孔
  2. 鼓座：空心圆柱 r∈[22.03,27.93]，z∈[-H_DRUM, 0]（简化为纯圆柱、无壁龛，项目决策）
  3. 基座：环梁 r∈[22.03,32.03]，z∈[-H_DRUM-BASE_T, -H_DRUM]
  4. dome+drum+base 三件 fuse 成共形单体积，材料按区域(z/r)在求解时 callable 赋

物理（求解另见 c6_solver）：自重分层 + 干缩热类比；基座底面(组400)全固支（地面）。
  关键：干缩时鼓座弹性约束不同于「拱脚全固支」——检验鼓座是否为 57° 的缺口之一。

尺寸（项目决策：无详细数据，用推定值，⚠️ 待测绘核实）：
  DRUM_IN=22.03, DRUM_OUT=27.93, H_DRUM=21.7  m
  BASE_OUT=32.03（环宽 ~10m）, BASE_T=4.5     m

用法（WSL）：
  python geometry/c6_drum_base.py --out c6_drum_base.msh

2026-08-17 写：战役三首版。
"""
import sys
import argparse
from pathlib import Path

import numpy as np
import gmsh

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import (
    R_INNER, T_BASE, T_OCULUS, D_OCULUS, MESH_DIR,
    COFFER_LAYERS, COFFER_SECTORS, COFFER_GEOMETRY, COFFER_STEPS,
)

# 推定尺寸（⚠️ 待核实；项目批准用估计值）
DRUM_IN = R_INNER            # 22.03
DRUM_OUT = R_INNER + T_BASE  # 27.93（与穹底外表面连续）
H_DRUM = 21.7                # 鼓座高（spring 线 0 到地面）推定
BASE_OUT = 32.03             # 基座外径（环宽 ~10m）
BASE_T = 4.5                 # 基座厚（深）


def thickness(phi):
    phi_o = np.arcsin(D_OCULUS / (2 * R_INNER))
    return T_OCULUS + (T_BASE - T_OCULUS) * (phi - phi_o) / (np.pi / 2 - phi_o)


def build_dome():
    """旋转母线变厚度穹顶（z≥0）"""
    phi_o = np.arcsin(D_OCULUS / (2 * R_INNER))
    xAi, zAi = R_INNER * np.sin(phi_o), R_INNER * np.cos(phi_o)
    xBi, zBi = R_INNER, 0.0
    xBo = DRUM_OUT
    xAo = (R_INNER + thickness(phi_o)) * np.sin(phi_o)
    zAo = (R_INNER + thickness(phi_o)) * np.cos(phi_o)

    p_ai = gmsh.model.occ.addPoint(xAi, 0, zAi)
    p_bi = gmsh.model.occ.addPoint(xBi, 0, zBi)
    p_bo = gmsh.model.occ.addPoint(xBo, 0, 0)
    p_ao = gmsh.model.occ.addPoint(xAo, 0, zAo)
    p_c = gmsh.model.occ.addPoint(0, 0, 0)

    arc = gmsh.model.occ.addCircleArc(p_ai, p_c, p_bi)
    l_spring = gmsh.model.occ.addLine(p_bi, p_bo)
    phis = np.linspace(np.pi / 2, phi_o, 60)
    ot = [p_bo]
    for p in phis[1:-1]:
        r = R_INNER + thickness(p)
        ot.append(gmsh.model.occ.addPoint(r * np.sin(p), 0, r * np.cos(p)))
    ot.append(p_ao)
    ol = [gmsh.model.occ.addLine(ot[k], ot[k + 1]) for k in range(len(ot) - 1)]
    l_oculus = gmsh.model.occ.addLine(p_ao, p_ai)
    loop = gmsh.model.occ.addCurveLoop([arc, l_spring] + ol + [l_oculus])
    surf = gmsh.model.occ.addPlaneSurface([loop])
    gmsh.model.occ.synchronize()
    out = gmsh.model.occ.revolve([(2, surf)], 0, 0, 0, 0, 0, 1, 2 * np.pi)
    gmsh.model.occ.synchronize()
    for d, t in out:
        if d == 3:
            return t
    raise RuntimeError("穹顶失败")


def build_drum():
    """空心圆柱鼓座 r∈[DRUM_IN,DRUM_OUT], z∈[-H_DRUM,0]"""
    out = gmsh.model.occ.addCylinder(0, 0, -H_DRUM - 1, 0, 0, H_DRUM + 2, DRUM_OUT)
    inn = gmsh.model.occ.addCylinder(0, 0, -H_DRUM - 1, 0, 0, H_DRUM + 2, DRUM_IN)
    gmsh.model.occ.synchronize()
    res = gmsh.model.occ.cut([(3, out)], [(3, inn)], removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    for d, t in res[0]:
        if d == 3:
            return t
    raise RuntimeError("鼓座失败")


def build_base():
    """基座环梁 r∈[DRUM_IN,BASE_OUT], z∈[-H_DRUM-BASE_T,-H_DRUM]"""
    z0 = -H_DRUM - BASE_T
    out = gmsh.model.occ.addCylinder(0, 0, z0, 0, 0, BASE_T, BASE_OUT)
    inn = gmsh.model.occ.addCylinder(0, 0, z0 - 0.1, 0, 0, BASE_T + 0.2, DRUM_IN)
    gmsh.model.occ.synchronize()
    res = gmsh.model.occ.cut([(3, out)], [(3, inn)], removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    for d, t in res[0]:
        if d == 3:
            return t
    raise RuntimeError("基座失败")


def cut_oculus(dome_tag):
    phi_o = np.arcsin(D_OCULUS / (2 * R_INNER))
    z_o = R_INNER * np.cos(phi_o)
    cyl = gmsh.model.occ.addCylinder(0, 0, z_o - 1, 0, 0, 30, D_OCULUS / 2 + 2.0)
    gmsh.model.occ.synchronize()
    res = gmsh.model.occ.cut([(3, dome_tag)], [(3, cyl)], removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    for d, t in res[0]:
        if d == 3:
            return t
    raise RuntimeError("Oculus 切割失败")


# ---- C7：方形藻井（直边版，2026-08-17 从 c3 移植） ----
def phi_c_levels():
    phi_o = np.arcsin(D_OCULUS / (2 * R_INNER))
    return np.linspace(phi_o + np.radians(8), np.radians(78), COFFER_LAYERS)


def create_coffer(level, theta_c):
    w = COFFER_GEOMETRY[level][1]      # bottom_w
    h = COFFER_GEOMETRY[level][3]      # arc_h
    d = COFFER_STEPS[level][0]         # 首级阶梯深
    margin = 0.5
    phi_c = phi_c_levels()[level]

    box = gmsh.model.occ.addBox(-w / 2, -h / 2, -d / 2 - margin, w, h, d / 2 + margin)
    gmsh.model.occ.synchronize()
    gmsh.model.occ.rotate([(3, box)], 0, 0, 0, 0, 1, 0, np.degrees(phi_c))
    gmsh.model.occ.rotate([(3, box)], 0, 0, 0, 0, 0, 1, np.degrees(theta_c))
    gmsh.model.occ.synchronize()
    rc = R_INNER - d / 2
    x_c = rc * np.sin(phi_c) * np.cos(theta_c)
    y_c = rc * np.sin(phi_c) * np.sin(theta_c)
    z_c = rc * np.cos(phi_c)
    gmsh.model.occ.translate([(3, box)], x_c, y_c, z_c)
    gmsh.model.occ.synchronize()
    return box


def cut_all_coffers(dome_tag):
    """穹顶挖除 5×28 方形藻井，返回新 tag"""
    boxes = []
    for i in range(COFFER_LAYERS):
        for theta_c in np.linspace(0, 2 * np.pi, COFFER_SECTORS, endpoint=False):
            boxes.append((3, create_coffer(i, theta_c)))
    res = gmsh.model.occ.cut([(3, dome_tag)], boxes, removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    for d, t in res[0]:
        if d == 3:
            return t
    raise RuntimeError("藻井切割失败")


def mark_groups(body_tag):
    z_base = -H_DRUM - BASE_T          # 基座底面
    base = []
    for dim, tag in gmsh.model.getEntities(dim=2):
        bbox = gmsh.model.occ.getBoundingBox(dim, tag)
        if (bbox[5] - bbox[2]) < 0.01 and abs(bbox[2] - z_base) < 0.05:
            base.append(tag)            # 基座底面(z=z_base 平环) → 地面固支
    gmsh.model.addPhysicalGroup(2, base, tag=400, name="base_bottom")
    gmsh.model.addPhysicalGroup(3, [body_tag], tag=1000, name="body")
    print(f"物理组: 基座底面 {len(base)} / 体 1")


def main():
    parser = argparse.ArgumentParser(description="C6/C7 穹顶+鼓座+基座(+方形藻井)")
    parser.add_argument("--lc", type=float, default=2.0)
    parser.add_argument("--no-coffer", action="store_true", help="不挖藻井（纯 C6）")
    parser.add_argument("--linear2nd", action="store_true",
                        help="SecondOrderLinear=1（直边，保 0 倒转；C7 方形藻井用）")
    parser.add_argument("--out", default="c6_drum_base.msh")
    args = parser.parse_args()

    MESH_DIR.mkdir(parents=True, exist_ok=True)
    gmsh.initialize()
    gmsh.model.add("pantheon_c6")

    print("[1/5] 建穹顶...")
    dome = build_dome()
    print("[1.5/5] 切 Oculus...")
    dome = cut_oculus(dome)
    if not args.no_coffer:
        print("[1.8/5] 穹顶挖 140 方形藻井...")
        dome = cut_all_coffers(dome)
    print("[2/5] 建鼓座 + 基座...")
    drum = build_drum()
    base = build_base()

    print("[2.5/5] fuse 共形...")
    gmsh.model.occ.synchronize()
    fused = gmsh.model.occ.fuse([(3, dome)], [(3, drum), (3, base)])
    gmsh.model.occ.synchronize()
    body = None
    for d, t in fused[0]:
        if d == 3:
            body = t
    if body is None:
        for d, t in gmsh.model.getEntities(dim=3):
            body = t
    print("[3.5/5] 标记物理组...")
    mark_groups(body)

    print("[4/5] 撒网 + 导出...")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", args.lc)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    if args.linear2nd:
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.model.mesh.generate(3)
    out = MESH_DIR / args.out
    gmsh.write(str(out))
    gmsh.finalize()
    print(f"✅ 完成: {out}")


if __name__ == "__main__":
    main()

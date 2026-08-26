#!/usr/bin/env python3
"""
C3：变厚度穹顶 + 藻井几何（旋转母线法，文档4 §9.6 变厚度 + §11 藻井 + §13.3 28对称）

几何方案（2026-08-17 项目决策）：
  1. 母线（x-z 平面闭合多边形，内边=真圆弧 R_INNER、外边=变厚度折线 t(φ)=1.5→5.9m）
     绕 z 轴旋转扫角 → 变厚度穹顶。
  2. 圆柱切 Oculus 开口。
  3. 藻井盒（长方体近似，旋转+平移到内球面）批量挖除。
  4. 物理组：拱脚面 400 + 体 1000；--slice 时另贴两条子午切面 500/600（对称 BC 用）。

--slice 模式（2026-08-17 为完整曲边复核算例加）：
  母线只转 2π/28（1 个扇区），每层只放 1 个藻井（共 5 个 = 20 个再入角），
  完整曲边 + HighOrderOptimize 有望倒转清零——用于复核满圆周版 θ_top 是否虚高。

用法（WSL）：
  python geometry/c3_variable_coffer.py --no-coffer --out c3_nocoffer.msh
  python geometry/c3_variable_coffer.py --lc 1.5 --out c3_coffer.msh
  python geometry/c3_variable_coffer.py --lc 1.5 --slice --out c3_coffer_28.msh
  python geometry/c3_variable_coffer.py --lc 1.5 --slice --linear2nd --out c3_coffer_28_lin2.msh

2026-08-17 写：复杂几何战役。P-08 质量API/P-09 fillet/P-11 setSize 等坑见 commit 记录。
"""
import sys
import argparse
from pathlib import Path

import numpy as np
import gmsh

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import (
    R_INNER, T_BASE, T_OCULUS, D_OCULUS,
    COFFER_LAYERS, COFFER_SECTORS, COFFER_GEOMETRY, COFFER_STEPS,
    MESH_DIR,
)

COFFER_EDGE_SIZE = 0.25     # 藻井棱边局部网格尺寸 (m)（P-11，本轮对布尔后倒转无效，保留备用）
FULL_ANGLE = 2 * np.pi
SLICE_SECTORS = 28          # 28 周期对称

sweep_angle = FULL_ANGLE    # 默认整天；--slice 时改为 2π/28
is_slice = False
round_coffer = False        # --round：圆角矩形藻井（磨平 90° 再入角）


def phi_c_levels():
    """5 层藻井子午角（近似均布）"""
    phi_o = np.arcsin(D_OCULUS / (2 * R_INNER))
    return np.linspace(phi_o + np.radians(8), np.radians(78), COFFER_LAYERS)


def thickness(phi):
    """子午角 φ 处厚度：φ_o 处 1.5 m → 拱脚(π/2) 处 5.9 m，线性"""
    phi_o = np.arcsin(D_OCULUS / (2 * R_INNER))
    return T_OCULUS + (T_BASE - T_OCULUS) * (phi - phi_o) / (np.pi / 2 - phi_o)


def build_dome_solid():
    """旋转母线法建变厚度穹顶实体（内边界真圆弧），返回实体 tag"""
    phi_o = np.arcsin(D_OCULUS / (2 * R_INNER))

    xAi, zAi = R_INNER * np.sin(phi_o), R_INNER * np.cos(phi_o)
    xBi, zBi = R_INNER, 0.0
    xBo = R_INNER + thickness(np.pi / 2)
    xAo = (R_INNER + thickness(phi_o)) * np.sin(phi_o)
    zAo = (R_INNER + thickness(phi_o)) * np.cos(phi_o)

    p_ai = gmsh.model.occ.addPoint(xAi, 0, zAi)
    p_bi = gmsh.model.occ.addPoint(xBi, 0, zBi)
    p_bo = gmsh.model.occ.addPoint(xBo, 0, 0)
    p_ao = gmsh.model.occ.addPoint(xAo, 0, zAo)
    p_ctr = gmsh.model.occ.addPoint(0, 0, 0)

    arc = gmsh.model.occ.addCircleArc(p_ai, p_ctr, p_bi)   # 内球面真圆弧
    l_spring = gmsh.model.occ.addLine(p_bi, p_bo)          # 拱脚端盖
    phis = np.linspace(np.pi / 2, phi_o, 60)               # 外型线（变厚度折线）
    outer_tags = [p_bo]
    for p in phis[1:-1]:
        r = R_INNER + thickness(p)
        outer_tags.append(gmsh.model.occ.addPoint(r * np.sin(p), 0, r * np.cos(p)))
    outer_tags.append(p_ao)
    outer_lines = [gmsh.model.occ.addLine(outer_tags[k], outer_tags[k + 1])
                   for k in range(len(outer_tags) - 1)]
    l_oculus = gmsh.model.occ.addLine(p_ao, p_ai)          # oculus 端盖

    loop = gmsh.model.occ.addCurveLoop([arc, l_spring] + outer_lines + [l_oculus])
    surf = gmsh.model.occ.addPlaneSurface([loop])
    gmsh.model.occ.synchronize()

    # 绕 z 轴旋转 sweep_angle：整天 2π，或 --slice 的 2π/28
    out = gmsh.model.occ.revolve([(2, surf)], 0, 0, 0, 0, 0, 1, sweep_angle)
    gmsh.model.occ.synchronize()
    for dim, tag in out:
        if dim == 3:
            return tag
    raise RuntimeError("旋转母线建穹顶实体失败")


def cut_oculus(dome_tag):
    """圆柱切 Oculus 开口，返回新 tag"""
    phi_o = np.arcsin(D_OCULUS / (2 * R_INNER))
    z_o = R_INNER * np.cos(phi_o)
    r_cut = D_OCULUS / 2 + 2.0
    cyl = gmsh.model.occ.addCylinder(0, 0, z_o - 1, 0, 0, 30, r_cut)
    gmsh.model.occ.synchronize()
    res = gmsh.model.occ.cut([(3, dome_tag)], [(3, cyl)],
                             removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    for dim, tag in res[0]:
        if dim == 3:
            return tag
    raise RuntimeError("Oculus 切割失败")


def create_coffer(level, theta_c):
    """在某 (φ_c, θ_c) 位置放藻井盒（局部 z=径向），返回体 tag"""
    phi_o = np.arcsin(D_OCULUS / (2 * R_INNER))
    phi_c = phi_c_levels()[level]

    w = COFFER_GEOMETRY[level][1]      # bottom_w：环向宽
    h = COFFER_GEOMETRY[level][3]      # arc_h：子午向高
    d = COFFER_STEPS[level][0]         # 首级阶梯深（径向）
    margin = 0.5

    box = gmsh.model.occ.addBox(-w / 2, -h / 2, -d / 2 - margin, w, h, d / 2 + margin)
    gmsh.model.occ.synchronize()

    # 定向：绕 y 轴转 φ，再绕 z 轴转 θ → z 指向径向
    gmsh.model.occ.rotate([(3, box)], 0, 0, 0, 0, 1, 0, np.degrees(phi_c))
    gmsh.model.occ.rotate([(3, box)], 0, 0, 0, 0, 0, 1, np.degrees(theta_c))
    gmsh.model.occ.synchronize()

    r_c = R_INNER - d / 2
    x_c = r_c * np.sin(phi_c) * np.cos(theta_c)
    y_c = r_c * np.sin(phi_c) * np.sin(theta_c)
    z_c = r_c * np.cos(phi_c)
    gmsh.model.occ.translate([(3, box)], x_c, y_c, z_c)
    gmsh.model.occ.synchronize()
    return box


def create_coffer_rounded(level, phi_c, theta_c):
    """圆角矩形藻井：4 边圆角 r，挤出成体（局部 z=径向）。2026-08-17 圆角复核用。"""
    w = COFFER_GEOMETRY[level][1]
    h = COFFER_GEOMETRY[level][3]
    d = COFFER_STEPS[level][0]
    margin = 1.5                 # P-12b：加大嵌深，分开布尔相切面（PLC）
    r = min(w, h) / 10.0           # P-12：圆角半径调小，减少布尔相切（PLC）
    r = min(r, 0.3)
    hw, hh = w / 2, h / 2
    dx, dy = hw - r, hh - r

    def P(x, y):
        return gmsh.model.occ.addPoint(x, y, 0)

    # 8 切线点
    b2l, b2r = P(-dx, -hh), P(dx, -hh)     # 下边
    r2b, r2t = P(hw, -dy), P(hw, dy)       # 右边
    t2r, t2l = P(dx, hh), P(-dx, hh)       # 上边
    l2t, l2b = P(-hw, dy), P(-hw, -dy)     # 左边
    # 四角圆心
    cBR, cTR = P(dx, -dy), P(dx, dy)
    cTL, cBL = P(-dx, dy), P(-dx, -dy)
    # 边 + 圆角弧（逆时针闭合）
    L1 = gmsh.model.occ.addLine(b2l, b2r)      # 下边
    A1 = gmsh.model.occ.addCircleArc(b2r, cBR, r2b)  # 右下圆角
    L2 = gmsh.model.occ.addLine(r2b, r2t)      # 右边
    A2 = gmsh.model.occ.addCircleArc(r2t, cTR, t2r)  # 右上圆角
    L3 = gmsh.model.occ.addLine(t2r, t2l)      # 上边
    A3 = gmsh.model.occ.addCircleArc(t2l, cTL, l2t)  # 左上圆角
    L4 = gmsh.model.occ.addLine(l2t, l2b)      # 左边
    A4 = gmsh.model.occ.addCircleArc(l2b, cBL, b2l)  # 左下圆角
    loop = gmsh.model.occ.addCurveLoop([L1, A1, L2, A2, L3, A3, L4, A4])
    surf = gmsh.model.occ.addPlaneSurface([loop])
    gmsh.model.occ.synchronize()
    out = gmsh.model.occ.extrude([(2, surf)], 0, 0, d + 2 * margin)
    gmsh.model.occ.synchronize()
    vol = None
    for dim, tag in out:
        if dim == 3:
            vol = tag
    if vol is None:
        raise RuntimeError("圆角藻井挤出失败")

    gmsh.model.occ.rotate([(3, vol)], 0, 0, 0, 0, 1, 0, np.degrees(phi_c))
    gmsh.model.occ.rotate([(3, vol)], 0, 0, 0, 0, 0, 1, np.degrees(theta_c))
    gmsh.model.occ.synchronize()
    rc = R_INNER - d / 2
    x_c = rc * np.sin(phi_c) * np.cos(theta_c)
    y_c = rc * np.sin(phi_c) * np.sin(theta_c)
    z_c = rc * np.cos(phi_c)
    gmsh.model.occ.translate([(3, vol)], x_c, y_c, z_c)
    gmsh.model.occ.synchronize()
    return vol


def cut_all_coffers(dome_tag):
    """批量挖藻井：满圆周 5×28，或 --slice 每层 1 个居中"""
    if is_slice:
        theta_list = [sweep_angle / 2]              # 扇区中心
    else:
        theta_list = np.linspace(0, 2 * np.pi, COFFER_SECTORS, endpoint=False)
    boxes = []
    for i in range(COFFER_LAYERS):
        for theta_c in theta_list:
            if round_coffer:
                boxes.append((3, create_coffer_rounded(i, phi_c_levels()[i], theta_c)))
            else:
                boxes.append((3, create_coffer(i, theta_c)))
    res = gmsh.model.occ.cut([(3, dome_tag)], boxes, removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    for dim, tag in res[0]:
        if dim == 3:
            return tag
    raise RuntimeError("藻井切割失败")


def centroid_angle_deg(face_tag):
    """面几何中心的角度 atan2(y,x)（度）"""
    x0, y0, z0, x1, y1, z1 = gmsh.model.occ.getBoundingBox(2, face_tag)
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    return np.degrees(np.arctan2(cy, cx))


def mark_groups(dome_tag):
    """拱脚面 400 + 体 1000；--slice 再贴子午切面 500/600"""
    base, faces = [], {}
    for dim, tag in gmsh.model.getEntities(dim=2):
        bbox = gmsh.model.occ.getBoundingBox(dim, tag)
        z_span = bbox[5] - bbox[2]
        if z_span < 0.01 and abs(bbox[2]) < 0.01:
            base.append(tag)                     # z≈0 平环 → 拱脚面

    gmsh.model.addPhysicalGroup(2, base, tag=400, name="dome_base")
    gmsh.model.addPhysicalGroup(3, [dome_tag], tag=1000, name="dome_body")
    print(f"物理组: 拱脚面 {len(base)} / 体 1（子午面 500/600 撒网后贴）")


def tag_meridian_faces():
    """撒网后按网格节点方位角贴两条子午切面（组500 @θ≈0，组600 @θ=α）。
    判定 = 竖向(z跨>10m) 且 面节点方位角集中(spread<6°)：子午面竖直整高，
    藻井面小、球面方位散布 均被排除。"""
    grp0, grp1 = [], []
    half = np.degrees(sweep_angle) / 2
    for dim, tag in gmsh.model.getEntities(dim=2):
        if dim != 2:
            continue
        bbox = gmsh.model.occ.getBoundingBox(dim, tag)
        if (bbox[5] - bbox[2]) < 10.0:           # 竖向不够高 → 非子午面
            continue
        try:
            _, coords, _ = gmsh.model.mesh.getNodes(2, tag)
        except Exception:
            continue
        coords = coords.reshape(-1, 3)
        if coords.shape[0] < 3:
            continue
        ang = np.degrees(np.arctan2(coords[:, 1], coords[:, 0]))
        if ang.max() - ang.min() < 6.0:          # 方位角集中 → 子午面
            (grp0 if np.mean(ang) < half else grp1).append(tag)
    if grp0:
        gmsh.model.addPhysicalGroup(2, grp0, tag=500, name="slice_face0")
    if grp1:
        gmsh.model.addPhysicalGroup(2, grp1, tag=600, name="slice_faceA")
    print(f"子午面: 组500@0° {len(grp0)} 面 / 组600@α° {len(grp1)} 面")


def sweep_angle_deg():
    return np.degrees(sweep_angle)


def main():
    global sweep_angle, is_slice, round_coffer
    parser = argparse.ArgumentParser(description="C3 变厚度+藻井几何")
    parser.add_argument("--lc", type=float, default=1.5, help="网格特征尺寸 (m)")
    parser.add_argument("--no-coffer", action="store_true", help="只建变厚度，不挖藻井")
    parser.add_argument("--slice", action="store_true", help="28 周期对称：母线转 2π/28，每层 1 藻井")
    parser.add_argument("--round", action="store_true",
                        help="圆角矩形藻井（磨平 90° 再入角，复核 θ_top 是否方形尖角虚高）")
    parser.add_argument("--linear2nd", action="store_true",
                        help="SecondOrderLinear=1（退回线性曲边，倒转清零但失曲边精度）")
    parser.add_argument("--out", default="c3_coffer.msh", help="输出文件名（MESH_DIR 下）")
    args = parser.parse_args()

    if args.slice:
        sweep_angle = 2 * np.pi / SLICE_SECTORS
        is_slice = True
    if args.round:
        round_coffer = True

    MESH_DIR.mkdir(parents=True, exist_ok=True)
    gmsh.initialize()
    gmsh.model.add("pantheon_c3")

    print(f"[1/4] 旋转母线建变厚度穹顶（扫角 {sweep_angle_deg():.2f}°）...")
    dome = build_dome_solid()

    print("[2/4] 切 Oculus 开口...")
    dome = cut_oculus(dome)

    if not args.no_coffer:
        print(f"[3/4] 挖藻井（{'满圆周 5x28' if not is_slice else '1 扇区 5 个'}）...")
        dome = cut_all_coffers(dome)
    else:
        print("[3/4] 跳过藻井（--no-coffer）")

    print("[3.5/4] 标记物理组...")
    mark_groups(dome)

    print("[4/4] 撒网 + 导出...")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", args.lc)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    if args.linear2nd:
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.model.mesh.generate(3)

    if is_slice:
        tag_meridian_faces()                     # 撒网后按节点方位角贴 500/600

    out = MESH_DIR / args.out
    gmsh.write(str(out))
    gmsh.finalize()
    print(f"✅ 完成: {out}")


if __name__ == "__main__":
    main()

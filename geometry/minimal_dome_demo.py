#!/usr/bin/env python3
"""
万神殿简化穹顶 · 最小完整案例（文档4 第 14 章落地版）

流程：
  1. 创建均匀厚度球壳（R_inner=22.03, t=平均厚度）
  2. 切割 Oculus 开口（直径 8.95 m）
  3. 标记物理组（内表面200 / 外表面300 / 拱脚面400 / 体1000）
  4. 划分二阶四面体网格
  5. 导出 .msh（c0_shell_groups.msh，供 C1 求解）

运行（WSL）：
  conda activate pantheon-fem
  python geometry/minimal_dome_demo.py

2026-08-15 写：由文档4 §14 完整代码落地；输出名改为 c0_shell_groups.msh
（文档5 §4.3 约定名）；拱脚=球底南极面（简化约束，真实拱脚 C2 鼓座引入）。
"""
import sys
import argparse
from pathlib import Path

import numpy as np
import gmsh

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS, MESH_DIR


def create_shell():
    """均匀厚度球壳（平均厚度近似），返回壳体的 tag"""
    t_avg = (T_OCULUS + T_BASE) / 2
    r_outer = R_INNER + t_avg

    outer = gmsh.model.occ.addSphere(0, 0, 0, r_outer)
    inner = gmsh.model.occ.addSphere(0, 0, 0, R_INNER)
    gmsh.model.occ.synchronize()

    result = gmsh.model.occ.cut([(3, outer)], [(3, inner)])
    gmsh.model.occ.synchronize()

    for dim, tag in result[0]:
        if dim == 3:
            return tag
    raise RuntimeError("球壳创建失败")


def truncate_dome(shell_tag):
    """截断为半球壳（z >= 0），拱脚截面在赤道面 z=0（2026-08-15 修：
    完整球壳无拱脚面，无法贴 400；截断后拱脚 = z=0 环形截面）"""
    box = gmsh.model.occ.addBox(-40, -40, -40, 80, 80, 40)  # z < 0 的大方块
    gmsh.model.occ.synchronize()

    result = gmsh.model.occ.cut(
        [(3, shell_tag)],
        [(3, box)],
        removeObject=True,
        removeTool=True,
    )
    gmsh.model.occ.synchronize()

    for dim, tag in result[0]:
        if dim == 3:
            return tag
    raise RuntimeError("截断失败")


def cut_oculus(shell_tag):
    """在球顶切出 Oculus 圆洞，返回新壳 tag"""
    phi_oculus = np.arcsin(D_OCULUS / (2 * R_INNER))
    z_oculus = R_INNER * np.cos(phi_oculus)

    r_cut = D_OCULUS / 2 + 2.0
    cut_cyl = gmsh.model.occ.addCylinder(
        0, 0, z_oculus - 1,
        0, 0, 30,
        r_cut,
    )
    gmsh.model.occ.synchronize()

    result = gmsh.model.occ.cut(
        [(3, shell_tag)],
        [(3, cut_cyl)],
        removeObject=True,
        removeTool=True,
    )
    gmsh.model.occ.synchronize()

    for dim, tag in result[0]:
        if dim == 3:
            return tag
    raise RuntimeError("Oculus 切割失败")


def mark_groups(shell_tag):
    """按 bbox 特征标记物理组（2026-08-15 修 P-03：整块几何面的 bbox 中心
    判断失效；改为 薄面(环) vs 球面片 + 半宽 判定）：
    内表面200 / 外表面300 / 拱脚面400(z=0环) / Oculus边缘100 / 体1000"""
    inner, outer, base, oculus = [], [], [], []

    for dim, tag in gmsh.model.getEntities(dim=2):
        bbox = gmsh.model.occ.getBoundingBox(dim, tag)
        z_span = bbox[5] - bbox[2]
        half_w = (bbox[3] - bbox[0]) / 2  # x 半宽 = z=0 截面半径（球面片）

        if z_span < 0.01:                # 薄面 = 环
            if abs(bbox[2]) < 0.01:
                base.append(tag)         # z≈0 → 拱脚环面
            else:
                oculus.append(tag)       # z≈21.57 → Oculus 边缘环面
        elif half_w > R_INNER + 1.0:
            outer.append(tag)            # 半宽≈25.73 → 外球面片
        else:
            inner.append(tag)            # 半宽≈22.03 → 内球面片

    gmsh.model.addPhysicalGroup(2, inner,  tag=200, name="dome_inner")
    gmsh.model.addPhysicalGroup(2, outer,  tag=300, name="dome_outer")
    gmsh.model.addPhysicalGroup(2, base,   tag=400, name="dome_base")
    gmsh.model.addPhysicalGroup(2, oculus, tag=100, name="oculus_edge")
    gmsh.model.addPhysicalGroup(3, [shell_tag], tag=1000, name="dome_body")

    print(f"物理组: 内{len(inner)}面 外{len(outer)}面 拱脚{len(base)}面 "
          f"Oculus{len(oculus)}面 体1")


def main():
    parser = argparse.ArgumentParser(description="万神殿截断半球壳网格生成")
    parser.add_argument("--lc", type=float, default=2.0, help="网格特征尺寸 (m)")
    parser.add_argument("--out", default="c0_shell_groups.msh",
                        help="输出文件名（MESH_DIR 下），如 c0_shell_groups_1m.msh")
    args = parser.parse_args()

    MESH_DIR.mkdir(parents=True, exist_ok=True)

    gmsh.initialize()
    gmsh.model.add("pantheon_minimal_dome")

    print("[1/4] 创建球壳...")
    shell_tag = create_shell()

    print("[1.5/4] 截断为半球壳（z>=0，拱脚=赤道截面）...")
    shell_tag = truncate_dome(shell_tag)

    print("[2/4] 切割 Oculus...")
    shell_tag = cut_oculus(shell_tag)

    print("[3/4] 标记物理组...")
    mark_groups(shell_tag)

    print("[4/4] 撒网 + 导出...")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", args.lc)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.model.mesh.generate(3)

    out = MESH_DIR / args.out
    gmsh.write(str(out))
    gmsh.finalize()
    print(f"✅ 完成: {out}")


if __name__ == "__main__":
    main()

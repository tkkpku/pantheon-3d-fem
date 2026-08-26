"""
C0 球壳几何脚本

功能：生成两同心球夹壳（简化等厚近似），划分网格并导出。
运行：python geometry/c0_spherical_shell.py（任意目录可运行，见 sys.path 引导）
"""
import sys
from pathlib import Path

import gmsh

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS, MESH_DIR


def build_shell():
    """创建球壳几何，返回壳体的实体 tag"""
    # 简化：平均厚度近似（T_OCULUS 顶厚 1.5 / T_BASE 拱脚厚 5.9）
    t_avg = (T_OCULUS + T_BASE) / 2
    r_outer = R_INNER + t_avg

    outer = gmsh.model.occ.addSphere(0, 0, 0, r_outer)
    inner = gmsh.model.occ.addSphere(0, 0, 0, R_INNER)

    gmsh.model.occ.synchronize()
    result = gmsh.model.occ.cut(
        [(3, outer)], [(3, inner)], removeObject=True, removeTool=True
    )
    gmsh.model.occ.synchronize()

    for dim, tag in result[0]:
        if dim == 3:
            return tag
    return None


def set_mesh_and_export(shell_tag):
    """设置网格参数、撒网、导出"""
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 2.0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.model.mesh.generate(3)
    gmsh.write(str(MESH_DIR / "c0_shell.msh"))


def main():
    gmsh.initialize()
    gmsh.model.add("c0_shell")

    shell_tag = build_shell()
    assert shell_tag is not None, "球壳 tag 不能为空，检查布尔运算"

    set_mesh_and_export(shell_tag)
    gmsh.finalize()
    print("✅ C0 球壳几何完成")


if __name__ == "__main__":
    main()

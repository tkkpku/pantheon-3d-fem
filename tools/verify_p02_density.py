#!/usr/bin/env python3
"""
P-02 教材坑验证：文档5 §7.3 密度分层 conditional 方向

疑点：代码 `conditional(ge(z, 0.0), 1600, 1350)` 注释写「z>=0 下半部 1600」，
但 z≥0 数学上是上半部——若 z 轴向上，则代码行为 = 「上重下轻」，
与 Masi Table 1「上轻下重」（上 1350 / 下 1600）矛盾。

验证方法：读网格 → 按文档5 §7.3 代码填密度 → 分区统计 z>0 / z<0 区域密度。

运行（WSL）：python tools/verify_p02_density.py
"""
import sys
from pathlib import Path

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import MESH_DIR


def main():
    from dolfinx import fem
    from dolfinx.io import gmshio
    import ufl

    msh = MESH_DIR / "c0_shell_groups.msh"   # 半球壳（z ∈ [0, ~25.7]），dolfinx 可读
    if not msh.exists():
        raise FileNotFoundError(f"网格不存在：{msh}，先跑 geometry/minimal_dome_demo.py")

    domain, _, _ = gmshio.read_from_msh(str(msh), MPI.COMM_WORLD, gdim=3)

    # ===== 按文档5 §7.3 意图实现（P-04 修：ufl.ge 不能吃 numpy 数组；
    #       P-05 修：fem.Expression+W.element 与 interpolate(ufl_expr) 在
    #       dolfinx 0.8 均不可用，改用 Python 可调用插值（最稳写法））=====
    W = fem.functionspace(domain, ("Lagrange", 1))
    rho = fem.Function(W)

    def rho_fill(x):
        # dolfinx interpolate 传入的 x: (3, N) 坐标数组（每列一个点）
        return np.where(x[2] >= 0.0, 1600.0, 1350.0)   # 文档5 注释称 z>=0「下半部 1600」

    rho.interpolate(rho_fill)

    # 一阶空间自由度 = 顶点数（≠ 网格节点数，二阶网格含边中点）——用自由度坐标统计
    dof_coords = W.tabulate_dof_coordinates()
    z_dof = dof_coords[:, 2]
    rho_vals = rho.x.array
    print(f"几何 z 范围: {z_dof.min():.2f} ~ {z_dof.max():.2f} m（半球壳，z 向上）")
    upper = rho_vals[z_dof > 0.5]    # 上半部（本网格全部区域）
    print(f"z > 0 区域密度: 唯一值 = {np.unique(upper)}")

    # 文档5 代码字面行为：z>=0 → 1600。半球壳 z>0 全覆盖，
    # 若全为 1600 则证明「代码把 z>=0（上半部）给了重密度 1600」
    if np.all(upper == 1600.0):
        print("✅ P-02 确认：文档5 §7.3 代码字面行为 = z≥0（上半部）→ 1600（重），"
              "与 Masi Table 1『上 1350 轻 / 下 1600 重』矛盾 → 文档5 代码方向写反"
              "（应 lt(z,0) 或 1350/1600 对调），属教材坑")
    elif np.all(upper == 1350.0):
        print("ℹ️ 代码行为 = 上轻下重，与 Masi 一致 → P-02 不成立（注释笔误？）")
    else:
        print(f"⚠️ 异常：upper={np.unique(upper)}")


if __name__ == "__main__":
    main()

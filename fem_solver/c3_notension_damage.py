#!/usr/bin/env python3
"""
C2+（暂名 c3）：分层密度 + Rankine 无拉伸损伤本构（fixed-point 顺序迭代）

物理：σ1 > ft(0.08 MPa) 的受拉区刚度折减 D = 1 - (ft/σ1)^2（弥散损伤，Masi 2018 思路简化）
      损伤不可逆（单调不减）、封顶 0.9 防奇异；纯压缩区不开裂（D=0）。
数值：每步仍是线弹性求解（cg+BoomerAMG），D 作为标量场系数进入弱形式，迭代至 ||ΔD||∞ 收敛。
      首次解用 E0 全场；D 场与应力 P1 空间 dof 编号一致（同网格同族），直接 numpy 写入。

用法（WSL）：
  python fem_solver/c3_notension_damage.py --mesh c0_shell_groups.msh [--e 14.8e9] [--max-iter 30]

2026-08-16 写：C1 三档网格无关性证据（σ1=0.1572 ≫ ft=0.08 MPa）推动立项。
"""
import sys
import argparse
from pathlib import Path

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import (
    NU_CONCRETE, DENSITY_STEPS, G, FT_CONCRETE, MESH_DIR, RESULT_DIR,
)

DAMAGE_CAP = 0.9        # D 封顶，防刚度奇异
FTOL = 1e-3             # 损伤场迭代收敛容差（L∞）
S1_PROTECT = 1e3        # σ1 极小的保护值 (Pa)，避免除零


def solve_notension(E0: float, msh_path: Path, max_iter: int = 30) -> dict:
    from dolfinx import fem
    from dolfinx.fem import petsc
    from dolfinx.io import gmshio, VTXWriter
    import ufl

    # ============ 1. 网格 + 空间 ============
    domain, cell_tags, facet_tags = gmshio.read_from_msh(
        str(msh_path), MPI.COMM_WORLD, gdim=3)
    V = fem.functionspace(domain, ("Lagrange", 2, (3,)))
    Q1 = fem.functionspace(domain, ("Lagrange", 1))           # 标量损伤场
    S = fem.functionspace(domain, ("Lagrange", 1, (3, 3)))    # 应力投影空间

    # ============ 2. BC：拱脚固支 ============
    base_facets = facet_tags.find(400)
    if base_facets.size == 0:
        raise RuntimeError("find(400) 为空：物理组没贴好")
    dofs = fem.locate_dofs_topological(V, 2, base_facets)
    bc = fem.dirichletbc(fem.Constant(domain, (0.0, 0.0, 0.0)), dofs, V)

    # ============ 3. 密度：分层（上 1350 / 下 1600，z>=0 分界） ============
    W_rho = fem.functionspace(domain, ("Lagrange", 1))
    rho = fem.Function(W_rho)

    def rho_fill(x):
        return np.where(x[2] >= 0.0, DENSITY_STEPS[0][1], DENSITY_STEPS[-1][1])

    rho.interpolate(rho_fill)
    g = fem.Constant(domain, G)
    b = ufl.as_vector([0.0, 0.0, -rho * g])

    # ============ 4. 损伤场与模量场 ============
    D_field = fem.Function(Q1)          # 损伤，初始 0
    E_field = fem.Function(Q1)          # 退化模量 E(x) = E0*(1-D)
    E_field.interpolate(lambda x: np.full(x.shape[1], E0))
    nu = fem.Constant(domain, NU_CONCRETE)

    def lam_of(E):
        return E * nu / ((1 + nu) * (1 - 2 * nu))

    def mu_of(E):
        return E / (2 * (1 + nu))

    # ============ 5. 弱形式（E 是空间场 → lam/mu 是 UFL 表达式） ============
    u = ufl.TrialFunction(V)
    v = ufl.TestFunction(V)

    def epsilon(w):
        return ufl.sym(ufl.grad(w))

    def sigma_w(w):
        lam = lam_of(E_field)
        mu = mu_of(E_field)
        return lam * ufl.tr(epsilon(w)) * ufl.Identity(3) + 2 * mu * epsilon(w)

    a = ufl.inner(sigma_w(u), epsilon(v)) * ufl.dx
    L = ufl.dot(b, v) * ufl.dx

    X = S.element.interpolation_points()          # (N,3) 应力投影求值点（P-05 新 API）

    # ============ 6. fixed-point 迭代 ============
    history = []
    uh = None
    sigma_h = None
    for it in range(max_iter):
        problem = petsc.LinearProblem(
            a, L, bcs=[bc],
            petsc_options={"ksp_type": "cg", "pc_type": "hypre",
                           "pc_hypre_type": "boomeramg", "ksp_rtol": 1e-8},
        )
        uh = problem.solve()

        # 主应力 σ1（S 空间 dof 上）
        sigma_h = fem.Function(S)
        sigma_h.interpolate(fem.Expression(sigma_w(uh), X))
        sigma_nodes = sigma_h.x.array.reshape(-1, 3, 3)
        s1 = np.linalg.eigvalsh(sigma_nodes)[:, -1]   # 升序 → 最后一列是 σ1

        # 损伤更新：Rankine 判据，不可逆，封顶
        s1_pos = np.maximum(s1, S1_PROTECT)
        D_new = np.maximum(1.0 - (FT_CONCRETE / s1_pos) ** 2, 0.0)
        D_new = np.minimum(D_new, DAMAGE_CAP)
        D_old = D_field.x.array.copy()
        D_new = np.maximum(D_new, D_old)              # 不可逆
        delta = float(np.max(np.abs(D_new - D_old)))
        D_field.x.array[:] = D_new

        # 退化模量场：E(x) = E0*(1-D)，与 D 同空间同布局，直接向量写入
        E_field.x.array[:] = E0 * (1.0 - D_field.x.array)

        u_mag = np.sqrt(np.sum(uh.x.array.reshape(-1, 3) ** 2, axis=1))
        u_max = float(u_mag.max()) * 1000.0
        s1_max = float(s1.max()) / 1e6
        d_vol = float(np.mean(D_new > 0.05)) * 100.0   # 损伤区占比 %
        history.append((it + 1, delta, u_max, s1_max, d_vol))
        print(f"iter {it + 1:2d}: ΔD={delta:.4e}  u_max={u_max:.4f} mm  "
              f"σ1_max={s1_max:.4f} MPa  损伤区={d_vol:.2f}%")

        if delta < FTOL:
            print(f"✅ 损伤场收敛（ΔD < {FTOL}），共 {it + 1} 次迭代")
            break

    # ============ 7. 导出 ============
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    tag = f"{msh_path.stem}_c3"
    with VTXWriter(domain.comm, str(RESULT_DIR / f"{tag}_u.bp"), [uh]) as w:
        w.write(0)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"{tag}_sigma.bp"), [sigma_h]) as w:
        w.write(0)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"{tag}_D.bp"), [D_field]) as w:
        w.write(0)

    return {"dof": V.dofmap.index_map.size_global, "history": history,
            "converged": history[-1][1] < FTOL}


def main():
    parser = argparse.ArgumentParser(description="C2+ 无拉伸损伤（Rankine fixed-point）")
    parser.add_argument("--mesh", default="c0_shell_groups.msh")
    parser.add_argument("--e", type=float, default=14.8e9)
    parser.add_argument("--max-iter", type=int, default=30)
    args = parser.parse_args()

    msh_path = MESH_DIR / args.mesh
    if not msh_path.exists():
        raise FileNotFoundError(f"网格不存在：{msh_path}")

    r = solve_notension(args.e, msh_path, args.max_iter)
    print(f"\n收敛状态: {'✅ 已收敛' if r['converged'] else '⚠️ 达到迭代上限'}")
    print("结果导出: output/results/c0_shell_groups*_c3_*.bp")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
C4+：自重+干缩 + Rankine 无拉伸损伤本构（fixed-point 顺序迭代）

物理：在 c3_notension_damage.py（C2+ 损伤）基础上叠加干缩：
      σ = λ(x) tr(ε_mech) I + 2μ(x) ε_mech，ε_mech = ε_tot + ε_sh·I（收缩，P-07 加号）
      损伤场 D(x) 折减模量 E(x)=E0(1-D) → 干缩等效荷载 ε_sh(3λ(x)+2μ(x))·div(v) 随损伤演化
      （损伤区贡献的收缩约束应力同步衰减，物理自洽）。
数值：每步线弹性 cg+BoomerAMG；σ1>ft 处 D=1-(ft/σ1)² 不可逆、封顶 0.9；||ΔD||∞<1e-3 收敛。

参数口径（2026-08-17 项目决策，一切以文献为准）：
      E0 默认 1.0e9 Pa（Masi Table 1 穹顶 28 天收缩模拟龄期值）
      ε_sh 默认 6.0e-5（Masi p.8 ε_v=0.15~0.30e-3 桥接 ε_v/3；五档扫描 4e-5~1e-4）
      开裂验收：θ_max 对照 Masi Table 2（47.4→65.8°）+ Terenzio 实测 ~57°

用法（WSL）：
  python fem_solver/c4plus_damage.py --mesh c0_shell_groups.msh
  python fem_solver/c4plus_damage.py --mesh c0_shell_groups.msh --eps-sh 5.0e-5 --e 1.0e9

2026-08-17 写：C4 线弹性扫描基础上立项。
"""
import sys
import argparse
from pathlib import Path

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import (
    NU_CONCRETE, DENSITY_STEPS, G, FT_CONCRETE,
    E_SHRINKAGE, EPS_SHRINKAGE, MESH_DIR, RESULT_DIR,
)

DAMAGE_CAP = 0.9        # D 封顶，防刚度奇异
FTOL = 1e-3             # 损伤场迭代收敛容差（L∞）
S1_PROTECT = 1e3        # σ1 极小的保护值 (Pa)，避免除零


def solve_damage(E0: float, eps_sh_value: float, msh_path: Path,
                 max_iter: int = 30) -> dict:
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

    # ============ 3. 密度分层 + 自重 ============
    W_rho = fem.functionspace(domain, ("Lagrange", 1))
    rho = fem.Function(W_rho)

    def rho_fill(x):
        return np.where(x[2] >= 0.0, DENSITY_STEPS[0][1], DENSITY_STEPS[-1][1])

    rho.interpolate(rho_fill)
    g = fem.Constant(domain, G)
    b = ufl.as_vector([0.0, 0.0, -rho * g])

    # ============ 4. 损伤场与模量场 ============
    D_field = fem.Function(Q1)
    E_field = fem.Function(Q1)
    E_field.interpolate(lambda x: np.full(x.shape[1], E0))
    nu = fem.Constant(domain, NU_CONCRETE)
    eps_sh = fem.Constant(domain, eps_sh_value)

    def lam_of(E):
        return E * nu / ((1 + nu) * (1 - 2 * nu))

    def mu_of(E):
        return E / (2 * (1 + nu))

    # ============ 5. 弱形式（E 空间场；干缩项随 E(x) 演化） ============
    u = ufl.TrialFunction(V)
    v = ufl.TestFunction(V)
    I3 = ufl.Identity(3)

    def epsilon(w):
        return ufl.sym(ufl.grad(w))

    lam_f = lam_of(E_field)
    mu_f = mu_of(E_field)
    a = ufl.inner(lam_f * ufl.tr(epsilon(u)) * I3 + 2 * mu_f * epsilon(u),
                  epsilon(v)) * ufl.dx
    # 右端：自重 − 干缩等效荷载（符号推导同 c4_dome_shrinkage.py 文件头）
    L = (ufl.dot(b, v) - eps_sh * (3 * lam_f + 2 * mu_f) * ufl.div(v)) * ufl.dx

    X = S.element.interpolation_points()

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

        # 含干缩的完整应力（P-07c：后处理口径与荷载一致，这里恒含干缩）
        def sigma_post(w):
            eps_mech = epsilon(w) + eps_sh * I3
            return lam_f * ufl.tr(eps_mech) * I3 + 2 * mu_f * eps_mech

        sigma_h = fem.Function(S)
        sigma_h.interpolate(fem.Expression(sigma_post(uh), X))
        sigma_nodes = sigma_h.x.array.reshape(-1, 3, 3)
        s1 = np.linalg.eigvalsh(sigma_nodes)[:, -1]

        # Rankine 损伤更新（同 c3：不可逆、封顶）
        s1_pos = np.maximum(s1, S1_PROTECT)
        D_new = np.maximum(1.0 - (FT_CONCRETE / s1_pos) ** 2, 0.0)
        D_new = np.minimum(D_new, DAMAGE_CAP)
        D_old = D_field.x.array.copy()
        D_new = np.maximum(D_new, D_old)
        delta = float(np.max(np.abs(D_new - D_old)))
        D_field.x.array[:] = D_new
        E_field.x.array[:] = E0 * (1.0 - D_field.x.array)

        u_mag = np.sqrt(np.sum(uh.x.array.reshape(-1, 3) ** 2, axis=1))
        u_max = float(u_mag.max()) * 1000.0
        s1_max = float(s1.max()) / 1e6
        d_vol = float(np.mean(D_new > 0.05)) * 100.0
        history.append((it + 1, delta, u_max, s1_max, d_vol))
        print(f"iter {it + 1:2d}: ΔD={delta:.4e}  u_max={u_max:.4f} mm  "
              f"σ1_max={s1_max:.4f} MPa  损伤区={d_vol:.2f}%")
        if delta < FTOL:
            print(f"✅ 损伤场收敛（ΔD < {FTOL}），共 {it + 1} 次迭代")
            break

    # ============ 7. 开裂角度口径（拱脚 0° 起算，对照 Masi Table 2 θ_max） ============
    # P-07b：tabulate_dof_coordinates 按点去重返回 (N,3)，自适应兼容 9N 布局
    Xg = np.asarray(S.tabulate_dof_coordinates())
    n_pts = sigma_nodes.shape[0]
    if Xg.ndim == 2 and Xg.shape[0] == n_pts:
        Xp = Xg
    elif Xg.ndim == 2 and Xg.shape[0] == 9 * n_pts:
        Xp = Xg.reshape(-1, 9, 3)[:, 0, :]
    else:
        raise RuntimeError(f"坐标布局未识别：Xg.shape={Xg.shape} vs 应力点 {n_pts}")
    assert D_field.x.array.size == n_pts, "损伤场与应力点布局不一致"

    r = np.linalg.norm(Xp, axis=1)
    phi_z_deg = np.degrees(np.arccos(np.clip(Xp[:, 2] / r, -1.0, 1.0)))
    angle_from_spring = 90.0 - phi_z_deg
    crack_idx = D_field.x.array > 0.05          # 损伤区口径（D>5%），同 c3
    crack_frac = float(np.mean(crack_idx)) * 100.0
    crack_top_deg = float(angle_from_spring[crack_idx].max()) if crack_idx.any() else 0.0

    # ---- 口径对齐：最大连通损伤带顶端（剔除孤立损伤点，2026-08-17） ----
    crack_conn_deg = 0.0
    if crack_idx.any():
        domain.topology.create_connectivity(3, 0)
        c2v = domain.topology.connectivity(3, 0)
        nv = domain.topology.index_map(0).size_local
        if nv == n_pts:
            from collections import deque
            adj = [[] for _ in range(nv)]
            for c in range(c2v.num_nodes):
                v = c2v.links(c)
                for i in range(4):
                    for j in range(i + 1, 4):
                        a, b = int(v[i]), int(v[j])
                        adj[a].append(b)
                        adj[b].append(a)
            unvisited = np.where(crack_idx)[0]
            seen = np.zeros(nv, dtype=bool)
            best_top, best_size = 0.0, 0
            for s in unvisited:
                if seen[s]:
                    continue
                dq = deque([s]); seen[s] = True; comp = []
                while dq:
                    a = dq.popleft(); comp.append(a)
                    for b in adj[a]:
                        if crack_idx[b] and not seen[b]:
                            seen[b] = True; dq.append(b)
                if len(comp) > best_size:
                    best_size = len(comp)
                    best_top = float(angle_from_spring[comp].max())
            crack_conn_deg = best_top

    # ============ 8. 导出 ============
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    tag = f"c4plus_{msh_path.stem}_E{E0 / 1e9:.1f}_sh{eps_sh_value:.2e}"
    with VTXWriter(domain.comm, str(RESULT_DIR / f"{tag}_u.bp"), [uh]) as w:
        w.write(0)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"{tag}_sigma.bp"), [sigma_h]) as w:
        w.write(0)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"{tag}_D.bp"), [D_field]) as w:
        w.write(0)

    return {"dof": V.dofmap.index_map.size_global * 3, "history": history,
            "converged": history[-1][1] < FTOL,
            "crack_frac_pct": crack_frac, "crack_top_deg": crack_top_deg,
            "crack_conn_deg": crack_conn_deg}


def main():
    parser = argparse.ArgumentParser(description="C4+ 自重+干缩 Rankine 无拉伸损伤")
    parser.add_argument("--mesh", default="c0_shell_groups.msh")
    parser.add_argument("--e", type=float, default=E_SHRINKAGE,
                        help=f"E (Pa)，默认 params.E_SHRINKAGE={E_SHRINKAGE:.1e}（Masi 收缩龄期值）")
    parser.add_argument("--eps-sh", type=float, default=EPS_SHRINKAGE,
                        help=f"干缩应变，默认 params.EPS_SHRINKAGE={EPS_SHRINKAGE:.2e}")
    parser.add_argument("--max-iter", type=int, default=30)
    args = parser.parse_args()

    msh_path = MESH_DIR / args.mesh
    if not msh_path.exists():
        raise FileNotFoundError(f"网格不存在：{msh_path}")

    r = solve_damage(args.e, args.eps_sh, msh_path, args.max_iter)
    print(f"\n收敛状态: {'✅ 已收敛' if r['converged'] else '⚠️ 达到迭代上限'}")
    print(f"损伤区占比 = {r['crack_frac_pct']:.2f}%")
    print(f"开裂区顶端角度（拱脚=0° 起算）= {r['crack_top_deg']:.1f}°  "
          f"（Masi Table 2: 47.4→65.8°；Terenzio 实测 ~57°）")
    print(f"最大连通损伤带顶端（口径对齐）= {r['crack_conn_deg']:.1f}°")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
C5：28 周期对称切片 · 变厚度+藻井 干缩求解（复核 C3 满藻井 θ_top 是否虚高）

目的：C3 满圆周藻井网格（完整曲边）有 8 个倒转单元无法求解；改用 28 切片
      （1/28，5 藻井，完整曲边+HighOrderOptimize 倒转清零）复核 θ_top。
对称 BC：两条子午切面（组 500 @θ≈0 即 x-z 平面、组 600 @θ=α=2π/28）约束 u·n=0。
  - 面 500（x-z 平面）：精确 Dirichlet u_y=0
  - 面 600（旋转法向）：罚函数硬约束 γ∫(n·u)(n·v) ds，γ→大 近刚性
荷载/参数同 C4（E=1.0 GPa、ε_sh 文献值、自重分层）。

本工具为完整曲边复核用；罚函数引入额外矩阵项，收敛性与精度以实际跑通为准。

用法（WSL）：
  python fem_solver/c5_slice_shrinkage.py --mesh c3_coffer_28.msh --load sw+sh \
      --e 1.0e9 --eps-sh 1.0e-4 --gamma 1e9

2026-08-17 写。
"""
import sys
import argparse
from pathlib import Path

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import (
    NU_CONCRETE, DENSITY_STEPS, G, E_SHRINKAGE, EPS_SHRINKAGE, FT_CONCRETE,
    MESH_DIR, RESULT_DIR,
)

SLICE_SECTORS = 28
ALPHA = 2 * np.pi / SLICE_SECTORS        # 扇区角


def solve_slice(load, msh_path, out_tag, E_value, eps_sh_value, gamma):
    from dolfinx import fem
    from dolfinx.fem import petsc
    from dolfinx.io import gmshio, VTXWriter
    import ufl

    domain, cell_tags, facet_tags = gmshio.read_from_msh(str(msh_path), MPI.COMM_WORLD, gdim=3)
    V = fem.functionspace(domain, ("Lagrange", 2, (3,)))

    # ---- BC：拱脚固支 ----
    base_facets = facet_tags.find(400)
    if base_facets.size == 0:
        raise RuntimeError("find(400) 为空")
    dofs = fem.locate_dofs_topological(V, 2, base_facets)
    bcs = [fem.dirichletbc(fem.Constant(domain, (0.0, 0.0, 0.0)), dofs, V)]

    # ---- BC：面500(θ≈0, x-z 平面) 精确 u_y=0（子空间；locate 返回 list → 摊平成 ndarray） ----
    f500 = facet_tags.find(500)
    if f500.size > 0:
        dofs_y = fem.locate_dofs_topological((V, V.sub(1)), 2, f500)
        dofs_y = np.concatenate([np.asarray(a).reshape(-1) for a in dofs_y]).astype(np.int32)
        bcs.append(fem.dirichletbc(fem.Constant(domain, 0.0), dofs_y, V.sub(1)))

    # ---- 材料 + 密度 + 自重 ----
    E = fem.Constant(domain, E_value)
    nu = fem.Constant(domain, NU_CONCRETE)
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    eps_sh = fem.Constant(domain, eps_sh_value)

    W_rho = fem.functionspace(domain, ("Lagrange", 1))
    rho = fem.Function(W_rho)

    def rho_fill(x):
        return np.where(x[2] >= 0.0, DENSITY_STEPS[0][1], DENSITY_STEPS[-1][1])

    rho.interpolate(rho_fill)
    g = fem.Constant(domain, G)
    b = ufl.as_vector([0.0, 0.0, -rho * g])

    # ---- 弱形式 ----
    u = ufl.TrialFunction(V)
    v = ufl.TestFunction(V)
    I3 = ufl.Identity(3)

    def epsilon(w):
        return ufl.sym(ufl.grad(w))

    a = ufl.inner(lam * ufl.tr(epsilon(u)) * I3 + 2 * mu * epsilon(u), epsilon(v)) * ufl.dx
    if load == "sw":
        L = ufl.dot(b, v) * ufl.dx
    elif load == "sh":
        L = -eps_sh * (3 * lam + 2 * mu) * ufl.div(v) * ufl.dx
    else:  # sw+sh
        L = (ufl.dot(b, v) - eps_sh * (3 * lam + 2 * mu) * ufl.div(v)) * ufl.dx

    # ---- 面600(θ=α, n=(-sinα,cosα,0)) 罚函数硬约束 u·n=0（旋转法向无法走分量 BC） ----
    ds = ufl.Measure("ds", domain=domain, subdomain_data=facet_tags)
    f600 = facet_tags.find(600)
    if f600.size > 0:
        n600 = ufl.as_vector([-np.sin(ALPHA), np.cos(ALPHA), 0.0])
        a += gamma * ufl.dot(u, n600) * ufl.dot(v, n600) * ds(600)
        print(f"对称面600 罚: {f600.size} facet, γ={gamma:.1e}")

    # ---- 求解 ----
    problem = petsc.LinearProblem(
        a, L, bcs=bcs,
        petsc_options={"ksp_type": "cg", "pc_type": "hypre",
                       "pc_hypre_type": "boomeramg", "ksp_rtol": 1e-8},
    )
    uh = problem.solve()

    # ---- 统计 ----
    u_mag = np.sqrt(np.sum(uh.x.array.reshape(-1, 3) ** 2, axis=1))
    u_max = float(u_mag.max()) * 1000.0

    S = fem.functionspace(domain, ("Lagrange", 1, (3, 3)))
    sigma_h = fem.Function(S)
    X = S.element.interpolation_points()

    def sigma_full(w):
        eps_mech = epsilon(w) + eps_sh * I3
        return lam * ufl.tr(eps_mech) * I3 + 2 * mu * eps_mech

    sigma_h.interpolate(fem.Expression(sigma_full(uh), X))
    sigma_nodes = sigma_h.x.array.reshape(-1, 3, 3)
    principal = np.linalg.eigvalsh(sigma_nodes)
    s1 = principal[:, -1]

    # 求值点坐标（P-07b：去重/自适应布局）
    Xg = np.asarray(S.tabulate_dof_coordinates())
    n_pts = sigma_nodes.shape[0]
    if Xg.ndim == 2 and Xg.shape[0] == n_pts:
        Xp = Xg
    elif Xg.ndim == 2 and Xg.shape[0] == 9 * n_pts:
        Xp = Xg.reshape(-1, 9, 3)[:, 0, :]
    else:
        raise RuntimeError(f"坐标布局未识别 {Xg.shape} vs {n_pts}")
    r = np.linalg.norm(Xp, axis=1)
    phi_z = np.degrees(np.arccos(np.clip(Xp[:, 2] / r, -1.0, 1.0)))
    angle_from_spring = 90.0 - phi_z
    crack = s1 > FT_CONCRETE
    crack_frac = float(np.mean(crack)) * 100.0
    crack_top = float(angle_from_spring[crack].max()) if crack.any() else 0.0

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"{out_tag}_u.bp"), [uh]) as w:
        w.write(0)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"{out_tag}_sigma.bp"), [sigma_h]) as w:
        w.write(0)

    return {"dof": V.dofmap.index_map.size_global * 3, "u_max_mm": u_max,
            "s1_max_MPa": float(s1.max()) / 1e6,
            "s3_min_MPa": float(principal[:, 0].min()) / 1e6,
            "crack_frac_pct": crack_frac, "crack_top_deg": crack_top}


def main():
    parser = argparse.ArgumentParser(description="28 切片变厚度+藻井 干缩求解")
    parser.add_argument("--mesh", default="c3_coffer_28.msh")
    parser.add_argument("--load", choices=["sw", "sh", "sw+sh"], default="sw+sh")
    parser.add_argument("--e", type=float, default=E_SHRINKAGE)
    parser.add_argument("--eps-sh", type=float, default=EPS_SHRINKAGE)
    parser.add_argument("--gamma", type=float, default=1e9, help="对称罚函数系数")
    args = parser.parse_args()

    msh_path = MESH_DIR / args.mesh
    if not msh_path.exists():
        raise FileNotFoundError(str(msh_path))

    out_tag = f"c5_{msh_path.stem}_{args.load.replace('+', 'p')}_E{args.e / 1e9:.1f}_sh{args.eps_sh:.2e}"
    r = solve_slice(args.load, msh_path, out_tag, args.e, args.eps_sh, args.gamma)
    print(f"\n===== C5 切片结果（{args.load}） =====")
    print(f"自由度 = {r['dof']}")
    print(f"最大位移 = {r['u_max_mm']:.4f} mm")
    print(f"σ1 = {r['s1_max_MPa']:.4f} MPa  σ3 = {r['s3_min_MPa']:.4f} MPa")
    print(f"开裂区 = {r['crack_frac_pct']:.2f}%  顶点角度 = {r['crack_top_deg']:.1f}°")


if __name__ == "__main__":
    main()

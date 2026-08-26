#!/usr/bin/env python3
"""
C6：穹顶+鼓座+基座 自重+干缩求解（战役三）

材料按区域（z/r）callable 赋：
  穹顶 z>0        : E=E_DOME(shrinkage 龄期值 1.0 GPa)，rho 分层 DENSITY_STEPS
  鼓座 -H_DRUM<z<0 : E=E_WALL(7.0 GPa)，rho=DENSITY_WALL
  基座 z<-H_DRUM   : E=E_FOUNDATION(13.5 GPa)，rho=DENSITY_FOUNDATION
BC：基座底面(组400)全固支（地面）——穹顶不再视为拱脚固支。
θ_top 只统计穹顶区(z>0)的 σ1>ft 名义开裂顶端角（拱脚=0° 起算）。
关键问题：弹性鼓座替代「拱脚全固支」后，穹顶干缩裂缝是否上爬（检验鼓座是否 57° 缺口）。

用法（WSL）：
  python fem_solver/c6_drum_solve.py --mesh c6_drum_base.msh --load sw+sh --eps-sh 1.0e-4

2026-08-17 写：战役三首版。
"""
import sys
import argparse
from pathlib import Path

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import (
    NU_CONCRETE, DENSITY_STEPS, DENSITY_WALL, DENSITY_FOUNDATION,
    E_WALL, E_FOUNDATION, E_SHRINKAGE, EPS_SHRINKAGE, FT_CONCRETE,
    G, MESH_DIR, RESULT_DIR,
)

H_DRUM = 21.7
DRUM_IN, DRUM_OUT = 22.03, 27.93


def solve_case(load, msh_path, out_tag, eps_sh_value, max_iter=30):
    from dolfinx import fem
    from dolfinx.fem import petsc
    from dolfinx.io import gmshio, VTXWriter
    import ufl

    domain, cell_tags, facet_tags = gmshio.read_from_msh(str(msh_path), MPI.COMM_WORLD, gdim=3)
    V = fem.functionspace(domain, ("Lagrange", 2, (3,)))

    # ---- BC：基座底面(400)全固支 ----
    base_facets = facet_tags.find(400)
    if base_facets.size == 0:
        raise RuntimeError("find(400) 为空")
    dofs = fem.locate_dofs_topological(V, 2, base_facets)
    bcs = [fem.dirichletbc(fem.Constant(domain, (0.0, 0.0, 0.0)), dofs, V)]

    # ---- 材料空间场：E(x), rho(x) ----
    W = fem.functionspace(domain, ("Lagrange", 1))
    E_field = fem.Function(W)
    rho_field = fem.Function(W)

    def fill(x):  # x: (3,N)；E,rho 按 z 分区
        z = x[2]
        E = np.where(z > 0.0, E_SHRINKAGE, 0.0)                          # 穹顶(年轻, 收缩龄期)
        E = np.where((z <= 0.0) & (z > -H_DRUM), E_WALL, E)              # 鼓座成熟
        E = np.where(z <= -H_DRUM, E_FOUNDATION, E)                      # 基座
        rho = np.full(x.shape[1], DENSITY_FOUNDATION)                    # 默认基座
        rho = np.where((z <= 0.0) & (z > -H_DRUM), DENSITY_WALL, rho)    # 鼓座
        rho_dome = np.where(z >= 0.0, DENSITY_STEPS[0][1], DENSITY_STEPS[-1][1])
        rho = np.where(z > 0.0, rho_dome, rho)                           # 穹顶分层
        return E, rho

    E_field.interpolate(lambda x: fill(x)[0])
    rho_field.interpolate(lambda x: fill(x)[1])

    # 干缩只施于穹顶区（z>0）——Masi 施工序列：穹顶后浇收缩、鼓座/基座成熟不缩（项目决策·甲方案）
    sh_marker = fem.Function(W)
    sh_marker.interpolate(lambda x: np.where(x[2] > 0.0, 1.0, 0.0))

    nu = fem.Constant(domain, NU_CONCRETE)

    def lam_of(Ev):
        return Ev * nu / ((1 + nu) * (1 - 2 * nu))

    def mu_of(Ev):
        return Ev / (2 * (1 + nu))

    eps_sh = fem.Constant(domain, eps_sh_value)
    g = fem.Constant(domain, G)
    b = ufl.as_vector([0.0, 0.0, -rho_field * g])

    u = ufl.TrialFunction(V)
    v = ufl.TestFunction(V)
    I3 = ufl.Identity(3)

    def epsilon(w):
        return ufl.sym(ufl.grad(w))

    lam_f = lam_of(E_field)
    mu_f = mu_of(E_field)
    a = ufl.inner(lam_f * ufl.tr(epsilon(u)) * I3 + 2 * mu_f * epsilon(u), epsilon(v)) * ufl.dx
    if load == "sw":
        L = ufl.dot(b, v) * ufl.dx
    elif load == "sh":
        L = -eps_sh * (3 * lam_f + 2 * mu_f) * sh_marker * ufl.div(v) * ufl.dx
    else:
        L = (ufl.dot(b, v) - eps_sh * (3 * lam_f + 2 * mu_f) * sh_marker * ufl.div(v)) * ufl.dx

    problem = petsc.LinearProblem(
        a, L, bcs=bcs,
        petsc_options={"ksp_type": "cg", "pc_type": "hypre",
                       "pc_hypre_type": "boomeramg", "ksp_rtol": 1e-8},
    )
    uh = problem.solve()

    u_mag = np.sqrt(np.sum(uh.x.array.reshape(-1, 3) ** 2, axis=1))
    u_max = float(u_mag.max()) * 1000.0

    S = fem.functionspace(domain, ("Lagrange", 1, (3, 3)))
    sigma_h = fem.Function(S)
    X = S.element.interpolation_points()

    def sigma_el(w):
        return lam_f * ufl.tr(epsilon(w)) * I3 + 2 * mu_f * epsilon(w)

    def sigma_full(w):
        eps_mech = epsilon(w) + eps_sh * sh_marker * I3     # 干缩仅穹顶区
        return lam_f * ufl.tr(eps_mech) * I3 + 2 * mu_f * eps_mech

    sigma_post = sigma_el if load == "sw" else sigma_full    # P-07c：口径随荷载
    sigma_h.interpolate(fem.Expression(sigma_post(uh), X))
    sn = sigma_h.x.array.reshape(-1, 3, 3)
    principal = np.linalg.eigvalsh(sn)
    s1 = principal[:, -1]
    s1_max = float(s1.max()) / 1e6
    s3_min = float(principal[:, 0].min()) / 1e6

    Xg = np.asarray(S.tabulate_dof_coordinates())
    n_pts = sn.shape[0]
    if Xg.ndim == 2 and Xg.shape[0] == n_pts:
        Xp = Xg
    elif Xg.ndim == 2 and Xg.shape[0] == 9 * n_pts:
        Xp = Xg.reshape(-1, 9, 3)[:, 0, :]
    else:
        raise RuntimeError(f"坐标布局 {Xg.shape} vs {n_pts}")

    # θ_top 只看穹顶区(z>0)
    dome_mask = Xp[:, 2] > 0.0
    r = np.linalg.norm(Xp, axis=1)
    phi_z = np.degrees(np.arccos(np.clip(Xp[:, 2] / r, -1.0, 1.0)))
    angle = 90.0 - phi_z
    crack = (s1 > FT_CONCRETE) & dome_mask
    crack_frac = float(np.mean(crack)) * 100.0
    crack_top = float(angle[crack & dome_mask].max()) if np.any(crack) else 0.0

    # ---- 口径对齐：最大连通裂缝簇顶端（穹顶区）+ 环向转压带（2026-08-17） ----
    crack_conn = 0.0
    if np.any(crack):
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
                        adj[a].append(b); adj[b].append(a)
            unvisited = np.where(crack)[0]
            seen = np.zeros(nv, dtype=bool)
            best_top, best_size = 0.0, 0
            for s in unvisited:
                if seen[s]:
                    continue
                dq = deque([s]); seen[s] = True; comp = []
                while dq:
                    a = dq.popleft(); comp.append(a)
                    for b in adj[a]:
                        if crack[b] and not seen[b]:
                            seen[b] = True; dq.append(b)
                if len(comp) > best_size:
                    best_size = len(comp)
                    best_top = float(angle[comp].max())
            crack_conn = best_top

    # 环向转压带（穹顶区，1° 带均值）
    hoop_trans = 0.0
    th = np.arctan2(Xp[:, 1], Xp[:, 0])
    e_th = np.stack([-np.sin(th), np.cos(th), np.zeros_like(th)], axis=1)
    s_th = np.einsum("ni,nij,nj->n", e_th, sn, e_th)
    band = np.clip(np.floor(angle).astype(int), 0, 89)
    for k in range(90):
        sel = (band == k) & dome_mask
        if sel.sum() > 10 and s_th[sel].mean() > 0.0:
            hoop_trans = float(k + 1)

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"{out_tag}_u.bp"), [uh]) as w:
        w.write(0)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"{out_tag}_sigma.bp"), [sigma_h]) as w:
        w.write(0)

    return {"dof": V.dofmap.index_map.size_global * 3, "u_max_mm": u_max,
            "s1_max_MPa": s1_max, "s3_min_MPa": s3_min,
            "crack_frac_pct": crack_frac, "crack_top_deg": crack_top,
            "crack_conn_deg": crack_conn, "hoop_transition_deg": hoop_trans}


def main():
    parser = argparse.ArgumentParser(description="C6 穹顶+鼓座+基座 求解")
    parser.add_argument("--mesh", default="c6_drum_base.msh")
    parser.add_argument("--load", choices=["sw", "sh", "sw+sh"], default="sw+sh")
    parser.add_argument("--eps-sh", type=float, default=EPS_SHRINKAGE)
    args = parser.parse_args()

    msh_path = MESH_DIR / args.mesh
    if not msh_path.exists():
        raise FileNotFoundError(str(msh_path))

    out_tag = f"c6_{msh_path.stem}_{args.load.replace('+', 'p')}_sh{args.eps_sh:.2e}"
    r = solve_case(args.load, msh_path, out_tag, args.eps_sh)
    print(f"\n===== C6 结果（{args.load}） =====")
    print(f"自由度 = {r['dof']}")
    print(f"最大位移 = {r['u_max_mm']:.3f} mm")
    print(f"σ1 = {r['s1_max_MPa']:.4f} MPa  σ3 = {r['s3_min_MPa']:.4f} MPa")
    print(f"穹顶开裂区 = {r['crack_frac_pct']:.2f}%  顶点角度 = {r['crack_top_deg']:.1f}°")
    print(f"连通裂缝带顶端（口径对齐）= {r['crack_conn_deg']:.1f}°  "
          f"环向转压带 = {r['hoop_transition_deg']:.1f}°")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
C4：穹顶干缩线弹性（热应变类比法，文档5 §10.2 落地 + 收缩符号修正）

物理：混凝土干缩 = 自由应变 ε_free = -ε_sh·I（收缩，负值），被拱脚固支约束后产生拉应力。
      力学应变 ε_mech = ε_tot - ε_free = ε_tot + ε_sh·I   ← 注意：热膨胀模板是减号，干缩是加号
      本构 σ = λ tr(ε_mech) I + 2μ ε_mech

弱形式推导（符号验算）：
      σ(u) = σ_el(u) + ε_sh(3λ+2μ) I
      ∫ σ(u):ε(v) = ∫ σ_el(u):ε(v) + ε_sh(3λ+2μ)∫ div(v)
      移项 → 右端荷载 = ∫ b·v - ε_sh(3λ+2μ)∫ div(v)
      一维自检：两端固支杆 → u=0，σ = E(0+ε_sh) = +E·ε_sh（受拉）✓

量级自检：E·ε_sh = 14.8e9 × 1.23e-5 = 182 kPa（与 params.py 注释「σ_sh=182 kPa / E」一致 ✓）

荷载组合（--load）：
  sw    自重 only        → C2 复刻（sanity：应复现 u_max≈0.7071 mm @2.0m，σ1≈0.0562 MPa）
  sh    干缩 only        → 归因对照（分离干缩单独贡献）
  sw+sh 自重+干缩（默认）→ C4 主算

线弹性叠加自检：逐点 u(sw+sh)=u(sw)+u(sh)、σ(sw+sh)=σ(sw)+σ(sh) 精确成立
（同一刚度矩阵，荷载相加 → 解相加）；但 max|u| 因范数非线性不直接可加，
满足 |u_sw+sh|max ≤ |u_sw|max + |u_sh|max。场级对比 .bp 可互验。

验收口径（Masi et al. 2018，见 docs/_legacy_source/pantheon_仿真结果检验清单_v1.md L124）：
  子午向裂缝从底部（拱脚）延伸至 ~57°。
  本脚本输出「σ1>ft 名义开裂区顶端角度（拱脚=0° 起算）」，与历史实测定性对比。
  角度映射：φ_z = arccos(z/r)（Z 轴起算，0°=天窗轴，90°=赤道/拱脚），angle_from_spring = 90° - φ_z。

用法（WSL）：
  python fem_solver/c4_dome_shrinkage.py --load sw+sh --mesh c0_shell_groups.msh
  python fem_solver/c4_dome_shrinkage.py --load sh   --mesh c0_shell_groups.msh
  python fem_solver/c4_dome_shrinkage.py --load sw   --mesh c0_shell_groups.msh   # sanity
  python fem_solver/c4_dome_shrinkage.py --load sw+sh --eps-sh 6.2e-6   # 敏感性 -50%

2026-08-17 写：C4 主算（自重+干缩）+ 归因（干缩单独）+ C2 复刻自检。
"""
import sys
import argparse
from pathlib import Path

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import (
    NU_CONCRETE, DENSITY_STEPS, G, E_CONCRETE,
    EPS_SHRINKAGE, FT_CONCRETE, MESH_DIR, RESULT_DIR,
)


def solve_case(load: str, msh_path: Path, out_tag: str, E_value: float,
               eps_sh_value: float, density_mode: str = "layered") -> dict:
    """单个荷载组合的 C4 求解，返回统计结果"""
    from dolfinx import fem
    from dolfinx.fem import petsc
    from dolfinx.io import gmshio, VTXWriter
    import ufl

    # ============ 1. 读网格（含物理组 200/300/400/1000） ============
    domain, cell_tags, facet_tags = gmshio.read_from_msh(
        str(msh_path), MPI.COMM_WORLD, gdim=3)

    # ============ 2. 函数空间：二阶三维矢量 ============
    V = fem.functionspace(domain, ("Lagrange", 2, (3,)))

    # ============ 3. 边界条件：拱脚面(400)固支 ============
    base_facets = facet_tags.find(400)
    if base_facets.size == 0:
        raise RuntimeError("find(400) 为空：物理组没贴好，回 geometry/minimal_dome_demo.py 检查")
    dofs = fem.locate_dofs_topological(V, 2, base_facets)
    bc = fem.dirichletbc(fem.Constant(domain, (0.0, 0.0, 0.0)), dofs, V)

    # ============ 4. 材料：E/ν + 分层密度（继承 C2：上轻下重） ============
    E = fem.Constant(domain, E_value)
    nu = fem.Constant(domain, NU_CONCRETE)
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    eps_sh = fem.Constant(domain, eps_sh_value)   # 干缩量级，恒为正（收缩）

    W_rho = fem.functionspace(domain, ("Lagrange", 1))
    if density_mode == "layered":
        # P-02/P-04 修法：callable 插值；z>=0 是上半部 → 轻 1350
        rho = fem.Function(W_rho)

        def rho_fill(x):
            return np.where(x[2] >= 0.0, DENSITY_STEPS[0][1], DENSITY_STEPS[-1][1])

        rho.interpolate(rho_fill)
    else:
        rho = fem.Constant(domain, DENSITY_STEPS[-1][1])
    g = fem.Constant(domain, G)
    b = ufl.as_vector([0.0, 0.0, -rho * g])

    # ============ 5. 弱形式（含干缩项，符号见文件头推导） ============
    u = ufl.TrialFunction(V)
    v = ufl.TestFunction(V)
    I3 = ufl.Identity(3)

    def epsilon(w):
        return ufl.sym(ufl.grad(w))

    # 左端：与 C1 完全一致（线弹性刚度）
    a = ufl.inner(lam * ufl.tr(epsilon(u)) * I3 + 2 * mu * epsilon(u),
                  epsilon(v)) * ufl.dx

    # 右端：自重（可选）+ 干缩等效荷载（可选）
    # 干缩项 = -ε_sh(3λ+2μ)·div(v)：收缩被约束 → 拉应力 → 等价「负体积力」进右端
    if load == "sw":
        L = ufl.dot(b, v) * ufl.dx
    elif load == "sh":
        L = -eps_sh * (3 * lam + 2 * mu) * ufl.div(v) * ufl.dx
    elif load == "sw+sh":
        L = (ufl.dot(b, v) - eps_sh * (3 * lam + 2 * mu) * ufl.div(v)) * ufl.dx
    else:
        raise ValueError(f"--load 只支持 sw / sh / sw+sh，收到：{load}")

    # ============ 6. 求解（cg + BoomerAMG，与 C1/C2+ 同配置） ============
    problem = petsc.LinearProblem(
        a, L, bcs=[bc],
        petsc_options={"ksp_type": "cg", "pc_type": "hypre",
                       "pc_hypre_type": "boomeramg", "ksp_rtol": 1e-8},
    )
    uh = problem.solve()

    # ============ 7. 位移统计 ============
    u_mag = np.sqrt(np.sum(uh.x.array.reshape(-1, 3) ** 2, axis=1))
    u_max_mm = u_mag.max() * 1000.0

    # ============ 8. 应力后处理（含干缩的完整应力） ============
    # 后处理应力必须与荷载一致：sw 档不含干缩项。否则全体主应力被抬升
    # ε_sh(3λ+2μ)=3Kε_sh≈0.182 MPa（2026-08-17 首跑 sw 档 σ1 0.0562→0.36 假象，P-07c）
    def sigma_el(w):
        return lam * ufl.tr(epsilon(w)) * I3 + 2 * mu * epsilon(w)

    def sigma_full(w):
        eps_mech = epsilon(w) + eps_sh * I3   # 收缩：ε_free=-ε_sh·I → ε_mech=ε_tot+ε_sh·I
        return lam * ufl.tr(eps_mech) * I3 + 2 * mu * eps_mech

    sigma_post = sigma_el if load == "sw" else sigma_full

    # P-05 修：dolfinx 0.8 Expression 构造 (expr, X)
    S = fem.functionspace(domain, ("Lagrange", 1, (3, 3)))
    sigma_h = fem.Function(S)
    X = S.element.interpolation_points()      # (N,3) 求值点
    sigma_h.interpolate(fem.Expression(sigma_post(uh), X))

    sigma_nodes = sigma_h.x.array.reshape(-1, 3, 3)
    principal = np.linalg.eigvalsh(sigma_nodes)   # 升序：最后一列 = σ1，第一列 = σ3
    s1 = principal[:, -1]                         # σ1 (Pa)
    s1_max = s1.max() / 1e6
    s3_min = principal[:, 0].min() / 1e6

    # ============ 9. 名义开裂区与 57° 口径对比 ============
    # 取 S 空间 dof 坐标（与 sigma_h.x.array 同布局：每点 9 分量连续），
    # reshape(-1,9,3)[:,0,:] 得到每点坐标 → 与 s1 逐点对齐
    # dolfinx 0.8 实测：tabulate_dof_coordinates 对张量空间按点去重返回 (N,3)，
    # 不是 9 倍重复布局（2026-08-17 首跑断言炸了才知道，P-07b 教训）
    Xg = np.asarray(S.tabulate_dof_coordinates())
    n_pts = sigma_nodes.shape[0]                  # 应力点数量（=sigma 数组行数）
    if Xg.ndim == 2 and Xg.shape[0] == n_pts:
        Xp = Xg                                   # 已按点去重：(N,3)
    elif Xg.ndim == 2 and Xg.shape[0] == 9 * n_pts:
        Xp = Xg.reshape(-1, 9, 3)[:, 0, :]        # 9 分量重复布局兜底：(9N,3)
    else:
        raise RuntimeError(f"坐标布局未识别：Xg.shape={Xg.shape} vs 应力点 {n_pts}")
    r = np.linalg.norm(Xp, axis=1)
    phi_z_deg = np.degrees(np.arccos(np.clip(Xp[:, 2] / r, -1.0, 1.0)))
    angle_from_spring = 90.0 - phi_z_deg          # 拱脚(赤道)=0°，向天窗增大
    crack_idx = s1 > FT_CONCRETE                  # σ1 超抗拉线的「名义开裂」点
    crack_frac = float(np.mean(crack_idx)) * 100.0
    crack_top_deg = float(angle_from_spring[crack_idx].max()) if crack_idx.any() else 0.0

    # ---- 口径对齐（2026-08-17）：最大连通裂缝簇顶端——锚点不是拱脚（本模型
    #      拱脚带无藻井不裂，裂缝从最底层藻井角起），而是全场最大的连通裂缝簇，
    #      报其顶端角；孤立尖角散点（74° 虚高来源）被连通性自然剔除 ----
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
            # 全连通域分解：找最大裂缝簇
            unvisited = np.where(crack_idx)[0]
            best_top = 0.0
            best_size = 0
            seen = np.zeros(nv, dtype=bool)
            for s in unvisited:
                if seen[s]:
                    continue
                # BFS 本簇
                dq = deque([s])
                seen[s] = True
                comp = []
                while dq:
                    a = dq.popleft()
                    comp.append(a)
                    for b in adj[a]:
                        if crack_idx[b] and not seen[b]:
                            seen[b] = True
                            dq.append(b)
                if len(comp) > best_size:
                    best_size = len(comp)
                    best_top = float(angle_from_spring[comp].max())
            crack_conn_deg = best_top

    # ---- 环向拉→压转变纬度（57° 假说核心量：裂缝止于环向转压处） ----
    # σ_θθ = e_θ·σ·e_θ，e_θ=(-sinθ,cosθ,0)；按 1° 纬度带取 σ_θθ 均值，
    # 转压纬度 = 最高「均值受拉」的带（理论裂缝屏障）
    theta_pts = np.arctan2(Xp[:, 1], Xp[:, 0])
    e_th = np.stack([-np.sin(theta_pts), np.cos(theta_pts),
                     np.zeros_like(theta_pts)], axis=1)
    s_theta = np.einsum("ni,nij,nj->n", e_th, sigma_nodes, e_th)
    band = np.clip(np.floor(angle_from_spring).astype(int), 0, 89)
    hoop_transition_deg = 0.0
    for k in range(90):
        m = band == k
        if m.sum() > 10 and s_theta[m].mean() > 0.0:
            hoop_transition_deg = float(k + 1)
    crack_hoop_top_deg = hoop_transition_deg

    # ============ 10. 导出（PyVista 用） ============
    # P-06 修：dolfinx 0.8 VTXWriter 同元素类型分导
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"c4_{out_tag}_u.bp"), [uh]) as w:
        w.write(0)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"c4_{out_tag}_sigma.bp"), [sigma_h]) as w:
        w.write(0)

    return {
        "load": load,
        "dof": V.dofmap.index_map.size_global * 3,   # 矢量空间单分量块尺寸 ×3 = 总自由度
        "u_max_mm": u_max_mm,
        "s1_max_MPa": s1_max,
        "s3_min_MPa": s3_min,
        "crack_frac_pct": crack_frac,
        "crack_top_deg": crack_top_deg,
        "crack_conn_deg": crack_conn_deg,
        "hoop_transition_deg": crack_hoop_top_deg,
    }


def main():
    parser = argparse.ArgumentParser(description="C4 穹顶干缩线弹性（热应变类比）")
    parser.add_argument("--load", choices=["sw", "sh", "sw+sh"], default="sw+sh",
                        help="sw=自重 / sh=干缩 / sw+sh=自重+干缩（默认）")
    parser.add_argument("--mesh", default="c0_shell_groups.msh",
                        help="MESH_DIR 下的网格文件名（如 c0_shell_groups_1m.msh）")
    parser.add_argument("--e", type=float, default=None, help="E (Pa)，缺省用 params.E_CONCRETE")
    parser.add_argument("--eps-sh", type=float, default=EPS_SHRINKAGE,
                        help=f"干缩应变量级（默认 params.EPS_SHRINKAGE={EPS_SHRINKAGE:.2e}）")
    parser.add_argument("--density", choices=["single", "layered"], default="layered",
                        help="single=C1 单层 1600；layered=C2 两层 1350/1600（默认）")
    args = parser.parse_args()

    msh_path = MESH_DIR / args.mesh
    if not msh_path.exists():
        raise FileNotFoundError(f"网格不存在：{msh_path}，先跑 geometry/minimal_dome_demo.py")

    e_val = args.e if args.e is not None else E_CONCRETE
    mesh_tag = msh_path.stem.replace("c0_shell_groups", "m").replace("_", "")
    dens_tag = "l" if args.density == "layered" else "s"
    out_tag = f"{mesh_tag}{dens_tag}_{args.load.replace('+', 'p')}_E{e_val / 1e9:.1f}_sh{args.eps_sh:.2e}"

    print(f"网格: {args.mesh} | 荷载: {args.load} | E: {e_val / 1e9:.1f} GPa | "
          f"ε_sh: {args.eps_sh:.2e}")
    r = solve_case(args.load, msh_path, out_tag, e_val, args.eps_sh,
                   density_mode=args.density)

    print(f"\n===== C4 结果（{r['load']}） =====")
    print(f"自由度 = {r['dof']}")
    print(f"最大位移 = {r['u_max_mm']:.4f} mm")
    print(f"最大主应力 σ1 = {r['s1_max_MPa']:.4f} MPa")
    print(f"最小主应力 σ3 = {r['s3_min_MPa']:.4f} MPa")
    print(f"名义开裂区（σ1>ft）占比 = {r['crack_frac_pct']:.2f}%")
    print(f"开裂区顶端角度（拱脚=0° 起算）= {r['crack_top_deg']:.1f}°  "
          f"（历史实测 ~57°，Masi 2018）")
    print(f"连通裂缝带顶端（口径对齐，剔除孤立尖角）= {r['crack_conn_deg']:.1f}°")
    print(f"环向转压纬度（σ_θθ 最高受拉带）= {r['hoop_transition_deg']:.1f}°  "
          f"（理论裂缝屏障，均匀半球 ~52°，Flügge）")


if __name__ == "__main__":
    main()

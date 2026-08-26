#!/usr/bin/env python3
"""
C1：球壳自重线弹性（文档5 第 9 章落地版）

流程：读 c0_shell_groups.msh（含物理组 200/300/400/1000）
      → 拱脚面(400)固支 → 自重 → 求解 → 位移/应力统计 → 导出 .bp

用法（WSL）：
  python fem_solver/c1_dome_selfweight.py            # 跑 E 敏感性三档（方案 A）
  python fem_solver/c1_dome_selfweight.py --e 14.8e9 # 只跑指定 E（Pa）

2026-08-15 写：文档5 §9.3 落地 + E 敏感性扫描（params.E_SENSITIVITY）；
拱脚=球底南极面（简化约束，真实拱脚 C2 鼓座引入）。
"""
import sys
import argparse
from pathlib import Path

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import (
    NU_CONCRETE, DENSITY_STEPS, G, E_CONCRETE, E_SENSITIVITY,
    MESH_DIR, RESULT_DIR,
)


def solve_case(E_value: float, msh_path: Path, out_tag: str, density_mode: str = "single") -> dict:
    """单个 E 值的 C1 求解，返回统计结果"""
    from dolfinx import fem, mesh  # noqa: F401 (mesh 用于网格对象)
    from dolfinx.fem import petsc
    from dolfinx.io import gmshio, VTXWriter
    import ufl

    # ============ 1. 读入网格（含物理组） ============
    domain, cell_tags, facet_tags = gmshio.read_from_msh(
        str(msh_path), MPI.COMM_WORLD, gdim=3,
    )
    cell_ids = np.unique(cell_tags.values)
    facet_ids = np.unique(facet_tags.values)
    print(f"体物理组: {cell_ids}  面物理组: {facet_ids}")

    # ============ 2. 函数空间：二阶三维矢量 ============
    V = fem.functionspace(domain, ("Lagrange", 2, (3,)))

    # ============ 3. 边界条件：拱脚面(400)固支 ============
    base_facets = facet_tags.find(400)
    if base_facets.size == 0:
        raise RuntimeError("find(400) 为空：物理组没贴好，回 geometry/minimal_dome_demo.py 检查")
    dofs = fem.locate_dofs_topological(V, 2, base_facets)
    bc = fem.dirichletbc(fem.Constant(domain, (0.0, 0.0, 0.0)), dofs, V)

    # ============ 4. 材料参数（E 由参数传入） ============
    E = fem.Constant(domain, E_value)
    nu = fem.Constant(domain, NU_CONCRETE)
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))

    # ============ 5. 自重 ============
    g = fem.Constant(domain, G)
    if density_mode == "layered":
        # C2：两层密度（上轻下重，z>=0 分界）
        # P-02/P-04 修法：callable 插值（ufl.ge 吃 numpy 数组会报错；方向 z>=0 是上半部→轻）
        W_rho = fem.functionspace(domain, ("Lagrange", 1))
        rho = fem.Function(W_rho)

        def rho_fill(x):  # x: (3, N) 坐标数组
            return np.where(x[2] >= 0.0, DENSITY_STEPS[0][1], DENSITY_STEPS[-1][1])

        rho.interpolate(rho_fill)
    else:
        # C1：单层下区密度 1600（简化，分层留给 C2）
        rho = fem.Constant(domain, DENSITY_STEPS[-1][1])
    b = ufl.as_vector([0.0, 0.0, -rho * g])

    # ============ 6. 弱形式 ============
    u = ufl.TrialFunction(V)
    v = ufl.TestFunction(V)

    def epsilon(w):
        return ufl.sym(ufl.grad(w))

    def sigma(w):
        return lam * ufl.tr(epsilon(w)) * ufl.Identity(3) + 2 * mu * epsilon(w)

    a = ufl.inner(sigma(u), epsilon(v)) * ufl.dx
    L = ufl.dot(b, v) * ufl.dx

    # ============ 7. 求解 ============
    # 1.0m 档 ~97 万 DOF：cg + BoomerAMG 迭代法（lu 直接法内存会爆）
    problem = petsc.LinearProblem(
        a, L, bcs=[bc],
        petsc_options={
            "ksp_type": "cg",
            "pc_type": "hypre",
            "pc_hypre_type": "boomeramg",
            "ksp_rtol": 1e-8,
            "ksp_monitor": None,
        },
    )
    uh = problem.solve()

    # ============ 8. 位移统计 ============
    u_mag = np.sqrt(np.sum(uh.x.array.reshape(-1, 3) ** 2, axis=1))
    u_max_mm = u_mag.max() * 1000.0

    # ============ 9. 应力后处理 ============
    # P-05 修：dolfinx 0.8 的 Expression 构造为 (expr, X)，X=求值点坐标 (3,N)；
    # 文档5 §8.3 的 (expr, W.element) 是旧 API
    S = fem.functionspace(domain, ("Lagrange", 1, (3, 3)))
    sigma_h = fem.Function(S)
    X = S.element.interpolation_points()      # (N,3)：元素插值点（Expression 求值点）
    sigma_expr = fem.Expression(sigma(uh), X)
    sigma_h.interpolate(sigma_expr)

    sigma_nodes = sigma_h.x.array.reshape(-1, 3, 3)
    principal = np.linalg.eigvalsh(sigma_nodes)
    s1_max = principal[:, -1].max() / 1e6
    s3_min = principal[:, 0].min() / 1e6

    # ============ 10. 导出（PyVista 用） ============
    # P-06 修：dolfinx 0.8 VTXWriter 要求同元素类型，位移/应力分开导出
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"c1_{out_tag}_u.bp"), [uh]) as w:
        w.write(0)
    with VTXWriter(domain.comm, str(RESULT_DIR / f"c1_{out_tag}_sigma.bp"), [sigma_h]) as w:
        w.write(0)

    return {
        "E_GPa": E_value / 1e9,
        "dof": V.dofmap.index_map.size_global,
        "u_max_mm": u_max_mm,
        "s1_max_MPa": s1_max,
        "s3_min_MPa": s3_min,
    }


def main():
    parser = argparse.ArgumentParser(description="C1 球壳自重线弹性")
    parser.add_argument("--e", type=float, default=None, help="E (Pa)，缺省跑 E_SENSITIVITY 三档")
    parser.add_argument("--mesh", default="c0_shell_groups.msh",
                        help="MESH_DIR 下的网格文件名（如 c0_shell_groups_1m.msh）")
    parser.add_argument("--density", choices=["single", "layered"], default="single",
                        help="single=C1 单层 1600；layered=C2 两层 1350/1600（z>=0 分界）")
    args = parser.parse_args()

    msh_path = MESH_DIR / args.mesh
    if not msh_path.exists():
        raise FileNotFoundError(f"网格不存在：{msh_path}，先跑 geometry/minimal_dome_demo.py")

    if args.e is not None:
        cases = [args.e]
    else:
        cases = list(E_SENSITIVITY)

    print(f"E 档位: {[c / 1e9 for c in cases]} GPa  |  自由度见各档输出")
    results = []
    for i, e_val in enumerate(cases):
        print(f"\n===== E = {e_val / 1e9:.1f} GPa ({i + 1}/{len(cases)}) =====")
        mesh_tag = msh_path.stem.replace("c0_shell_groups", "m").replace("_", "")  # "m" / "m1m" / "m0p5m"
        dens_tag = "l" if args.density == "layered" else "s"
        r = solve_case(e_val, msh_path, f"{mesh_tag}{dens_tag}_E{e_val / 1e9:.1f}",
                       density_mode=args.density)
        results.append(r)
        print(f"自由度 = {r['dof']}")
        print(f"最大位移 = {r['u_max_mm']:.4f} mm")
        print(f"最大主应力 σ1 = {r['s1_max_MPa']:.4f} MPa")
        print(f"最小主应力 σ3 = {r['s3_min_MPa']:.4f} MPa")

    if len(results) > 1:
        print("\n===== E 敏感性汇总（方案 A） =====")
        print(f"{'E (GPa)':>10} {'自由度':>10} {'u_max (mm)':>14} {'σ1 (MPa)':>12} {'σ3 (MPa)':>12}")
        for r in results:
            print(f"{r['E_GPa']:>10.1f} {r['dof']:>10} {r['u_max_mm']:>14.4f} "
                  f"{r['s1_max_MPa']:>12.4f} {r['s3_min_MPa']:>12.4f}")
        # 理论校验：线弹性自重下 σ 与 E 无关（静定），位移 ∝ 1/E
        if len(results) >= 2:
            r0, r1 = results[0], results[1]
            print(f"\n理论校验：σ1 应基本不变（{r0['s1_max_MPa']:.4f} vs {r1['s1_max_MPa']:.4f} MPa）")
            ratio = (r1["u_max_mm"] * r1["E_GPa"]) / (r0["u_max_mm"] * r0["E_GPa"])
            print(f"位移×E 应守恒：u_max×E 比值 = {ratio:.3f}（≈1 即验证通过）")

    print("\n✅ C1 完成，结果在 output/results/c1_E*.bp")


if __name__ == "__main__":
    main()

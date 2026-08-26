#!/usr/bin/env python3
"""
网格无关性误差估计（Richardson 外推）

用法：
  python tools/estimate_grid_error.py --coarse 0.8380 --fine <1.0m档u_max> --ratio 2 --p 2
  （缺省用内置的 2.0m 基准数据，只需给 --fine）

原理：
  网格尺寸 h → h/2 时，误差 e_h = C·h^p（p=收敛阶）。
  Richardson 外推：u_exact ≈ u_fine + (u_fine - u_coarse) / (r^p - 1)
  其中 r = h_coarse / h_fine（网格加密比，本项目 2.0m→1.0m 为 2）。
  P2 位移：理论阶 p=2（H1 范数）/ p=3（L2 范数）；点值常取 2~3 之间，
  因此同时给出 p=2 与 p=3 两种估计作为误差上下界参考。
"""
import argparse

# 2026-08-15 实测（2.0m 档，E=14.8 GPa，方案 A）
BASELINE = {
    "u_max_mm": 0.8380,
    "s1_MPa": 0.0666,
    "s3_MPa": -0.7991,
}


def richardson(coarse: float, fine: float, r: float, p: int) -> dict:
    diff = fine - coarse
    exact = fine + diff / (r ** p - 1)
    err_est = abs(diff) / (r ** p - 1)
    rel_err = err_est / abs(exact) * 100 if exact else 0.0
    return {
        "coarse": coarse,
        "fine": fine,
        "diff": diff,
        "exact_extrapolated": exact,
        "abs_err_est": err_est,
        "rel_err_pct": rel_err,
    }


def main():
    parser = argparse.ArgumentParser(description="Richardson 网格误差估计")
    parser.add_argument("--fine", type=float, required=True, help="1.0m 档 u_max (mm)")
    parser.add_argument("--coarse", type=float, default=BASELINE["u_max_mm"],
                        help="2.0m 档 u_max (mm)，缺省用内置基准")
    parser.add_argument("--ratio", type=float, default=2.0, help="网格加密比")
    parser.add_argument("--s1-fine", type=float, default=None, help="1.0m 档 σ1 (MPa)，缺省跳过")
    args = parser.parse_args()

    print("===== 网格无关性 · Richardson 外推（E=14.8 GPa） =====")
    print(f"{'h (m)':>6} | {'u_max (mm)':>12}")
    print(f"{'2.0':>6} | {args.coarse:>12.4f}")
    print(f"{'1.0':>6} | {args.fine:>12.4f}")
    print()

    for p in (2, 3):
        est = richardson(args.coarse, args.fine, args.ratio, p)
        print(f"[p={p} 假设] 外推精确值 = {est['exact_extrapolated']:.4f} mm | "
              f"误差估计 = {est['abs_err_est']:.4f} mm ({est['rel_err_pct']:.2f}%)")

    # 两档相对变化（工程常用直觉指标）
    rel_change = abs(args.fine - args.coarse) / abs(args.coarse) * 100
    print(f"\n两档相对变化 = {rel_change:.2f}%（<2% 通常认为网格已收敛）")

    if args.s1_fine is not None:
        s1_change = abs(args.s1_fine - BASELINE["s1_MPa"])
        print(f"σ1: 2.0m={BASELINE['s1_MPa']:.4f} MPa → 1.0m={args.s1_fine:.4f} MPa "
              f"(变化 {s1_change:.4f} MPa)")
    else:
        print("（未提供 1.0m 档 σ1，应力对比跳过）")


if __name__ == "__main__":
    main()

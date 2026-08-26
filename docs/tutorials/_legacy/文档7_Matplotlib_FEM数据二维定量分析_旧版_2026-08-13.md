# 万神殿穹顶三维FEM重构 · 文档7 · Matplotlib FEM数据二维定量分析

> **定位**：PyVista 负责三维云图，Matplotlib 负责二维定量曲线——子午线应力分布、双模型对比、网格收敛曲线等论文级图表。
> **前提**：已完成文档5（FEniCSx 求解）和文档6（PyVista 可视化），有 NumPy/CSV 格式的仿真数据。
> **风格**：所有绑图代码配论文级规范（坐标轴标签、单位、图例、字体）。

---

## 目录

1. [工具定位：Matplotlib 在本项目中的角色](#1-工具定位matplotlib-在本项目中的角色)
2. [🟢 从 CSV/NumPy 读取仿真数据](#2-从-csvnumpy-读取仿真数据)
3. [🟡 沿子午线应力分布曲线（核心定量图）](#3-沿子午线应力分布曲线核心定量图)
4. [🟡 双模型对比曲线（C1 vs C2 / 新旧对比）](#4-双模型对比曲线c1-vs-c2--新旧对比)
5. [🟡 网格收敛性曲线](#5-网格收敛性曲线)
6. [🟡 拱脚推力对比柱状图](#6-拱脚推力对比柱状图)
7. [🟡 密度梯度分布图](#7-密度梯度分布图)
8. [🟡 论文级图片规范化](#8-论文级图片规范化)
9. [📦 完整绑图脚本](#9-完整绑图脚本)
10. [Matplotlib 审核自查清单](#10-matplotlib-审核自查清单)

---

## 1. 工具定位：Matplotlib 在本项目中的角色

PyVista 画「三维的云图」——你看应力在穹顶表面怎么分布。

Matplotlib 画「二维的曲线」——你定量回答：
- 环向应力沿子午线怎么变化？
- 加鼓座后最大拉应力降低了多少？
- 网格从 5 万加到 80 万，结果收敛了吗？

**这两种图互补。三维云图给直觉，二维曲线给数据。**

---

## 2. 🟢 从 CSV/NumPy 读取仿真数据

### 2.1 仿真数据导出规范（统一格式）

本项目推荐将沿子午线的应力数据导出为 CSV：

```csv
# meridional_stress_C2.csv
phi_deg,sigma_theta_kPa,sigma_phi_kPa,sigma_1_kPa,u_r_mm
0.0,150.2,-520.3,150.2,0.12
5.0,145.8,-510.1,145.8,0.25
...
90.0,-45.3,-890.5,-45.3,0.00
```

### 2.2 读取数据

```python
import numpy as np
import pandas as pd
from pathlib import Path

def load_meridional_data(case_name):
    """
    加载沿子午线的仿真数据。

    Args:
        case_name: 算例名称，如 "C1", "C2", "C4"

    Returns:
        DataFrame 包含 phi_deg, sigma_theta, sigma_phi, sigma_1, u_r
    """
    filepath = Path(f"output/data/meridional_stress_{case_name}.csv")

    if not filepath.exists():
        raise FileNotFoundError(
            f"找不到数据文件: {filepath}\n"
            f"请先运行 {case_name} 算例并导出沿子午线的数据。"
        )

    df = pd.read_csv(filepath)
    return df
```

### 2.3 导出功能

```python
def export_meridional_data(phi_deg, sigma_theta, sigma_phi, sigma_1, u_r,
                           case_name, output_dir="output/data"):
    """
    将沿子午线的 FEM 结果导出为 CSV。

    Args:
        phi_deg: 子午角度 (°)，从 Oculus 到拱脚
        sigma_theta: 环向应力 [kPa]
        sigma_phi: 子午向应力 [kPa]
        sigma_1: 第一主应力 [kPa]
        u_r: 径向位移 [mm]
        case_name: 算例名称
    """
    from pathlib import Path
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({
        "phi_deg": phi_deg,
        "sigma_theta_kPa": sigma_theta,
        "sigma_phi_kPa": sigma_phi,
        "sigma_1_kPa": sigma_1,
        "u_r_mm": u_r,
    })

    filepath = output_dir / f"meridional_stress_{case_name}.csv"
    df.to_csv(filepath, index=False)
    print(f"数据已导出: {filepath}")
```

---

## 3. 🟡 沿子午线应力分布曲线（核心定量图）

这是本项目**最重要的二维图**——展示了从 Oculus（φ=0°）到拱脚（φ=90°），环向应力和子午向应力如何变化。

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_meridional_stress(df, case_name, output_path=None):
    """
    绘制沿子午线的环向应力和子午向应力分布。

    Args:
        df: DataFrame，包含 phi_deg, sigma_theta_kPa, sigma_phi_kPa
        case_name: 算例名称（用于标题）
        output_path: 保存路径（None 则显示）
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # 环向应力 σ_θθ
    ax.plot(df["phi_deg"], df["sigma_theta_kPa"],
            "r-", linewidth=2, label=r"$\sigma_{\theta\theta}$ (环向)")

    # 子午向应力 σ_φφ
    ax.plot(df["phi_deg"], df["sigma_phi_kPa"],
            "b-", linewidth=2, label=r"$\sigma_{\phi\phi}$ (子午向)")

    # 零线
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=1, alpha=0.7)

    # 抗拉强度线
    ax.axhline(y=80, color="red", linestyle=":", linewidth=1.5, alpha=0.5,
               label=r"$f_t$ = 80 kPa (抗拉强度)")

    # 标注
    ax.set_xlabel(r"子午角 $\phi$ (°)", fontsize=13)
    ax.set_ylabel("应力 (kPa)", fontsize=13)
    ax.set_title(f"万神殿穹顶 · 沿子午线应力分布 ({case_name})", fontsize=14)
    ax.legend(fontsize=11, loc="lower left")
    ax.grid(True, alpha=0.3)

    # 轴范围
    ax.set_xlim(0, 90)
    ax.set_ylim(-2000, 500)   # 根据实际数据调整

    # 标注关键区域
    ax.annotate("环向受拉\n(开裂风险)",
                xy=(75, 100), xytext=(50, 200),
                arrowprops=dict(arrowstyle="->", color="red"),
                fontsize=10, color="red")

    ax.annotate("环向受压\n(安全)",
                xy=(15, -300), xytext=(20, -800),
                arrowprops=dict(arrowstyle="->", color="blue"),
                fontsize=10, color="blue")

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"图片已保存: {output_path}")
    else:
        plt.show()

    plt.close()
    return fig
```

---

## 4. 🟡 双模型对比曲线（C1 vs C2 / 新旧对比）

### 4.1 C1 vs C2 环向应力对比

```python
def plot_c1_vs_c2_comparison(df_c1, df_c2, output_path=None):
    """
    C1（纯穹顶+刚性拱脚） vs C2（穹顶+鼓座耦合）环向应力对比。

    这是展示「鼓座约束效应」的核心图表。
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # --- 左图：环向应力对比 ---
    ax1.plot(df_c1["phi_deg"], df_c1["sigma_theta_kPa"],
             "r-", linewidth=2, label="C1: 纯穹顶（刚性拱脚）")
    ax1.plot(df_c2["phi_deg"], df_c2["sigma_theta_kPa"],
             "b--", linewidth=2, label="C2: 穹顶+鼓座（粘结）")

    ax1.axhline(y=0, color="gray", linestyle="--", linewidth=1)
    ax1.axhline(y=80, color="red", linestyle=":", linewidth=1, alpha=0.5)

    ax1.set_xlabel(r"子午角 $\phi$ (°)", fontsize=12)
    ax1.set_ylabel(r"环向应力 $\sigma_{\theta\theta}$ (kPa)", fontsize=12)
    ax1.set_title("环向应力分布对比", fontsize=13)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # --- 右图：差异曲线 ---
    diff = df_c2["sigma_theta_kPa"] - df_c1["sigma_theta_kPa"]

    ax2.plot(df_c1["phi_deg"], diff, "g-", linewidth=2)
    ax2.fill_between(df_c1["phi_deg"], 0, diff,
                     where=(diff < 0), color="green", alpha=0.2,
                     label="C2 拉应力更低（鼓座释放约束）")
    ax2.fill_between(df_c1["phi_deg"], 0, diff,
                     where=(diff > 0), color="red", alpha=0.2,
                     label="C2 拉应力更高（异常）")

    ax2.axhline(y=0, color="gray", linestyle="--", linewidth=1)
    ax2.set_xlabel(r"子午角 $\phi$ (°)", fontsize=12)
    ax2.set_ylabel(r"$\Delta\sigma_{\theta\theta}$ (kPa)", fontsize=12)
    ax2.set_title("C2 − C1 环向应力差异", fontsize=13)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    plt.suptitle("万神殿穹顶 · 鼓座约束效应量化", fontsize=14, y=1.02)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
    else:
        plt.show()
    plt.close()
```

### 4.2 V1.0 vs V2.0 新旧模型对比

```python
def plot_v1_vs_v2_comparison(df_v2_c1, v1_phi, v1_sigma_theta,
                              output_path=None):
    """
    V1.0（一维薄膜解） vs V2.0 C1（三维FEM，同工况）对比。

    展示三维效应如何修正一维薄膜解的绝对值。
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # V1.0 结果
    ax.plot(v1_phi, v1_sigma_theta, "gray", linewidth=2,
            linestyle="--", alpha=0.7,
            label="V1.0: 一维薄膜解（C++）")

    # V2.0 C1（同工况：纯穹顶+刚性拱脚）
    ax.plot(df_v2_c1["phi_deg"], df_v2_c1["sigma_theta_kPa"],
            "b-", linewidth=2.5,
            label="V2.0: 三维FEM C1（Gmsh+FEniCSx）")

    # 标注系统性偏移
    mid_phi = 45
    y_v1 = np.interp(mid_phi, v1_phi, v1_sigma_theta)
    y_v2 = np.interp(mid_phi, df_v2_c1["phi_deg"],
                     df_v2_c1["sigma_theta_kPa"])

    ax.annotate(f"", xy=(mid_phi, y_v2), xytext=(mid_phi, y_v1),
                arrowprops=dict(arrowstyle="<->", color="black", lw=2))
    ax.text(mid_phi + 2, (y_v1 + y_v2) / 2,
            f"三维效应\n修正~{abs((y_v1-y_v2)/y_v1*100):.0f}%",
            fontsize=10, va="center")

    ax.axhline(y=0, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel(r"子午角 $\phi$ (°)", fontsize=13)
    ax.set_ylabel("环向应力 (kPa)", fontsize=13)
    ax.set_title("万神殿穹顶 · V1.0 vs V2.0 模型对比（C1同工况）", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
    else:
        plt.show()
    plt.close()
```

---

## 5. 🟡 网格收敛性曲线

```python
def plot_mesh_convergence(mesh_sizes, key_results, labels, output_path=None):
    """
    绘制网格收敛性曲线。

    这是 FEM 论文的「标配」图——证明你的结果不依赖网格粗细。

    Args:
        mesh_sizes: 网格尺寸列表（如 [2.0, 1.0, 0.5, 0.25] m）
        key_results: dict of {label: [values]}，如
                     {"max_displacement_mm": [5.2, 5.8, 6.1, 6.2]}
        labels: 图例标签
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ["blue", "red", "green", "orange"]
    markers = ["o", "s", "^", "D"]

    for (name, values), color, marker in zip(key_results.items(), colors, markers):
        ax.plot(mesh_sizes, values, f"{color}-{marker}",
                linewidth=2, markersize=8, label=name)

    ax.set_xlabel("网格尺寸 (m)", fontsize=13)
    ax.set_ylabel("关键结果", fontsize=13)
    ax.set_title("万神殿穹顶 C2 · 网格收敛性分析", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    # 对数坐标（通常网格收敛用对数坐标更清晰）
    ax.set_xscale("log")

    # 反转向（网格越细 = 越往左）
    ax.invert_xaxis()

    # 标注收敛区域
    ax.axvspan(0.2, 0.5, alpha=0.1, color="green",
               label="收敛区域（变化 < 3%）")

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
```

---

## 6. 🟡 拱脚推力对比柱状图

```python
def plot_thrust_comparison(cases, thrusts, output_path=None):
    """
    各算例的拱脚水平推力对比柱状图。

    Args:
        cases: 算例名称列表，如 ["C1", "C2", "C4"]
        thrusts: 水平推力列表 [kN]
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    colors = ["#E74C3C", "#3498DB", "#2ECC71", "#F39C12"]

    bars = ax.bar(cases, thrusts, color=colors[:len(cases)],
                  edgecolor="black", linewidth=0.5, width=0.5)

    # 数值标注
    for bar, thrust in zip(bars, thrusts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f"{thrust:.1f} kN",
                ha="center", va="bottom", fontsize=11, fontweight="bold")

    # 变化百分比标注
    if len(thrusts) >= 2:
        for i in range(1, len(thrusts)):
            change = (thrusts[i] - thrusts[0]) / thrusts[0] * 100
            ax.annotate(f"{change:+.1f}%",
                        xy=(i, thrusts[i]),
                        xytext=(i, thrusts[i] + max(thrusts)*0.05),
                        fontsize=10, color="red" if change > 0 else "green",
                        ha="center")

    ax.set_ylabel("水平推力 (kN)", fontsize=13)
    ax.set_title("万神殿穹顶 · 拱脚水平推力对比", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
```

---

## 7. 🟡 密度梯度分布图

```python
def plot_density_gradient(output_path=None):
    """
    绘制万神殿穹顶的密度梯度分布图。

    展示从顶部轻质浮石（1350 kg/m³）到底部致密玄武岩（2100 kg/m³）的梯度。
    """
    phi_deg = np.linspace(0, 90, 200)

    def density_at(phi_deg):
        if phi_deg <= 12:
            return 1350
        elif phi_deg <= 25:
            return 1650
        elif phi_deg <= 40:
            return 1900
        else:
            return 2100

    rho = np.array([density_at(p) for p in phi_deg])

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.fill_between(phi_deg, 0, rho, alpha=0.3, color="orange")
    ax.plot(phi_deg, rho, "brown", linewidth=2.5)

    # 标注各区
    ax.axvline(x=12, color="gray", linestyle="--", linewidth=1)
    ax.axvline(x=25, color="gray", linestyle="--", linewidth=1)
    ax.axvline(x=40, color="gray", linestyle="--", linewidth=1)

    ax.text(6, 1400, "轻质浮石\n1350 kg/m³", ha="center", fontsize=10)
    ax.text(18.5, 1700, "混合骨料\n~1650 kg/m³", ha="center", fontsize=10)
    ax.text(32.5, 1950, "较重骨料\n~1900 kg/m³", ha="center", fontsize=10)
    ax.text(65, 2150, "致密玄武岩\n2100 kg/m³", ha="center", fontsize=10)

    ax.set_xlabel(r"子午角 $\phi$ (°)，0°=Oculus, 90°=拱脚", fontsize=12)
    ax.set_ylabel(r"密度 $\rho$ (kg/m³)", fontsize=12)
    ax.set_title("万神殿穹顶 · 古罗马混凝土密度梯度 (Masi et al. 2018)", fontsize=13)
    ax.set_xlim(0, 90)
    ax.set_ylim(1000, 2300)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
```

---

## 8. 🟡 论文级图片规范化

### 8.1 全局样式设置

```python
import matplotlib.pyplot as plt
import matplotlib as mpl

def set_paper_style():
    """
    设置论文级绑图样式。

    特征：
      - 统一的字体大小和族
      - 适配 IEEE/ASME 期刊双栏格式
      - 高 DPI 输出
    """
    plt.rcParams.update({
        # --- 字体 ---
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,

        # --- 图片尺寸 ---
        "figure.figsize": (8, 5),      # 默认（适合 1/2 页宽）
        "figure.dpi": 150,

        # --- 线条 ---
        "lines.linewidth": 1.5,
        "lines.markersize": 6,

        # --- 坐标轴 ---
        "axes.linewidth": 1.0,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",

        # --- 保存 ---
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.format": "png",

        # --- LaTeX（如已安装）---
        "text.usetex": False,   # 如果装了 LaTeX 可以设为 True
    })

def save_figure(fig, filename, formats=["png", "pdf"]):
    """
    保存图片为多种格式。

    PNG 用于插入 Word/PPT，PDF 用于 LaTeX 论文。
    """
    from pathlib import Path
    for fmt in formats:
        path = Path(filename).with_suffix(f".{fmt}")
        fig.savefig(str(path), dpi=300, bbox_inches="tight")
        print(f"  → {path}")
```

### 8.2 坐标轴标签规范

```python
# ✅ 正确示范
ax.set_xlabel(r"子午角 $\phi$ (°)", fontsize=12)
ax.set_ylabel(r"环向应力 $\sigma_{\theta\theta}$ (kPa)", fontsize=12)

# ✅ 带物理含义的标题
ax.set_title("万神殿穹顶 C2 · 沿子午线环向应力分布", fontsize=13)

# ❌ 错误示范
# ax.set_xlabel("x")        # 没有说明是什么
# ax.set_ylabel("y")        # 没有单位
# ax.set_title("Figure 1")  # 没有信息量
```

### 8.3 图例规范

```python
# ✅ 规范图例
ax.legend(
    fontsize=10,
    loc="best",          # 自动选最佳位置
    framealpha=0.8,      # 半透明背景
    edgecolor="black",
    ncol=1,
)

# 或放在图外
ax.legend(
    fontsize=10,
    loc="upper left",
    bbox_to_anchor=(1.02, 1),   # 放在图外右侧
    borderaxespad=0,
)
```

---

## 9. 📦 完整绑图脚本

```python
#!/usr/bin/env python3
"""
万神殿穹顶 · 完整二维分析绑图脚本
==================================
生成全部论文级二维图表。

运行：
  python3 post_process/plot_2d_all.py
"""

import matplotlib
matplotlib.use("Agg")   # 非交互后端（服务器/无GUI环境）

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# ============================================================
# 配置
# ============================================================
OUTPUT_DIR = Path("output/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 论文样式
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "legend.fontsize": 10,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# ============================================================
# 模拟数据生成（实际使用中从 FEM 结果读取）
# ============================================================
def generate_demo_data():
    """生成演示用沿子午线数据"""
    phi = np.linspace(0, 90, 50)

    # C1: 纯穹顶+刚性拱脚（拉应力更大，压应力更小）
    sigma_theta_c1 = 400 * np.exp(-((phi - 75) / 20)**2) - 200
    sigma_phi_c1 = -400 - 200 * np.sin(np.radians(phi))

    # C2: 穹顶+鼓座（拉应力降低 ~30%）
    sigma_theta_c2 = sigma_theta_c1 * 0.7   # 鼓座释放约束
    sigma_phi_c2 = sigma_phi_c1 * 0.9       # 略小的压应力

    df_c1 = pd.DataFrame({
        "phi_deg": phi,
        "sigma_theta_kPa": sigma_theta_c1,
        "sigma_phi_kPa": sigma_phi_c1,
    })
    df_c2 = pd.DataFrame({
        "phi_deg": phi,
        "sigma_theta_kPa": sigma_theta_c2,
        "sigma_phi_kPa": sigma_phi_c2,
    })

    return df_c1, df_c2

# ============================================================
# 图1: 沿子午线应力分布
# ============================================================
def fig1_meridional_stress(df, case_name):
    """图1：单算例的沿子午线应力分布"""
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(df["phi_deg"], df["sigma_theta_kPa"], "r-",
            linewidth=2, label=r"$\sigma_{\theta\theta}$ (环向)")
    ax.plot(df["phi_deg"], df["sigma_phi_kPa"], "b-",
            linewidth=2, label=r"$\sigma_{\phi\phi}$ (子午向)")

    ax.axhline(y=0, color="gray", linestyle="--", linewidth=1)
    ax.axhline(y=80, color="red", linestyle=":", linewidth=1.5,
               alpha=0.5, label=r"$f_t$ = 80 kPa")

    ax.set_xlabel(r"子午角 $\phi$ (°)", fontsize=12)
    ax.set_ylabel("应力 (kPa)", fontsize=12)
    ax.set_title(f"万神殿穹顶 · 沿子午线应力分布 ({case_name})", fontsize=13)
    ax.legend(fontsize=10, loc="lower left")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 90)

    output_path = OUTPUT_DIR / f"meridional_stress_{case_name}.png"
    fig.savefig(str(output_path))
    plt.close(fig)
    print(f"  → {output_path}")

# ============================================================
# 图2: C1 vs C2 对比
# ============================================================
def fig2_c1_vs_c2(df_c1, df_c2):
    """图2：C1 vs C2 环向应力对比 + 差异曲线"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # 左：应力对比
    ax1.plot(df_c1["phi_deg"], df_c1["sigma_theta_kPa"],
             "r-", linewidth=2, label="C1: 纯穹顶（刚性拱脚）")
    ax1.plot(df_c2["phi_deg"], df_c2["sigma_theta_kPa"],
             "b--", linewidth=2, label="C2: 穹顶+鼓座（粘结）")
    ax1.axhline(y=0, color="gray", linestyle="--", linewidth=1)
    ax1.axhline(y=80, color="red", linestyle=":", linewidth=1, alpha=0.5)
    ax1.set_xlabel(r"子午角 $\phi$ (°)", fontsize=12)
    ax1.set_ylabel(r"$\sigma_{\theta\theta}$ (kPa)", fontsize=12)
    ax1.set_title("环向应力分布", fontsize=13)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # 右：差异
    diff = df_c2["sigma_theta_kPa"] - df_c1["sigma_theta_kPa"]
    ax2.plot(df_c1["phi_deg"], diff, "g-", linewidth=2)
    ax2.fill_between(df_c1["phi_deg"], 0, diff,
                     where=(diff < 0), color="green", alpha=0.2,
                     label="鼓座释放约束")
    ax2.axhline(y=0, color="gray", linestyle="--", linewidth=1)
    ax2.set_xlabel(r"子午角 $\phi$ (°)", fontsize=12)
    ax2.set_ylabel(r"$\Delta\sigma_{\theta\theta}$ (kPa)", fontsize=12)
    ax2.set_title("C2 − C1 环向应力差异", fontsize=13)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    plt.suptitle("万神殿穹顶 · 鼓座约束效应量化", fontsize=14, y=1.02)
    plt.tight_layout()

    output_path = OUTPUT_DIR / "comparison_C1_vs_C2.png"
    fig.savefig(str(output_path))
    plt.close(fig)
    print(f"  → {output_path}")

# ============================================================
# 图3: 网格收敛性
# ============================================================
def fig3_mesh_convergence():
    """图3：网格收敛性曲线"""
    mesh_sizes = [2.0, 1.5, 1.0, 0.75, 0.5]
    max_disp = [5.2, 5.9, 6.3, 6.5, 6.6]
    max_stress = [320, 350, 375, 388, 392]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(mesh_sizes, max_disp, "bo-", linewidth=2, markersize=8,
            label="最大位移 (mm)")
    ax.plot(mesh_sizes, max_stress, "rs-", linewidth=2, markersize=8,
            label="最大环向拉应力 (kPa)")

    ax.set_xlabel("网格特征尺寸 (m)", fontsize=12)
    ax.set_ylabel("关键结果值", fontsize=12)
    ax.set_title("万神殿穹顶 C2 · 网格收敛性分析", fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xscale("log")
    ax.invert_xaxis()

    ax.axvspan(0.3, 0.8, alpha=0.1, color="green")

    output_path = OUTPUT_DIR / "mesh_convergence.png"
    fig.savefig(str(output_path))
    plt.close(fig)
    print(f"  → {output_path}")

# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60)
    print("  万神殿穹顶 · 二维定量分析绑图")
    print("=" * 60)

    df_c1, df_c2 = generate_demo_data()

    print("\n[1/3] 沿子午线应力分布...")
    fig1_meridional_stress(df_c1, "C1")
    fig1_meridional_stress(df_c2, "C2")

    print("\n[2/3] C1 vs C2 对比...")
    fig2_c1_vs_c2(df_c1, df_c2)

    print("\n[3/3] 网格收敛性...")
    fig3_mesh_convergence()

    print(f"\n{'='*60}")
    print(f"  ✅ 全部图表生成完成！")
    print(f"  输出目录: {OUTPUT_DIR}/")
    for f in sorted(OUTPUT_DIR.glob("*.png")):
        print(f"    - {f.name}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
```

---

## 10. Matplotlib 审核自查清单

- [ ] 所有坐标轴是否标注了物理量名称和单位？
- [ ] 图例是否清晰区分了不同曲线/模型？
- [ ] 应力曲线的零线是否画出（方便判断拉/压）？
- [ ] 抗拉强度 f_t = 80 kPa 是否在图上标出？
- [ ] C1 vs C2 对比图的色标（或线型）是否一致且可区分？
- [ ] 网格收敛性曲线的 X 轴是否使用对数坐标？
- [ ] 所有输出图片的 DPI 是否 ≥ 300（论文要求）？
- [ ] 字体大小是否适合论文排版（通常 8-11 pt）？
- [ ] 图片是否同时保存了 PNG（插入 Word）和 PDF（插入 LaTeX）格式？

---

> 🎉 **恭喜！你已完成全部 8 篇学习材料（文档0～文档7）！**
>
> **下一步**：你是否准备好按照 `pantheon_重构总纲_v2.md` 的阶段一（环境搭建+仓库初始化+工具链验证）进入项目实操阶段？

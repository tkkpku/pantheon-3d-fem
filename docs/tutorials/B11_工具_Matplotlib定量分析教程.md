# 文档7 · Matplotlib FEM 数据二维定量分析（重构版）

> **项目**：万神殿穹顶三维 FEM 重构
> **版本**：v2.0 轮次 1/4（2026-08-13 逐轮重写）
> **前置要求**：文档5 有结果数据；文档6 有三维云图
> **配套环境**：`pantheon-fem`（matplotlib 已装）

---

## 写给你的使用说明（30 秒读完）

三维云图（文档6）回答「**哪里**应力大」，二维曲线（本文档）回答「**多少**、**怎么变**」。

这本教材教你：

1. 从 CSV / NumPy 读仿真数据；
2. 画沿子午线的应力曲线（核心定量图）；
3. 画双模型对比、网格收敛、拱脚推力柱状图；
4. 按论文级规范出图（字号、单位、图例、文件格式）。

原则只有一条：**每一张图都要能放进论文/汇报，独立可读**。

### 🎩 老板版速读（60 秒，Leader 必读）

你不用画图，但验收定量图时检查四件事：

1. **轴标签带单位**（「应力 [MPa]」而不是「y」）；
2. **标题带编号和含义**（「图 3：C1 vs C2 应力对比」）；
3. **收敛图 x 轴反向 + 标注相邻变化率**（Δ < 5% 才算收敛）；
4. **300 dpi / PDF**，对比图坐标范围一致。

不合格退回，不用看代码。

---

## 第 0 章 学习地图

| 章 | 内容 | 难度 | 能力 |
| --- | --- | --- | --- |
| 第 1 章 | Matplotlib 定位 + 第一个图 | 🟢 | 基础 |
| 第 2 章 | 沿子午线应力曲线 | 🟡 | 核心 |
| 第 3 章 | 双模型对比与收敛曲线 | 🟡 | 核心 |
| 第 4 章 | 柱状图与密度分布 | 🟡 | 项目 |
| 第 5 章 | 论文级规范 + 完整案例 | 🔴 | 交付 |
| 附录 | 术语、坑点、审核清单 | 🟢 | 工具 |

---

## 第 1 章 Matplotlib 定位与第一个图

### 1.1 Matplotlib 是干什么的

**Matplotlib 是 Python 最经典的二维绘图库**：画折线图、柱状图、散点图、双 y 轴图。

和 PyVista 的分工：

| 库 | 维度 | 回答的问题 |
| --- | --- | --- |
| PyVista | 三维 | 哪里应力大、变形什么样 |
| Matplotlib | 二维 | 沿某条线怎么变化、两模型差多少 |

### 1.2 核心概念：Figure / Axes

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()   # fig = 整张纸, ax = 图上的坐标系
```

- `fig`（Figure）：整张画纸（可以放多张子图）；
- `ax`（Axes）：纸上的一个坐标系（一张子图）。

**以后所有操作都在 `ax` 上做**：`ax.plot`、`ax.set_xlabel`……

### 1.3 第一个图：读 CSV 画曲线

假设文档5 导出了沿子午线的数据 `meridional_stress_C2.csv`：

```csv
phi_deg,sigma_meridional_MPa
11.7,0.12
20.0,0.31
30.0,0.58
...
```

```python
import matplotlib.pyplot as plt
import numpy as np

# 1. 读数据（numpy 直接读 CSV）
data = np.genfromtxt("output/data/meridional_stress_C2.csv",
                     delimiter=",", skip_header=1)
phi = data[:, 0]       # 第一列：子午角
sigma = data[:, 1]     # 第二列：子午向应力

# 2. 画图
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(phi, sigma, "o-", label="C2")

ax.set_xlabel("子午角 φ [°]")
ax.set_ylabel("子午向应力 [MPa]")
ax.set_title("沿子午线的子午向应力分布")
ax.legend()
ax.grid(True, linestyle="--", alpha=0.5)

fig.tight_layout()
fig.savefig("output/figures/meridional_stress.png", dpi=300)
print("已保存")
```

### 1.4 逐行拆解

| 代码 | 作用 |
| --- | --- |
| `np.genfromtxt(...)` | 读 CSV（跳过表头） |
| `ax.plot(phi, sigma, "o-")` | 画折线+圆点 |
| `ax.set_xlabel/ylabel` | 轴标签（**带单位**） |
| `ax.legend()` | 图例 |
| `ax.grid(...)` | 网格线（虚线、半透明） |
| `fig.tight_layout()` | 自动排版防重叠 |
| `fig.savefig(..., dpi=300)` | 高清保存（论文要求 300 dpi） |

### 1.5 本章小结

1. Matplotlib 画二维定量图，PyVista 画三维云图；
2. `fig` 是纸、`ax` 是坐标系，操作都在 `ax`；
3. 读 CSV 用 `np.genfromtxt`；
4. 出图必带：轴标签（单位）、标题、图例、300 dpi。

### 1.6 小练习

1. 造一个假的 `meridional_stress_C2.csv`（10 行），跑通 1.3；
2. 把 `"o-"` 改成 `"--"`，观察差别；
3. 解释 fig 和 ax 的区别。

---

## 第 2 章 沿子午线应力曲线：核心定量图

### 2.1 为什么这张图是「核心」

穹顶从顶部（Oculus）到底部（拱脚），应力沿子午线变化——这张图回答：

- 哪里应力最大（决定开裂风险）；
- 从顶到底变化趋势（受压区/受拉区）；
- 不同模型（C1/C2）差多少。

### 2.2 标准画法（含双 y 轴）

子午向应力 + 环向应力可以放双 y 轴：

```python
fig, ax1 = plt.subplots(figsize=(7, 4))

ax1.plot(phi, sigma_mer, "b-o", label="子午向")
ax1.set_xlabel("子午角 φ [°]")
ax1.set_ylabel("子午向应力 [MPa]", color="blue")
ax1.tick_params(axis="y", labelcolor="blue")

# 第二个 y 轴（右侧）
ax2 = ax1.twinx()
ax2.plot(phi, sigma_hoop, "r-s", label="环向")
ax2.set_ylabel("环向应力 [MPa]", color="red")
ax2.tick_params(axis="y", labelcolor="red")

ax1.grid(True, linestyle="--", alpha=0.5)
fig.tight_layout()
fig.savefig("output/figures/meridional_hoop.png", dpi=300)
```

**要点**：

- `twinx()` 创建共享 x 轴的第二个 y 轴；
- 两条线用不同颜色 + 不同标记（`o`/`s`）；
- 两侧轴标签颜色与线颜色一致（读者不会认错）。

### 2.3 在图上标关键点

```python
# 找到最大应力位置
i_max = np.argmax(sigma_mer)

ax1.plot(phi[i_max], sigma_mer[i_max], "k*", markersize=14,
         label=f"峰值 {sigma_mer[i_max]:.2f} MPa")
ax1.annotate(
    f"φ={phi[i_max]:.1f}°, σ={sigma_mer[i_max]:.2f} MPa",
    xy=(phi[i_max], sigma_mer[i_max]),
    xytext=(phi[i_max] + 5, sigma_mer[i_max] + 0.5),
    arrowprops=dict(arrowstyle="->"),
)
```

峰值标注让图「会说话」——评审一眼看到关键数字。

### 2.4 本章小结

1. 沿子午线应力曲线 = 核心定量图；
2. 双 y 轴用 `twinx()`，颜色对齐；
3. 峰值用 `annotate` 标注（位置 + 数值）。

### 2.5 小练习

1. 用假数据画子午/环向双轴图；
2. 标注峰值并写清坐标；
3. 思考：为什么环向应力对穹顶很重要？

---

## 第 3 章 双模型对比与网格收敛曲线

### 3.1 本章目标

1. 画 C1 vs C2（新旧模型）对比曲线；
2. 画网格收敛曲线（文档3 第 8 章的方法落地成图）；
3. 学会半对数坐标。

### 3.2 C1 vs C2 对比

```python
# 读两个模型的数据
data_c1 = np.genfromtxt("output/data/meridional_stress_C1.csv",
                        delimiter=",", skip_header=1)
data_c2 = np.genfromtxt("output/data/meridional_stress_C2.csv",
                        delimiter=",", skip_header=1)

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(data_c1[:, 0], data_c1[:, 1], "b-o", label="C1（仅穹顶）")
ax.plot(data_c2[:, 0], data_c2[:, 1], "r--s", label="C2（含鼓座）")

ax.set_xlabel("子午角 φ [°]")
ax.set_ylabel("子午向应力 [MPa]")
ax.set_title("C1 vs C2 子午向应力对比")
ax.legend()
ax.grid(True, linestyle="--", alpha=0.5)
fig.tight_layout()
fig.savefig("output/figures/c1_vs_c2.png", dpi=300)
```

**对比图的规范**：

- 两条线样式**明显不同**（实线圆点 vs 虚线方块）；
- 图例说明**模型差异**（C1 仅穹顶 vs C2 含鼓座）；
- 需要时标注差异区（如阴影 `axvspan`）。

### 3.3 网格收敛曲线

文档3 讲过：三套网格（粗/中/细）算同一问题，看关键结果是否稳定。

```python
# 数据：网格尺寸 h 与对应最大位移/应力
h = np.array([1.00, 0.50, 0.25])          # 网格尺寸 [m]
u_max = np.array([1.32, 1.28, 1.27])      # 最大位移 [mm]（假数据示例）

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(h, u_max, "o-", linewidth=2, markersize=8)
ax.set_xlabel("网格尺寸 h [m]")
ax.set_ylabel("最大位移 [mm]")
ax.set_title("网格收敛性验证")

# 关键：x 轴反向（网格从粗到细 = h 从大到小）
ax.invert_xaxis()

# 标注收敛判据：相邻两次变化
for i in range(len(h) - 1):
    change = abs(u_max[i+1] - u_max[i]) / u_max[i] * 100
    ax.annotate(f"Δ={change:.1f}%",
                xy=((h[i]+h[i+1])/2, (u_max[i]+u_max[i+1])/2),
                fontsize=9)

ax.grid(True, linestyle="--", alpha=0.5)
fig.tight_layout()
fig.savefig("output/figures/convergence.png", dpi=300)
```

**读图标准**：相邻两次变化 < 1–5%，认为收敛；收敛图里 Δ 越来越小就是好图。

### 3.4 半对数坐标（误差图用）

收敛误差通常指数下降，线性坐标看不出趋势：

```python
fig, ax = plt.subplots()
ax.semilogy(h, error, "o-")        # y 轴取对数
ax.set_xlabel("网格尺寸 h [m]")
ax.set_ylabel("误差（对数坐标）")
```

`semilogy` = x 线性、y 对数。误差按指数下降时，半对数图是一条直线——视觉上一目了然。

### 3.5 本章小结

1. 对比图：两线样式区分 + 图例说明模型差异；
2. 收敛图：h 从大到小（x 反向）+ 标注相邻变化率；
3. 误差指数下降用 `semilogy`。

### 3.6 小练习

1. 用假数据画 C1/C2 对比；
2. 画收敛曲线并标 Δ；
3. 解释：收敛图里 Δ 代表什么？

---

## 第 4 章 柱状图与密度分布

### 4.1 本章目标

1. 画拱脚推力对比柱状图；
2. 画密度梯度分布图。

### 4.2 拱脚推力对比柱状图

```python
labels = ["C1", "C2", "V1.0 解析"]
thrust = [8.4, 9.1, 8.8]        # 单位 MN（假数据示例）

fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(labels, thrust, color=["steelblue", "tomato", "gray"],
              edgecolor="black", linewidth=0.8)

# 柱顶标数值
for bar, val in zip(bars, thrust):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.05,
            f"{val:.1f}", ha="center", fontsize=11)

ax.set_ylabel("拱脚水平推力 [MN]")
ax.set_title("拱脚推力对比（C1/C2 vs V1.0）")
ax.grid(axis="y", linestyle="--", alpha=0.5)
fig.tight_layout()
fig.savefig("output/figures/thrust_compare.png", dpi=300)
```

**柱状图规范**：

- 柱顶标数值（省得读者数格子）；
- 不同模型不同颜色 + 图例/说明；
- 网格只画 y 方向（`axis="y"`）。

### 4.3 密度梯度分布图

万神殿密度分层（1350/1500/1600）可以用阶梯图/柱状图表示：

```python
phi_edges = [0, 12, 25, 40, 90]        # 分层边界 [°]
density = [1350, 1500, 1600, 1600]     # 各层密度 [kg/m³]

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.step(phi_edges, density + [density[-1]], where="post")
ax.fill_between(phi_edges, density + [density[-1]], step="post",
                alpha=0.3)

ax.set_xlabel("从球顶起算的纬度 [°]")
ax.set_ylabel("密度 [kg/m³]")
ax.set_title("穹顶密度分层（Masi 2018）")
ax.grid(True, linestyle="--", alpha=0.5)
fig.tight_layout()
fig.savefig("output/figures/density_steps.png", dpi=300)
```

`step(..., where="post")` = 阶梯图，`fill_between` 填充颜色——一眼看出「上轻下重」。

### 4.4 本章小结

1. 柱状图：柱顶标数值、y 向网格；
2. 阶梯图：`step` + `fill_between` 表示分层量；
3. 每张图都要有单位（MN、kg/m³）。

### 4.5 小练习

1. 用假数据画推力柱状图并标数值；
2. 画密度阶梯图；
3. 思考：为什么密度分层对自重应力有影响？

---

## 第 5 章 论文级图片规范与完整出图脚本

### 5.1 本章目标

1. 掌握论文级图片的统一规范（字体、尺寸、格式）；
2. 写出一个可复用的「全套出图」脚本。

### 5.2 论文级规范清单

| 项 | 规范 |
| --- | --- |
| 尺寸 | 单栏 3.5 in、双栏 7 in |
| 字号 | 正文 10–11 pt，轴标签 12 pt |
| 格式 | PNG 300 dpi 或 PDF（矢量） |
| 轴标签 | 物理量 + 单位，如「应力 [MPa]」 |
| 标题 | 带编号 + 含义，如「图 3：C1 vs C2 应力对比」 |
| 图例 | 说明模型差异，不写「line1」 |
| 网格 | 虚线浅色，或不用 |

### 5.3 全局样式（推荐开头统一设置）

```python
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 12,
    "legend.fontsize": 10,
    "figure.dpi": 100,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})
```

一次设置，全书所有图自动规范。

### 5.4 错误示范 vs 正确示范

**错误**：

```python
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_title("Figure 1")
```

**正确**：

```python
ax.set_xlabel("子午角 φ [°]")
ax.set_ylabel("子午向应力 [MPa]")
ax.set_title("图 3：C1 vs C2 子午向应力对比")
```

**判断标准**：把图发给一个不懂项目的人，只看轴标签能不能知道图在说什么。

### 5.5 完整出图脚本

保存为 `post_process/plot_quantitative.py`，把第 2–4 章串起来：

```python
"""
万神殿定量出图：应力曲线 + 对比 + 收敛 + 推力柱状图
"""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

OUT = Path("output/figures")
OUT.mkdir(parents=True, exist_ok=True)

# ============ 图 1：沿子午线应力 ============
def plot_meridional():
    data = np.genfromtxt("output/data/meridional_stress_C2.csv",
                         delimiter=",", skip_header=1)
    phi, sigma = data[:, 0], data[:, 1]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(phi, sigma, "b-o", label="C2")
    i_max = np.argmax(sigma)
    ax.annotate(f"峰值 {sigma[i_max]:.2f} MPa",
                xy=(phi[i_max], sigma[i_max]),
                xytext=(phi[i_max] + 3, sigma[i_max] + 0.3),
                arrowprops=dict(arrowstyle="->"))
    ax.set_xlabel("子午角 φ [°]")
    ax.set_ylabel("子午向应力 [MPa]")
    ax.set_title("图 1：沿子午线的应力分布")
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.savefig(OUT / "fig1_meridional.png")
    plt.close(fig)

# ============ 图 2：C1 vs C2 ============
def plot_compare():
    d1 = np.genfromtxt("output/data/meridional_stress_C1.csv",
                       delimiter=",", skip_header=1)
    d2 = np.genfromtxt("output/data/meridional_stress_C2.csv",
                       delimiter=",", skip_header=1)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(d1[:, 0], d1[:, 1], "b-o", label="C1（仅穹顶）")
    ax.plot(d2[:, 0], d2[:, 1], "r--s", label="C2（含鼓座）")
    ax.set_xlabel("子午角 φ [°]")
    ax.set_ylabel("子午向应力 [MPa]")
    ax.set_title("图 2：C1 vs C2 对比")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.savefig(OUT / "fig2_compare.png")
    plt.close(fig)

# ============ 图 3：网格收敛 ============
def plot_convergence():
    h = np.array([1.00, 0.50, 0.25])
    u = np.array([1.32, 1.28, 1.27])
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(h, u, "o-", linewidth=2, markersize=8)
    ax.invert_xaxis()
    ax.set_xlabel("网格尺寸 h [m]")
    ax.set_ylabel("最大位移 [mm]")
    ax.set_title("图 3：网格收敛性验证")
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.savefig(OUT / "fig3_convergence.png")
    plt.close(fig)

# ============ 图 4：拱脚推力柱状图 ============
def plot_thrust():
    labels = ["C1", "C2", "V1.0"]
    thrust = [8.4, 9.1, 8.8]
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, thrust, color=["steelblue", "tomato", "gray"])
    for bar, val in zip(bars, thrust):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.05,
                f"{val:.1f}", ha="center")
    ax.set_ylabel("拱脚推力 [MN]")
    ax.set_title("图 4：拱脚推力对比")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    fig.savefig(OUT / "fig4_thrust.png")
    plt.close(fig)


if __name__ == "__main__":
    plot_meridional()
    plot_compare()
    plot_convergence()
    plot_thrust()
    print("✅ 定量图全部生成，位于 output/figures/")
```

### 5.6 结构说明

每个绘图函数：

- 只做一件事（读数据 → 画图 → 保存 → `plt.close`）；
- 文件名带编号（fig1/fig2...）；
- 全部走全局样式（5.3 的 rcParams）。

### 5.7 本章小结

1. 论文级图 = 带单位轴标签 + 编号标题 + 300 dpi + 全局样式；
2. 出图脚本用「一函数一图」组织，方便单独重画；
3. 判断标准：脱离项目也能读懂图。

### 5.8 小练习

1. 用假数据跑通 5.5 脚本，生成四张图；
2. 把其中一张图改成 PDF 格式保存；
3. 找一张自己以前画的图，按 5.2 规范改到达标。

---

## 附录：术语表、坑点、审核清单

### 术语表

| 英文 | 中文 | 一句话 |
| --- | --- | --- |
| figure | 画纸 | 整张图 |
| axes | 坐标系 | 纸上的子图 |
| plot | 折线图 | 连线 |
| bar | 柱状图 | 柱子 |
| step | 阶梯图 | 分段常值 |
| twinx | 双 y 轴 | 右侧第二个坐标轴 |
| legend | 图例 | 线/柱的说明 |
| annotate | 标注 | 带箭头的文字 |
| semilogy | 半对数坐标 | y 取对数 |
| dpi | 分辨率 | 每英寸点数（300=论文） |
| rcParams | 全局样式 | 一次设置处处生效 |
| tight_layout | 紧凑排版 | 防元素重叠 |

### 坑点速查

| 症状 | 解决 |
| --- | --- |
| 中文乱码 | 设置中文字体（见文档0）或用英文标签 |
| 图例盖住曲线 | `legend(loc="best")` 或 `bbox_to_anchor` |
| 保存后图片被裁 | `savefig.bbox="tight"` |
| 轴标签没单位 | 规范检查：每个标签必须带 [] |
| 颜色太花 | 每图 ≤3 色，对比图用冷-暖色 |

### 审核清单

- [ ] 轴标签：物理量 + 单位
- [ ] 标题：编号 + 含义
- [ ] 图例：说明差异，不用「line1」
- [ ] 单位正确（MPa、MN、mm、kg/m³）
- [ ] 对比图色标/坐标范围一致
- [ ] 300 dpi PNG 或 PDF
- [ ] 脱离项目也能读懂

---

> 全书完（v2.0，2026-08-13 重写）。旧版存档于 `docs/tutorials/_legacy/`。

---

## 实战增补 · 万神殿定量图的完整图库（2026-08 实战）

> 本章基于《万神殿全解》成书卷七/卷九：Richardson 收敛图、双 y 轴敏感性图、半对数误差图——三张「证明类」图表的完整数据与画法。定量图的目标不是好看，是**让结论被看见**。

### 增补 1：网格收敛图——项目的「身份证」

数据（C1 三档，E=14.8 GPa）：

| h (m) | u_max (mm) | σ1 (MPa) |
| --- | --- | --- |
| 2.0 | 0.8380 | 0.0666 |
| 1.0 | 0.8390 | 0.1142 |
| 0.5 | 0.8392 | 0.1572 |

**画法要点**：x 轴是网格尺寸 h（反向：从粗到细 = h 从大到小）；位移与应力**双轴分开**（量级差太大）；标注收敛判据线（相邻变化 <2%）。**这张图要同时传达两条信息：位移收敛（好）与 σ1 极值不收敛（单点极值非收敛量）——一张图讲完「什么可信什么不可信」。**

**实测收敛阶**：p = log₂(0.0010/0.0002) = 2.32，可标注在图上——「把计算过程写进图里」是定量图的最高形态。

### 增补 2：Richardson 外推结果表（工具 tools/estimate_grid_error.py 实测）

```python
def richardson(coarse, fine, r, p):
    exact = fine + (fine-coarse)/(r**p - 1)
    err = abs(fine-coarse)/(r**p - 1)
```

实测输出：p=2 外推 0.8391 mm（误差 0.0003）、p=3 外推 0.8393 mm（误差 0.0001）——**双假设给误差上下界**（P2 元点值理论阶 2~3 之间）。图中画「两档外推值区间」比画点更诚实。

### 增补 3：双 y 轴敏感性图（V1.0 fig04a 的升级版）

藻井深度扫描 {0.6×, 0.8×, 1.0×, 1.2×, 1.4×}：左轴 JCIR%（柱状，恒等 B）、右轴 MCFR%（折线，收缩拖后腿）。**画法要点**（plot_sensitivity.m 实战）：

- `yyaxis left/right` 双轴 + `ylim([0,16])` 统一范围；
- 图上直接标注物理解释：「JCIR == B (identity)」「Shrinkage-dominant」——**文字标注画在图上，结论跟着图走**；
- `xline(1.0, 'k--')` 标注「Actual design」基准。

### 增补 4：半对数误差图（收敛研究标配）

误差随 h 的衰减在 log-log 坐标下是直线（斜率 = 收敛阶 p）。画法：`plt.loglog(h, err)` 或 `semilogy`。**用直线的斜率读收敛阶，比算 log₂ 更直观**——两种表达同一件事，图上给斜率、文字给数值。

### 增补 5：论文级规范清单（AI-Leader 验收 §2.4 落地）

| 规范 | 实测案例 |
| --- | --- |
| 轴标签带单位 | `u_max (mm)`、`σ1 (MPa)`、`Latitude (deg)` |
| 300 dpi | 论文投稿底线 |
| 对比图 clim/ylim 一致 | 五档 ε_sh 扫描共用 [0,12] 与统一色标 |
| 图上标注关键数值 | 收敛阶 p=2.32、JCIR=8.1%、MCFR=5.8% 直接写图上 |
| 数据源注释 | 「Data: arch_scan.csv」——图与台账可回溯 |

### 增补小练习

1. 用 {0.8380, 0.8390, 0.8392} 三档数据画收敛图，x 轴为什么「反向」？
2. 画出 Richardson 双假设（p=2/3）的外推区间，说明哪个更可信。
3. 双 y 轴图里 JCIR 用柱、MCFR 用折线的理由是什么？（一个是恒等关系、一个是派生量）
4. 你的上一张图缺了清单里的哪几项？

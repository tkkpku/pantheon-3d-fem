# 文档6 · PyVista 三维结果可视化与 FEM 云图渲染（重构版）

> **项目**：万神殿穹顶三维 FEM 重构
> **版本**：v2.0 轮次 1/6（2026-08-13 逐轮重写）
> **前置要求**：文档5 已跑出 C1 结果（`c1_result.bp`）
> **配套环境**：WSL2 `pantheon-fem`（pyvista 0.48.4）

---

## 写给你的使用说明（30 秒读完）

文档5 把数字算出来了，文档6 负责**把数字变成看得懂的图**。

PyVista 是 Python 最强的三维可视化库之一，本书教你三件事：

1. 读取 FEM 结果（`.bp` / `.vtu`）并画第一张云图；
2. 控制视角、颜色、色标，让图「会说话」；
3. 项目需要的进阶技巧：切面、透明叠加、批量截图、动画。

- 每章一个主题，先讲直觉再给代码；
- 所有示例都标注「运行方法」和「预期输出」；
- 记住一个原则：**图是给论文和汇报用的，不是给自己看的**——所以每张图都要有物理含义、单位、色标。

### 🎩 老板版速读（60 秒，Leader 必读）

你不用画图，但要会**验收 AI 出的图**。四张图四个检查点：

1. **色标带单位**（位移 [mm]、应力 [MPa]）；
2. **对比图色标范围一致**（不固定 clim = 自欺欺人）；
3. **视角有含义**（等轴/侧视/俯视，不是随手转的）；
4. **图上有标题**（编号 + 物理含义）。

一眼不合格就退回重画，不用看代码。

---

## 第 0 章 学习地图

### 0.1 全书地图

| 章 | 内容 | 难度 | 能力 |
| --- | --- | --- | --- |
| 第 1 章 | PyVista 是什么 + 环境自检 | 🟢 | 热身 |
| 第 2 章 | 读 FEM 结果 + 第一张云图 | 🟢 | 核心 |
| 第 3 章 | 视角、颜色、色标 | 🟡 | 核心 |
| 第 4 章 | 矢量场（位移箭头） | 🟡 | 进阶 |
| 第 5 章 | 切面与几何叠加 | 🟡 | 项目 |
| 第 6 章 | 批量截图与动画 | 🟡 | 交付 |
| 附录 | 术语表、坑点、审核清单 | 🟢 | 工具 |

### 0.2 学习路线

- **主线**：第 1 → 2 → 3 章（必读）；
- **支线**：第 4 → 5 → 6 章（做 C2+ 后处理时用）；
- **工具**：附录。

### 0.3 环境自检

```bash
conda activate pantheon-fem
python -c "import pyvista; print(pyvista.__version__)"
```

预期输出（版本可能略不同）：

```text
0.48.4
```

> 如果 `import pyvista` 报错，先 `pip install pyvista`。文档4 第 8.5 节也用过它。

---

## 第 1 章 PyVista 是什么

### 1.1 一句话版本

**PyVista 是一个三维可视化库：把「网格 + 数据」变成可以旋转、缩放、截图的三维场景。**

### 1.2 它在流水线里的位置

```text
FEniCSx 求解（文档5）→ 结果 .bp/.vtu → PyVista（本文档）→ 云图/动画/截图
```

### 1.3 核心数据结构：三个容器

| 数据结构 | 装什么 | 什么时候用 |
| --- | --- | --- |
| `UnstructuredGrid` | 任意形状网格（四面体等） | **FEM 结果（本项目）** |
| `PolyData` | 表面/点云 | 提取表面后 |
| `StructuredGrid` | 规则网格 | 较少用 |

**FEM 结果的标配**：`UnstructuredGrid` + 节点/单元上附着的标量场（位移幅值、应力）或矢量场（位移）。

### 1.4 数据附着的两种方式

| 方式 | 含义 | 例子 |
| --- | --- | --- |
| 点数据（point data） | 每个节点一个值 | 节点位移 |
| 单元数据（cell data） | 每个单元一个值 | 单元应力（常值） |

画图前要知道自己的数据是哪种——云图效果不同。

### 1.5 本章小结

1. PyVista = 网格 + 数据 → 三维场景；
2. `UnstructuredGrid` 是 FEM 结果的标准容器；
3. 数据分点数据和单元数据。

### 1.6 小练习

1. 跑通环境自检；
2. 用一句话向室友解释 PyVista 是干嘛的；
3. 思考：为什么可视化也是工程验证的一部分？（提示：文档3 第 8 章的陷阱）

---

## 第 2 章 读 FEM 结果 + 第一张云图

### 2.1 本章目标

把文档5 的 C1 结果读进来，画出第一张位移云图。

### 2.2 读取 `.bp` 结果

文档5 导出的是 `.bp`（FEniCSx 的二进制结果格式）。读取：

```python
import pyvista as pv

# 读取 BP 结果（含位移 uh 和应力 sigma_h 两个场）
reader = pv.get_reader("output/results/c1_result.bp")
mesh = reader.read()

# 查看有哪些数据字段
print("数据字段:", mesh.array_names)
```

预期输出类似：

```text
数据字段: ['f', 'u', 'sigma']
```

（名字取决于文档5 导出时的命名。）

### 2.3 画第一张云图

```python
# 画位移幅值云图（假设字段名是 "u"，矢量场会自动取幅值）
plotter = pv.Plotter()
plotter.add_mesh(
    mesh,
    scalars="u",          # 用哪个字段上色
    show_edges=False,     # 不显示网格线（云图更干净）
    cmap="coolwarm",      # 蓝→红 色标
)
plotter.add_text("C1 位移云图 [m]", font_size=12)
plotter.show()
```

### 2.4 逐行拆解

| 代码 | 作用 |
| --- | --- |
| `pv.get_reader(...)` | 按文件类型自动选择读取器 |
| `reader.read()` | 读成 PyVista 网格对象 |
| `plotter.add_mesh(mesh, scalars="u", ...)` | 把网格画进场景，按 u 字段上色 |
| `cmap="coolwarm"` | 颜色方案：蓝（小）→ 红（大） |
| `add_text(...)` | 加标题文字 |
| `plotter.show()` | 弹出窗口显示 |

### 2.5 保存截图

```python
plotter = pv.Plotter(off_screen=True)   # 离屏模式（服务器/批处理）
plotter.add_mesh(mesh, scalars="u", cmap="coolwarm")
plotter.screenshot("output/figures/c1_displacement.png")
print("截图已保存")
```

**离屏模式**（`off_screen=True`）：不弹窗口，直接存图——批处理和 WSL 无图形环境时必用。

### 2.6 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `get_reader` 不支持 `.bp` | 版本太老 | 升级 pyvista（≥0.43） |
| 字段名找不到 | 名字记错 | 先打印 `array_names` |
| 窗口弹不出来 | WSLg 不可用 | 用 `off_screen=True` + `screenshot` |
| 颜色看不出差异 | 字段全是一个值 | 检查数据是否成功读入 |

### 2.7 本章小结

1. `get_reader` + `read()` 读结果；
2. `add_mesh(scalars=...)` 画云图，`cmap` 选配色；
3. `off_screen=True` + `screenshot()` 离屏保存；
4. 先打印 `array_names` 确认字段名。

### 2.8 小练习

1. 读 C1 结果，打印字段名；
2. 画位移云图并保存 PNG；
3. 实验：`show_edges=True` 和不加 `cmap`，观察差别。

---

## 第 3 章 视角、颜色、色标：让云图会说话

### 3.1 本章目标

1. 掌握三种预设视角（xy/xz/等轴）；
2. 掌握色标（scalarbar）的设置：单位、范围、标题；
3. 理解「固定色标范围」为什么对对比图至关重要。

### 3.2 视角：从哪看万神殿

```python
plotter = pv.Plotter()
plotter.add_mesh(mesh, scalars="u", cmap="coolwarm")

# 俯视图（从 z 轴往下看）
plotter.view_xy()

# 侧视图（从 y 方向看）
plotter.view_xz()

# 等轴视角（45° 立体感）
plotter.view_isometric()

# 完全手动：相机位置
plotter.camera_position = [(40, 40, 30),   # 相机在哪
                           (0, 0, 0),      # 看哪里
                           (0, 0, 1)]      # 哪个方向朝上
plotter.show()
```

**万神殿推荐**：

| 图 | 视角 | 用途 |
| --- | --- | --- |
| 整体位移 | 等轴 | 汇报主图 |
| 侧剖面 | xz | 看厚度方向分布 |
| 俯视 | xy | 看藻井/对称性 |

### 3.3 色标：图的「图例」

一张好云图必须有色标，否则读者不知道颜色对应多少：

```python
plotter.add_mesh(
    mesh,
    scalars="u",
    cmap="coolwarm",
    scalar_bar_args={
        "title": "位移 [mm]",       # 带单位！
        "position_x": 0.85,
        "position_y": 0.1,
        "width": 0.1,
        "height": 0.8,
    },
)
```

**单位换算**：FEniCSx 输出位移单位是 m，画图常转 mm（×1000）：

```python
import numpy as np

# 复制网格，把位移转成 mm
mesh_mm = mesh.copy()
u = mesh_mm.point_data["u"] * 1000.0
mesh_mm.point_data["u_mm"] = u
```

### 3.4 固定色标范围：对比的关键

两张图要对比时（粗网格 vs 细网格），**色标范围必须一致**，否则看起来「细网格应力更大」其实是色标骗人。

```python
plotter.add_mesh(
    mesh,
    scalars="sigma_mpa",
    clim=[0, 2.0],        # 固定颜色对应范围 0~2 MPa
    cmap="coolwarm",
)
```

`clim`（color limits）= 颜色映射范围。对比图一律固定，不许自动缩放。

### 3.5 常用配色（cmap）速查

| cmap | 风格 | 适合 |
| --- | --- | --- |
| `coolwarm` | 蓝→红 | 位移/应力（最常用） |
| `viridis` | 紫→黄 | 通用（色盲友好） |
| `RdBu_r` | 红→蓝 | 拉压对比（负→正） |
| `jet` | 彩虹 | 演示（学术上不推荐） |

> 学术图推荐 `coolwarm` 或 `viridis`，别用 `jet`。

### 3.6 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 色标没有单位 | scalar_bar 没设 title | 加 `"title": "位移 [mm]"` |
| 对比图看起来突变 | 色标范围不一致 | 统一 `clim` |
| 视角转不过来 | 用了错误 view_* | 查 3.2 表 |
| 颜色太花 | cmap 选错 | 用 coolwarm/viridis |

### 3.7 本章小结

1. 视角：`view_xy/xz/isometric` 或 `camera_position`；
2. 色标：`scalar_bar_args` 设标题（带单位）；
3. 单位换算：m → mm 在画图前做；
4. 对比图必须固定 `clim`。

### 3.8 小练习

1. 分别用三种视角保存三张图；
2. 画 σ1（最大主应力）云图，单位 MPa，固定 clim=[0, 2]；
3. 解释：为什么对比图不固定色标是「自欺欺人」？

---

## 第 4 章 矢量场与切面：看「方向」和「内部」

### 4.1 本章目标

1. 用箭头显示位移矢量方向；
2. 用切面看球壳内部应力分布。

### 4.2 矢量箭头：位移往哪走

```python
# glyphs：在每个节点画一个小箭头，方向和大小来自矢量场
arrows = mesh.glyph(
    orient="u",          # 用哪个矢量场定方向
    scale="u",           # 用哪个场定大小
    factor=0.02,         # 箭头放大系数（位移太小，必须放大）
)

plotter = pv.Plotter()
plotter.add_mesh(mesh, color="lightgray", opacity=0.3)  # 半透明壳体
plotter.add_mesh(arrows, color="red")                    # 箭头
plotter.show()
```

**注意 `factor`**：位移只有毫米级，直接画箭头看不见，必须放大——`factor` 就是放大倍数，值要靠试。

### 4.3 切面：切开球壳看内部

```python
# 沿 z 方向切一刀（xz 平面）
slice_mesh = mesh.slice(normal=(0, 1, 0),   # 法向 = y 方向 → 切出 xz 面
                        origin=(0, 0, 0))    # 切面过原点

plotter = pv.Plotter()
plotter.add_mesh(slice_mesh, scalars="u", cmap="coolwarm")
plotter.view_xz()
plotter.show()
```

**切面能看什么**：球壳的厚度方向应力分布、内表面和外表面的差异——这是云图看不到的「内部信息」。

### 4.4 切片在万神殿的用途

- 沿子午面切：看穹顶从顶到底的应力变化；
- 切到藻井层：看藻井周围应力集中；
- 切到交界面：看穹顶-鼓座传力。

### 4.5 本章小结

1. `glyph()` 画矢量箭头，`factor` 控制放大；
2. `slice(normal, origin)` 切面；
3. 切面是看内部应力的标准手段。

### 4.6 小练习

1. 画位移箭头（试几个 factor 值）；
2. 沿 xz 切面画应力云图并保存；
3. 思考：切面图对「验证拱脚传力」有什么用？

---

## 第 5 章 透明叠加、批量截图、动画：汇报级出图

### 5.1 本章目标

1. 用透明度叠加显示「几何 + 结果」；
2. 批量生成多角度截图；
3. 生成旋转动画。

### 5.2 透明叠加：壳体 + 切面同框

```python
plotter = pv.Plotter()

# 半透明壳体（看整体）
plotter.add_mesh(mesh, color="lightgray", opacity=0.2)

# 不透明切面（看内部结果）
slice_mesh = mesh.slice(normal=(0, 1, 0), origin=(0, 0, 0))
plotter.add_mesh(slice_mesh, scalars="u", cmap="coolwarm")

plotter.add_axes()        # 坐标轴
plotter.view_isometric()
plotter.show()
```

`opacity=0.2` = 20% 不透明（80% 透明）。**透明壳体 + 彩色切面**是 FEM 汇报的标准构图。

### 5.3 批量截图：多视角一张图

```python
from pathlib import Path

out_dir = Path("output/figures")
out_dir.mkdir(parents=True, exist_ok=True)

views = {
    "isometric": "view_isometric",
    "side": "view_xz",
    "top": "view_xy",
}

for name, view in views.items():
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(mesh, scalars="u", cmap="coolwarm")
    getattr(plotter, view)()
    plotter.screenshot(str(out_dir / f"c1_{name}.png"))
    plotter.close()
    print(f"已保存: c1_{name}.png")
```

**套路**：循环里每次新建 Plotter → 设视角 → 截图 → `close()`。忘记 `close()` 会占满内存。

### 5.4 旋转动画

```python
plotter = pv.Plotter(off_screen=True)
plotter.add_mesh(mesh, scalars="u", cmap="coolwarm")

# 绕 z 轴转 36 步，每步存一张
for i in range(36):
    plotter.camera_position = plotter.camera_position  # 保持
    plotter.camera.azimuth(10)                          # 每次转 10°
    plotter.screenshot(str(out_dir / f"anim_{i:02d}.png"))

plotter.close()
print("动画帧已生成，可用 ffmpeg 合成视频")
```

```bash
# 合成视频（WSL 或 Windows 有 ffmpeg 时）
ffmpeg -framerate 10 -i output/figures/anim_%02d.png -c:v libx264 output/figures/c1_rotate.mp4
```

### 5.5 本章小结

1. `opacity` 控制透明，透明壳体 + 彩色切面 = 标准构图；
2. 批量截图用循环 + `close()`；
3. 动画 = 逐帧截图 + ffmpeg 合成。

### 5.6 小练习

1. 生成「透明壳体 + 切面」的合成图；
2. 批量生成三个视角截图；
3. 生成 12 帧小动画（不要求 ffmpeg，先生成帧）。

---

## 第 6 章 完整案例：C1 结果可视化

### 6.1 完整代码

把前 5 章串成一套可复用的出图脚本 `post_process/plot_c1.py`：

```python
"""
C1 结果可视化：位移云图 + 应力云图 + 切面 + 批量截图
运行：conda activate pantheon-fem && python post_process/plot_c1.py
"""
import numpy as np
import pyvista as pv
from pathlib import Path

OUT = Path("output/figures")
OUT.mkdir(parents=True, exist_ok=True)

# ============ 1. 读取结果 ============
reader = pv.get_reader("output/results/c1_result.bp")
mesh = reader.read()
print("字段:", mesh.array_names)

# 位移转 mm
if "u" in mesh.array_names:
    mesh.point_data["u_mm"] = mesh.point_data["u"] * 1000.0

# ============ 2. 位移云图（等轴 + 固定色标） ============
def displacement_plot(title, view="view_isometric", fname="c1_u.png"):
    p = pv.Plotter(off_screen=True)
    p.add_mesh(mesh, scalars="u_mm", cmap="coolwarm",
               scalar_bar_args={"title": "位移 [mm]"})
    getattr(p, view)()
    p.add_text(title, font_size=12)
    p.screenshot(str(OUT / fname))
    p.close()
    print(f"已保存 {fname}")

displacement_plot("C1 位移云图")
displacement_plot("C1 侧视", "view_xz", "c1_u_side.png")

# ============ 3. 切面 + 透明壳体 ============
slice_mesh = mesh.slice(normal=(0, 1, 0), origin=(0, 0, 0))
p = pv.Plotter(off_screen=True)
p.add_mesh(mesh, color="lightgray", opacity=0.15)
p.add_mesh(slice_mesh, scalars="u_mm", cmap="coolwarm",
           scalar_bar_args={"title": "位移 [mm]"})
p.view_isometric()
p.screenshot(str(OUT / "c1_slice.png"))
p.close()
print("已保存 c1_slice.png")

print("✅ C1 可视化完成，全部图片在 output/figures/")
```

### 6.2 验收标准

- [ ] 三张图生成：`c1_u.png`、`c1_u_side.png`、`c1_slice.png`；
- [ ] 色标带单位 mm；
- [ ] 切面图壳体透明、切面彩色；
- [ ] 图上有标题。

### 6.3 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 找不到 `u` 字段 | 文档5 导出字段名不同 | 打印 `array_names` 改名字 |
| 切片是空的 | 切面位置没穿过模型 | 调 `origin` |
| 颜色全一个色 | 数据没乘 1000 或范围太小 | 检查数据 + 固定 clim |
| 内存涨爆 | 循环没 close | 每个循环 `p.close()` |

---

## 附录：术语表、坑点、审核清单

### 术语表

| 英文 | 中文 | 一句话 |
| --- | --- | --- |
| plotter | 绘图器 | 管理场景的对象 |
| mesh | 网格对象 | 节点+单元+数据 |
| scalars | 标量字段 | 用来上色的数据 |
| cmap | 色图 | 颜色映射方案 |
| clim | 色标范围 | 颜色对应值的上下限 |
| scalar bar | 色标 | 图的图例 |
| glyph | 箭头/标记 | 表示矢量方向的图形 |
| slice | 切面 | 切一刀看内部 |
| opacity | 透明度 | 0~1，越小越透明 |
| off_screen | 离屏 | 不弹窗直接存图 |
| screenshot | 截图 | 保存图片 |
| azimuth | 方位角 | 相机绕轴旋转角度 |

### 坑点速查

| 症状 | 解决 |
| --- | --- |
| 窗口弹不出 | `off_screen=True` |
| 对比图失真 | 固定 `clim` |
| 位移看不见 | 转 mm + 放大 factor |
| 字段找不到 | 先 `array_names` |
| 动画卡顿 | 帧数减少 + 离屏 |

### 审核清单

- [ ] 色标有标题和单位
- [ ] 对比图色标范围一致
- [ ] 图上有标题/编号
- [ ] 单位正确（m→mm，Pa→MPa）
- [ ] 视图角度有物理含义（侧视/俯视/等轴）
- [ ] 图片清晰、无水印遮挡

---

> 全书完（v2.0，2026-08-13 重写）。旧版存档于 `docs/tutorials/_legacy/`。

---

## 实战增补 · .bp 结果读取与云图口径（2026-08 实战）

> 本章基于《万神殿全解》成书卷九：ADIOS2 .bp 结果格式五件套、命名规则解码、以及「云图口径决定科学结论」的实战教训（74.2° 散点 vs 12.6° 连通带）。

### 增补 1：.bp 结果目录五件套（先懂格式再画图）

每个 VTXWriter 导出的结果是一个目录：

| 文件 | 作用 | 实例（c1_E14.8_sigma） |
| --- | --- | --- |
| data.0 | 实际数据（二进制数组） | 707,136 字节 |
| md.0 | 元数据（变量名/类型/网格结构） | 1,960 字节 |
| mmd.0 | 元-元数据 | 212 字节 |
| md.idx | 元数据索引（偏移表） | 146 字节 |
| profiling.json | 写出性能档案（JSON 可读） | 726 字节 |

**快速验场技巧**：`data.0 大小 = 场规模 × 8 字节/分量`。u 场 1,926,240 字节 ≈ 3 分量 × 8 × 80,260 点——不打开文件就能核验场的大小。

### 增补 2：命名规则解码（文件名即元数据）

```
c4_ml_swpsh_E1.0_sh6.00e-05_sigma.bp
│  │   │       │      │         └── 场类型（sigma/u/D）
│  │   │       │      └── 干缩应变
│  │   │       └── E 档
│  │   └── 荷载（sw/sh/swpsh）
│  └── 网格标记（m/ml/m1m/m0p5ms）
└── 算例编号
```

PyVista 读 .bp 后可用 `glob("output/results/*swpsh*sigma.bp")` 秒选任意算例组合——**命名体系是可视化的前置基础设施。**

### 增补 3：云图口径——同一份数据，两种画法两种结论

8/17 决战日的核心教训（数据存档 §10）：

| 口径 | 画法 | 结果 | 问题 |
| --- | --- | --- | --- |
| max 单点 | 全场 σ1 云图 + 色标最大值 | θ_top=74.2° | **孤立尖角散点**（每个藻井角一小撮超限点，互不相连）——超过文献上限 65.8°，误导 |
| 连通簇 | 仅画 BFS 最大连通开裂带的点 | θ_top=12.6° | 真实连贯裂缝带，始终贴着环向转压带 |

**PyVista 实践**：画 σ1 云图时，超限区（σ1>f_t）用 `threshold` 过滤后再看——**如果超限区是一堆互不相连的小斑点，最大值就是散点口径，不能当裂缝讲**。云图不只是一张图，它是口径的表达。

### 增补 4：固定色标——对比的命门

多算例对比（如五档 ε_sh 扫描）时，**所有图的 clim 必须一致**（如统一 [0, 0.12] MPa）——否则色标随数据缩放，视觉上「一样的颜色」代表「不同的数值」。项目规范：对比图 clim 一致（AI-Leader 验收清单 §2.4）。

### 增补 5：WSL 离屏渲染

WSL 无显示环境，PyVista 必须离屏（offscreen）：

```python
pv.start_xvfb()          # 或 pyvista.OFF_SCREEN = True
plotter.screenshot("fig.png", window_size=[1600,1200])
```

实战环境：pyvista 0.48.4 + WSL2 + xvfb——**「能出图」和「能交互看图」在 WSL 里是两件事**，截图管线是脚本可复现的底线。

### 增补小练习

1. 打开任一 .bp 目录，用 profiling.json 说出写出耗时与字节数。
2. 用命名规则解码：`c4plus_c0_shell_groups_1m_E1.0_sh1.00e-04_D.bp` 的每一段。
3. 阈下思考：为什么「max 单点口径」在奇异场（尖角）上必然虚高？什么口径能修正？
4. 设计一张「五档 ε_sh 扫描对比图」的 clim 方案。

# 万神殿穹顶三维FEM重构 · 文档6 · PyVista三维结果可视化与FEM云图渲染

> **定位**：求解完成后，需要把结果「画出来」。PyVista 负责三维云图——位移场、应力场、开裂区域标注。
> **前提**：已完成文档5（FEniCSx 求解），有 `.vtu`/`.bp` 结果文件或 NumPy 应力数据。
> **风格**：全程可运行代码，绑定万神殿项目真实场景。

---

## 目录

1. [工具基础总览：PyVista 是什么](#1-工具基础总览pyvista-是什么)
2. [🟢 入门：读取 FEM 结果并画第一个云图](#2-入门读取-fem-结果并画第一个云图)
3. [🟢 入门：标量场云图（位移幅值、主应力）](#3-入门标量场云图位移幅值主应力)
4. [🟢 入门：矢量场（位移方向箭头）](#4-入门矢量场位移方向箭头)
5. [🟢 入门：调整视角、颜色映射、色标](#5-入门调整视角颜色映射色标)
6. [🟡 项目刚需：切面可视化（沿子午面切片）](#6-项目刚需切面可视化沿子午面切片)
7. [🟡 项目刚需：筛选单元绘制开裂区域](#7-项目刚需筛选单元绘制开裂区域)
8. [🟡 项目刚需：几何透明叠加（穹顶+鼓座同时展示）](#8-项目刚需几何透明叠加穹顶鼓座同时展示)
9. [🟡 项目刚需：批量截图自动输出](#9-项目刚需批量截图自动输出)
10. [🟡 项目刚需：动画旋转导出](#10-项目刚需动画旋转导出)
11. [📦 完整可视化案例](#11-完整可视化案例)
12. [常见错误与坑点](#12-常见错误与坑点)
13. [PyVista 审核自查清单](#13-pyvista-审核自查清单)

---

## 1. 工具基础总览：PyVista 是什么

### 1.1 PyVista = VTK 的 Pythonic 封装

VTK（Visualization Toolkit）是世界上最强大的科学可视化库之一，但它的原生 Python API 极其冗长。PyVista 对 VTK 做了 Pythonic 封装——用最少的代码实现最常需的可视化效果。

| | PyVista | Matplotlib 三维 |
|---|---|---|
| **三维网格** | 原生支持非结构化四面体网格 | 不支持 FEM 网格 |
| **云图** | 原生支持标量/矢量场映射 | 仅支持简单曲面 |
| **切面** | 任意裁切 + 内部可视 | 不支持 |
| **性能** | GPU 加速（RTX5070Ti 有用！） | CPU 渲染，大模型卡顿 |
| **适用场景** | 三维 FEM 结果可视化 | 二维曲线/曲面 |

### 1.2 PyVista 的数据模型

```python
import pyvista as pv

# PyVista 的核心数据结构
# UnstructuredGrid: 非结构化网格（四面体、六面体混合）
# PolyData: 面片数据（表面网格）
# StructuredGrid: 结构化网格（如均匀立方体网格）

# FEM 结果通常储存在 UnstructuredGrid 中
# 每个节点/单元上可以附着多个标量/矢量场
```

### 1.3 基本渲染管线

```
数据（网格 + 场）→ 映射器（颜色映射）→ 演员（在场景中定位）→ 渲染器 → 窗口
```

PyVista 把这一切封装为 `.plot()` 方法，一行代码出图。

---

## 2. 🟢 入门：读取 FEM 结果并画第一个云图

### 2.1 从 .vtu 文件读取

```python
import pyvista as pv

# 读取 FEniCSx 导出的 .vtu 文件（或 .vtk 文件）
mesh = pv.read("output/results/displacement000000.vtu")

# 查看网格信息
print(mesh)
# 输出：
# UnstructuredGrid (0x...)
#   N Cells:    12345
#   N Points:   67890
#   N Arrays:   1

# 查看附着的数据字段
print(mesh.array_names)
# 输出：['displacement'] 或 ['u']

# 画云图
mesh.plot(
    scalars="displacement",   # 要显示的数据字段
    cmap="viridis",           # 颜色映射
    show_edges=False,         # 不显示网格边（FEM 网格太密）
    show_bounds=True,         # 显示包围盒坐标轴
    title="万神殿穹顶 · 位移幅值"
)
```

### 2.2 从 NumPy 数据构建 PyVista 网格

如果只有节点坐标和单元连接关系（无 .vtu 文件）：

```python
import numpy as np
import pyvista as pv

# 假设你有：
# points: (n_nodes, 3) 节点坐标
# cells: (n_elements, 4) 四面体顶点索引（一阶）
# data: (n_nodes,) 节点上的标量数据（如位移）

def build_pyvista_grid(points, cells_tetra, displacement):
    """
    从 NumPy 数据构建 PyVista 非结构化网格。

    Args:
        points: shape (n_nodes, 3) 节点坐标
        cells_tetra: shape (n_elements, 4) 四面体顶点索引
        displacement: shape (n_nodes,) 位移幅值

    Returns:
        grid: PyVista UnstructuredGrid
    """
    # PyVista 要求的 cells 格式：
    # [n_vertices_per_cell, v0, v1, v2, v3, n_vertices_per_cell, ...]
    n_cells = cells_tetra.shape[0]
    cells_flat = np.hstack([
        np.full((n_cells, 1), 4),   # 每个单元 4 个顶点
        cells_tetra
    ]).ravel()

    cell_types = np.full(n_cells, pv.CellType.TETRA, dtype=np.int32)

    grid = pv.UnstructuredGrid(cells_flat, cell_types, points)
    grid["displacement"] = displacement   # 附着标量数据

    return grid
```

---

## 3. 🟢 入门：标量场云图（位移幅值、主应力）

### 3.1 位移幅值云图

```python
import pyvista as pv
import numpy as np

def plot_displacement_magnitude(mesh, displacement_vector):
    """
    画位移幅值云图。

    Args:
        mesh: PyVista UnstructuredGrid
        displacement_vector: shape (n_points, 3) 位移矢量场
    """
    # 计算位移幅值
    disp_mag = np.sqrt(
        displacement_vector[:, 0]**2 +
        displacement_vector[:, 1]**2 +
        displacement_vector[:, 2]**2
    )

    # 附着到网格
    mesh["disp_magnitude"] = disp_mag

    # 画图
    mesh.plot(
        scalars="disp_magnitude",
        cmap="plasma",
        scalar_bar_args={
            "title": "位移幅值 (m)",
            "title_font_size": 14,
            "label_font_size": 12,
        },
        show_edges=False,
        lighting=True,           # 开启光照（使曲面更立体）
        smooth_shading=True,     # 平滑着色
        title="万神殿穹顶 · 自重位移幅值",
        window_size=[1000, 800],
    )
```

### 3.2 第一主应力云图（开裂判定核心图）

```python
def plot_principal_stress_1(mesh, sigma_1):
    """
    画第一主应力 σ₁ 云图。

    正值（拉应力）= 暖色 → 潜在开裂区
    负值（压应力）= 冷色 → 安全受压区

    Args:
        mesh: PyVista UnstructuredGrid
        sigma_1: shape (n_points,) 第一主应力 [Pa]
    """
    # 转为 MPa（方便阅读）
    sigma_1_mpa = sigma_1 / 1e6

    mesh["sigma_1_MPa"] = sigma_1_mpa

    # 设置颜色映射：以 f_t = 0.08 MPa 为零点分界
    f_t_mpa = 0.08

    mesh.plot(
        scalars="sigma_1_MPa",
        cmap="RdBu_r",           # 红（拉）→ 白 → 蓝（压）
        clim=[-0.5, 0.5],        # 固定色标范围（MPa）
        scalar_bar_args={
            "title": "σ₁ (MPa)",
            "title_font_size": 14,
        },
        show_edges=False,
        lighting=True,
        title="万神殿穹顶 · 第一主应力 σ₁",
        window_size=[1000, 800],
    )
```

### 3.3 多子图对比（C1 vs C2 并排）

```python
import pyvista as pv

def plot_side_by_side(mesh_left, scalars_left, title_left,
                      mesh_right, scalars_right, title_right):
    """并排对比两个模型的结果"""

    pl = pv.Plotter(shape=(1, 2), window_size=[1800, 800])

    # 左图
    pl.subplot(0, 0)
    pl.add_mesh(mesh_left, scalars=scalars_left, cmap="RdBu_r",
                show_edges=False, lighting=True)
    pl.add_title(title_left, font_size=14)

    # 右图
    pl.subplot(0, 1)
    pl.add_mesh(mesh_right, scalars=scalars_right, cmap="RdBu_r",
                show_edges=False, lighting=True)
    pl.add_title(title_right, font_size=14)

    # 同步色标
    pl.link_views()

    pl.show()
```

---

## 4. 🟢 入门：矢量场（位移方向箭头）

### 4.1 位移矢量箭头

```python
def plot_displacement_vectors(mesh, displacement_vector, stride=50):
    """
    在网格上用箭头表示位移方向和大小。

    Args:
        mesh: PyVista UnstructuredGrid
        displacement_vector: shape (n_points, 3)
        stride: 每隔多少个点画一个箭头（避免太密）
    """
    # 取子集
    subset = mesh.extract_points(
        np.arange(0, mesh.n_points, stride)
    )

    # 对应的位移矢量
    vectors = displacement_vector[::stride]
    mag = np.sqrt(vectors[:, 0]**2 + vectors[:, 1]**2 + vectors[:, 2]**2)

    # 创建箭头
    arrows = pv.Arrow()   # 单个箭头的几何

    # 画网格 + 箭头
    pl = pv.Plotter(window_size=[1000, 800])
    pl.add_mesh(mesh, color="lightgray", show_edges=False, opacity=0.5)

    # 用 glyph 在每个点上放置箭头
    subset["vectors"] = vectors
    subset["magnitude"] = mag

    glyphs = subset.glyph(
        orient="vectors",
        scale="magnitude",
        factor=0.5,          # 缩放因子
        geom=pv.Arrow()
    )

    pl.add_mesh(glyphs, cmap="plasma", scalars="magnitude")
    pl.add_title("万神殿穹顶 · 位移矢量场")
    pl.show()
```

### 4.2 放大变形显示

```python
def plot_deformed_shape(mesh, displacement_vector, scale=100):
    """
    放大变形显示：将变形后的网格叠加在原网格上。

    scale=100 意味着 1mm 的实际位移在图中显示为 100mm。

    Args:
        mesh: 原始网格
        displacement_vector: 位移场
        scale: 变形放大倍数
    """
    # 创建变形后的网格
    deformed = mesh.copy()
    deformed.points += displacement_vector * scale

    pl = pv.Plotter(window_size=[1000, 800])

    # 原始网格：半透明灰色
    pl.add_mesh(mesh, color="lightgray", opacity=0.3,
                show_edges=False, label="原始形状（透明）")

    # 变形网格：彩色（按位移）
    disp_mag = np.sqrt(
        displacement_vector[:, 0]**2 +
        displacement_vector[:, 1]**2 +
        displacement_vector[:, 2]**2
    )
    deformed["disp"] = disp_mag

    pl.add_mesh(deformed, scalars="disp", cmap="plasma",
                show_edges=False, label=f"变形后（×{scale}）")

    pl.add_title(f"万神殿穹顶 · 变形图（放大×{scale}）")
    pl.add_legend()
    pl.show()
```

---

## 5. 🟢 入门：调整视角、颜色映射、色标

### 5.1 视角控制

```python
pl = pv.Plotter()

pl.add_mesh(mesh, scalars="sigma_1_MPa", cmap="RdBu_r")

# 预设视角
pl.camera_position = "xz"   # 从 XZ 平面看（侧视图）

# 或手动设置相机
pl.camera.position = (50, 0, 20)    # 相机位置
pl.camera.focal_point = (0, 0, 5)   # 看向哪里
pl.camera.up = (0, 0, 1)            # 向上的方向

# 万神殿穹顶的推荐视角：
# 侧视图：camera_position = 'xz'
# 俯视图：camera_position = 'xy'
# 45°视角：camera.position = (40, 40, 30)

pl.show()
```

### 5.2 颜色映射选择

| 数据类型 | 推荐 cmap | 说明 |
|---|---|---|
| 位移幅值（非负） | `"plasma"` / `"viridis"` / `"inferno"` | 感知均匀，从暗到亮 |
| 主应力（正负） | `"RdBu_r"` / `"coolwarm"` | 红正蓝负，白为零 |
| 开裂判定（二值） | `"cool"` + 自定义 clim | 开裂区暖色，安全区冷色 |
| 网格预览 | 无 cmap + 固定颜色 | `color="lightblue"` |

### 5.3 色标定制

```python
mesh.plot(
    scalars="sigma_1_MPa",
    cmap="RdBu_r",
    clim=[-1.0, 0.5],       # 手动设定色标范围
    below_color="blue",     # 低于下限的颜色
    above_color="red",      # 高于上限的颜色
    nan_color="gray",       # NaN 的颜色
    scalar_bar_args={
        "title": "σ₁ (MPa)",
        "n_labels": 7,
        "italic": True,
        "position_x": 0.85,
        "position_y": 0.1,
        "height": 0.6,
    }
)
```

---

## 6. 🟡 项目刚需：切面可视化（沿子午面切片）

### 6.1 沿子午面切片观察内部应力

```python
def plot_meridional_slice(mesh, scalars, phi=0, cmap="RdBu_r"):
    """
    沿子午面（θ = phi 平面）对穹顶做切片，观察内部应力分布。

    这很重要——穹顶外表面和内表面的应力可以差很多！
    切片让我们看到厚度方向的应力梯度。

    Args:
        mesh: PyVista UnstructuredGrid
        scalars: 标量场名称
        phi: 子午面角度（弧度），默认 0 = XZ 平面
    """
    # 创建切面
    # 子午面：包含 Z 轴的平面，由法向量定义
    # θ = phi → 法向量 = (sin(phi), -cos(phi), 0)
    normal = (np.sin(phi), -np.cos(phi), 0)
    origin = (0, 0, 0)   # 经过球心

    slice_mesh = mesh.slice(normal=normal, origin=origin)

    pl = pv.Plotter(window_size=[1200, 800])

    # 半透明的整体网格
    pl.add_mesh(mesh, color="lightgray", opacity=0.2, show_edges=False)

    # 切片（彩色云图）
    pl.add_mesh(slice_mesh, scalars=scalars, cmap=cmap,
                show_edges=False, lighting=True)

    pl.add_title(f"万神殿穹顶 · 子午面切片 (θ = {np.degrees(phi):.0f}°)")
    pl.show()
```

### 6.2 多层水平切片

```python
def plot_horizontal_slices(mesh, scalars, z_levels, cmap="RdBu_r"):
    """
    在不同高度做水平切片，观察应力随高度的变化。

    Args:
        mesh: PyVista UnstructuredGrid
        scalars: 标量场名称
        z_levels: 切片高度列表（从球心起算）
    """
    pl = pv.Plotter(window_size=[1200, 900])

    # 半透明整体
    pl.add_mesh(mesh, color="lightgray", opacity=0.15, show_edges=False)

    for z in z_levels:
        slice_mesh = mesh.slice(normal=(0, 0, 1), origin=(0, 0, z))
        pl.add_mesh(slice_mesh, scalars=scalars, cmap=cmap,
                    show_edges=False, lighting=True)

    pl.add_title("万神殿穹顶 · 多层水平切片")
    pl.show()
```

---

## 7. 🟡 项目刚需：筛选单元绘制开裂区域

### 7.1 高亮开裂区域

```python
def plot_cracked_regions(mesh, sigma_1, f_t=0.08e6):
    """
    高亮第一主应力超过抗拉强度的区域。

    Args:
        mesh: PyVista UnstructuredGrid
        sigma_1: 第一主应力 [Pa]
        f_t: 抗拉强度 [Pa]，默认 0.08 MPa
    """
    # 创建开裂掩码
    cracked_mask = sigma_1 > f_t

    # 提取开裂区域的单元
    # PyVista 提供 threshold 方法
    mesh_copy = mesh.copy()
    mesh_copy["sigma_1"] = sigma_1
    mesh_copy["cracked"] = cracked_mask.astype(float)

    pl = pv.Plotter(window_size=[1000, 800])

    # 完整网格：半透明灰色
    pl.add_mesh(mesh, color="lightgray", opacity=0.3,
                show_edges=False, label="完整穹顶")

    # 开裂区域：红色高亮
    cracked_mesh = mesh_copy.threshold(value=0.5, scalars="cracked")
    if cracked_mesh.n_cells > 0:
        pl.add_mesh(cracked_mesh, color="red", opacity=0.8,
                    show_edges=False, label="开裂区域 (σ₁ > f_t)")

    n_cracked_points = np.sum(cracked_mask)
    pct_cracked = 100 * n_cracked_points / len(sigma_1)

    pl.add_title(
        f"万神殿穹顶 · 开裂区域判定\n"
        f"开裂点数: {n_cracked_points} / {len(sigma_1)} ({pct_cracked:.1f}%)"
    )
    pl.add_legend()
    pl.show()
```

### 7.2 开裂区域 + 应力云图叠加

```python
def plot_stress_with_crack_overlay(mesh, sigma_1, f_t=0.08e6):
    """
    应力云图上叠加开裂区域轮廓。
    """
    mesh_copy = mesh.copy()
    sigma_1_mpa = sigma_1 / 1e6
    mesh_copy["sigma_1_MPa"] = sigma_1_mpa
    mesh_copy["cracked"] = (sigma_1 > f_t).astype(float)

    pl = pv.Plotter(window_size=[1000, 800])

    # 应力云图
    pl.add_mesh(mesh_copy, scalars="sigma_1_MPa", cmap="RdBu_r",
                clim=[-0.5, 0.5], show_edges=False, lighting=True)

    # 开裂区域轮廓线
    cracked = mesh_copy.threshold(value=0.5, scalars="cracked")
    if cracked.n_cells > 0:
        edges = cracked.extract_feature_edges(
            feature_angle=30, boundary_edges=True
        )
        pl.add_mesh(edges, color="black", line_width=3, label="开裂边界")

    pl.add_title("万神殿穹顶 · σ₁ 云图 + 开裂区域边界")
    pl.show()
```

---

## 8. 🟡 项目刚需：几何透明叠加（穹顶+鼓座同时展示）

```python
def plot_dome_and_drum(dome_mesh, drum_mesh,
                       dome_scalars=None, drum_scalars=None):
    """
    同时展示穹顶和鼓座，不同透明度区分。

    Args:
        dome_mesh: 穹顶网格
        drum_mesh: 鼓座网格
        dome_scalars: 穹顶上的标量场（如位移）
        drum_scalars: 鼓座上的标量场
    """
    pl = pv.Plotter(window_size=[1200, 900])

    # 鼓座：半透明 + 低调颜色
    if drum_scalars:
        drum_mesh_copy = drum_mesh.copy()
        drum_mesh_copy["scalars"] = drum_scalars
        pl.add_mesh(drum_mesh_copy, scalars="scalars",
                    cmap="Greys", opacity=0.6,
                    show_edges=False, label="鼓座")
    else:
        pl.add_mesh(drum_mesh, color="darkgray", opacity=0.4,
                    show_edges=False, label="鼓座")

    # 穹顶：不透明 + 彩色云图
    if dome_scalars:
        dome_mesh_copy = dome_mesh.copy()
        dome_mesh_copy["scalars"] = dome_scalars
        pl.add_mesh(dome_mesh_copy, scalars="scalars",
                    cmap="RdBu_r", opacity=0.9,
                    show_edges=False, label="穹顶")
    else:
        pl.add_mesh(dome_mesh, color="lightgray", opacity=0.8,
                    show_edges=False, label="穹顶")

    pl.add_title("万神殿 · 穹顶+鼓座耦合模型")
    pl.add_legend()
    pl.camera_position = "xz"
    pl.show()
```

---

## 9. 🟡 项目刚需：批量截图自动输出

### 9.1 多视角自动截图

```python
def batch_screenshot(mesh, scalars, output_dir, cmap="RdBu_r"):
    """
    批量生成多视角截图。

    Args:
        mesh: PyVista 网格
        scalars: 标量场名称
        output_dir: 输出目录
    """
    from pathlib import Path
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    views = {
        "front": "xz",
        "side": "yz",
        "top": "xy",
        "perspective": None,   # 默认视角
    }

    for name, view in views.items():
        pl = pv.Plotter(window_size=[1200, 900], off_screen=True)

        pl.add_mesh(mesh, scalars=scalars, cmap=cmap,
                    show_edges=False, lighting=True)

        if view:
            pl.camera_position = view
        else:
            pl.camera.position = (40, 40, 30)
            pl.camera.focal_point = (0, 0, 5)

        pl.add_title(f"万神殿穹顶 · {name.upper()} 视图")

        filepath = output_dir / f"dome_{scalars}_{name}.png"
        pl.screenshot(str(filepath))
        pl.close()
        print(f"  已保存: {filepath}")
```

### 9.2 论文级高质量截图

```python
def paper_quality_screenshot(mesh, scalars, output_path, title="",
                             cmap="RdBu_r", clim=None):
    """
    生成论文级高质量截图。

    Features:
      - 高分辨率（300 DPI）
      - 白色背景
      - 统一的字体大小
      - 无窗口边框
    """
    pl = pv.Plotter(
        window_size=[2000, 1500],   # 高分辨率
        off_screen=True
    )

    pl.add_mesh(mesh, scalars=scalars, cmap=cmap,
                clim=clim, show_edges=False,
                lighting=True, smooth_shading=True,
                specular=0.2, diffuse=0.8)

    pl.camera_position = "xz"

    if title:
        pl.add_title(title, font_size=20, color="black")

    pl.background_color = "white"

    pl.screenshot(
        output_path,
        return_img=False,
        scale=1,
    )
    pl.close()
    print(f"论文级截图已保存: {output_path}")
```

---

## 10. 🟡 项目刚需：动画旋转导出

```python
def export_rotation_animation(mesh, scalars, output_path,
                              n_frames=180, cmap="RdBu_r"):
    """
    导出旋转动画（GIF 或 MP4）。

    Args:
        mesh: PyVista 网格
        scalars: 标量场名称
        output_path: 输出文件路径（.gif 或 .mp4）
        n_frames: 帧数（360°旋转的总帧数）
    """
    # 创建动画文件
    pl = pv.Plotter(window_size=[800, 600], off_screen=True)

    pl.add_mesh(mesh, scalars=scalars, cmap=cmap,
                show_edges=False, lighting=True)

    pl.add_title("万神殿穹顶 · 旋转视图")

    # 打开 GIF/MP4 写入器
    pl.open_gif(str(output_path))

    # 旋转一圈
    for i in range(n_frames):
        angle = 360 * i / n_frames
        # 相机绕 Z 轴旋转
        radius = 50
        x = radius * np.cos(np.radians(angle))
        y = radius * np.sin(np.radians(angle))
        pl.camera.position = (x, y, 10)
        pl.camera.focal_point = (0, 0, 5)
        pl.camera.up = (0, 0, 1)

        pl.write_frame()

    pl.close()
    print(f"动画已导出: {output_path}")
```

---

## 11. 📦 完整可视化案例

```python
#!/usr/bin/env python3
"""
万神殿穹顶 · 完整可视化工作流
==============================
从 FEniCSx 结果到全套三维可视化输出。

输入：FEniCSx 求解结果（NumPy 数组）
输出：应力云图、位移矢量、开裂区域、切面图、多视角截图
"""

import numpy as np
import pyvista as pv
from pathlib import Path

# ============================================================
# 配置
# ============================================================
OUTPUT_DIR = Path("output/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

F_T = 0.08e6  # 抗拉强度 [Pa]

# ============================================================
# 模拟加载数据（实际使用中从 FEniCSx 结果读取）
# ============================================================
def load_fem_results():
    """模拟加载 FEM 结果（实际使用中替换为真实数据读取）"""
    # TODO: 从 .vtu / .bp / .npy 读取实际数据
    # 这里用随机数据做框架演示
    np.random.seed(42)

    # 创建简化的穹顶网格点
    R = 22.03
    phi_vals = np.linspace(0.2, np.pi/2, 30)   # 子午向 30 个点
    theta_vals = np.linspace(0, 2*np.pi, 80)   # 环向 80 个点

    points = []
    for phi in phi_vals:
        for theta in theta_vals:
            r = R + 2.0   # 近似在外表面
            x = r * np.sin(phi) * np.cos(theta)
            y = r * np.sin(phi) * np.sin(theta)
            z = r * np.cos(phi)
            points.append([x, y, z])

    points = np.array(points)

    # 生成模拟应力数据
    sigma_1 = np.zeros(len(points))
    for i, (phi, theta) in enumerate([(p, t) for p in phi_vals for t in theta_vals]):
        # 环向应力：底部受拉，顶部受压
        sigma_theta = -0.5e6 * np.cos(2 * phi)   # 底部拉，顶部压
        sigma_1[i] = sigma_theta

    disp = np.random.normal(0, 0.002, (len(points), 3))
    disp[:, 2] -= 0.005   # 总体向下

    return points, sigma_1, disp

# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60)
    print("  万神殿穹顶 · 三维可视化工作流")
    print("=" * 60)

    # 1. 加载数据
    print("\n[1/6] 加载 FEM 结果...")
    points, sigma_1, disp = load_fem_results()
    print(f"  节点数: {len(points)}")

    # 2. 创建 PyVista 点云（简化演示）
    print("\n[2/6] 创建可视化数据...")
    cloud = pv.PolyData(points)
    cloud["sigma_1_MPa"] = sigma_1 / 1e6
    cloud["disp_mag_mm"] = np.sqrt(disp[:, 0]**2 + disp[:, 1]**2 + disp[:, 2]**2) * 1000

    # 3. 应力云图
    print("\n[3/6] 生成第一主应力云图...")
    pl = pv.Plotter(window_size=[1000, 800], off_screen=True)
    pl.add_mesh(cloud, scalars="sigma_1_MPa", cmap="RdBu_r",
                clim=[-0.5, 0.5], point_size=8,
                render_points_as_spheres=True)
    pl.add_title("万神殿穹顶 · 第一主应力 σ₁ (MPa)")
    pl.camera_position = "xz"
    pl.screenshot(str(OUTPUT_DIR / "stress_sigma1.png"))
    pl.close()
    print("  → output/figures/stress_sigma1.png")

    # 4. 位移云图
    print("\n[4/6] 生成位移幅值云图...")
    pl = pv.Plotter(window_size=[1000, 800], off_screen=True)
    pl.add_mesh(cloud, scalars="disp_mag_mm", cmap="plasma",
                point_size=8, render_points_as_spheres=True,
                clim=[0, 20])
    pl.add_title("万神殿穹顶 · 位移幅值 (mm)")
    pl.camera_position = "xz"
    pl.screenshot(str(OUTPUT_DIR / "displacement.png"))
    pl.close()
    print("  → output/figures/displacement.png")

    # 5. 开裂区域高亮
    print("\n[5/6] 判定并高亮开裂区域...")
    cracked_mask = sigma_1 > F_T
    n_cracked = np.sum(cracked_mask)
    pct = 100 * n_cracked / len(sigma_1)

    pl = pv.Plotter(window_size=[1000, 800], off_screen=True)

    # 安全区域
    safe = cloud.extract_points(np.where(~cracked_mask)[0])
    pl.add_mesh(safe, color="lightgray", opacity=0.3, point_size=8,
                render_points_as_spheres=True)

    # 开裂区域
    if n_cracked > 0:
        cracked = cloud.extract_points(np.where(cracked_mask)[0])
        pl.add_mesh(cracked, color="red", opacity=0.8, point_size=10,
                    render_points_as_spheres=True)

    pl.add_title(f"万神殿穹顶 · 开裂区域 (σ₁ > {F_T/1e6:.2f} MPa)\n"
                 f"开裂比例: {pct:.1f}%")
    pl.camera_position = "xz"
    pl.screenshot(str(OUTPUT_DIR / "cracked_regions.png"))
    pl.close()
    print(f"  → output/figures/cracked_regions.png")
    print(f"  开裂比例: {pct:.1f}%")

    # 6. 汇总
    print(f"\n{'='*60}")
    print(f"  ✅ 可视化完成！")
    print(f"  产出文件: {OUTPUT_DIR}/")
    for f in sorted(OUTPUT_DIR.glob("*.png")):
        print(f"    - {f.name}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
```

---

## 12. 常见错误与坑点

### 12.1 数据缩放错误

**症状**：应力云图色标显示 MPa 但数据是 Pa → 全是几百几千。

**解决**：统一单位。
```python
# 应力：FEniCSx 输出的单位是 Pa
# 显示时转为 MPa
sigma_mpa = sigma / 1e6

# 位移：FEniCSx 输出的单位是 m
# 显示时转为 mm
disp_mm = disp * 1000
```

### 12.2 色标范围不一致

**症状**：对比 C1 和 C2 时，两图色标范围不同 → 无法直接对比。

**解决**：手动统一 `clim`。
```python
# 固定色标范围
vmin = -0.5  # MPa
vmax = 0.5

plotter.add_mesh(mesh_c1, scalars="sigma_1", cmap="RdBu_r",
                 clim=[vmin, vmax])
plotter.add_mesh(mesh_c2, scalars="sigma_1", cmap="RdBu_r",
                 clim=[vmin, vmax])
```

### 12.3 渲染窗口黑屏（WSL2）

**症状**：`.plot()` 弹出窗口但一片黑。

**解决方案**：
```python
# 使用离屏渲染保存为 PNG
pl = pv.Plotter(off_screen=True)
pl.add_mesh(mesh, ...)
pl.screenshot("output.png")
pl.close()
```

### 12.4 大模型渲染卡顿

**症状**：80 万单元的网格，旋转视角卡成幻灯片。

**解决方案**：
- 使用 `.decimate()` 降低面片数
- 使用 `extract_surface()` 只渲染外表面
- 减小 `window_size`

---

## 13. PyVista 审核自查清单

- [ ] 应力云图中色标单位是否正确（MPa 而非 Pa）？
- [ ] 位移云图中最大位移位置是否在穹顶顶部（离约束最远）？
- [ ] C1 和 C2 对比图的色标是否统一？
- [ ] 开裂区域判定使用的 f_t = 0.08 MPa 是否正确？
- [ ] 子午面切片图是否能清晰显示厚度方向的应力梯度？
- [ ] 所有截图是否包含标题和色标？
- [ ] 动画/截图的分辨率是否满足报告要求（≥ 1920×1080）？

---

> **下一篇**：文档7 — Matplotlib FEM 数据二维定量分析。PyVista 负责三维云图，Matplotlib 负责二维定量曲线——子午线应力分布、双模型对比、网格收敛曲线。

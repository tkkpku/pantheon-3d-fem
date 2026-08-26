# 文档5 · FEniCSx 有限元求解完全教程（重构版）

> **项目**：万神殿穹顶三维 FEM 重构
> **版本**：v2.0 轮次 1/10（2026-08-13 逐轮重写）
> **前置要求**：文档3（FEM 基础）、文档4（Gmsh 已生成 .msh）
> **配套环境**：WSL2 `pantheon-fem`（dolfinx 0.8.0）

---

## 写给你的使用说明（30 秒读完）

文档4 负责「把几何变成网格」，文档5 负责「把网格变成结果」。

这本教材的核心任务只有一件：**让你理解并写出 FEniCSx 求解代码**——读入网格、定义函数空间、写弱形式、施加边界条件、求解、输出应力。

- 每一章一个主题，从「跑通一个最简程序」开始，逐步逼近 C1 算例；
- 每个概念都先讲物理/数学直觉，再给代码；
- 每个代码示例都标注「运行方法」和「预期输出」；
- 文档3 的概念（弱形式、试函数/测试函数、自由度）会反复出现——**忘记就回文档3 查**。

### 🎩 老板版速读（60 秒，Leader 必读）

你不需要写求解代码，但要会**审 AI 写的求解脚本**。只记三件事：

1. **七步骨架**：读网格 → 函数空间 → 边界条件 → 试/测试函数 → 弱形式 → 求解 → 输出。缺 BC = 奇异矩阵报错；
2. **三个高频翻车点**：单位必须全 SI（m/Pa/kg）；dolfinx 0.8 的 BC 值用 `fem.Constant`（矢量空间用 `(0,0,0)`）；物理组标签必须和 Gmsh 对得上（400=拱脚）；
3. **验收量级**：位移 mm 级、应力 MPa 级；σ1 对照抗拉强度 0.08 MPa——超了就说明该上非线性模型。

审代码时问 AI 三个问题：BC 施加在哪？自重方向对吗？网格无关性做了吗？

**学完这本教材，你应该能**：

1. 把 Gmsh 导出的 `.msh` 读进 FEniCSx；
2. 写出标量和矢量函数空间；
3. 用物理组标签施加 Dirichlet 边界条件；
4. 写出线弹性弱形式（UFL 代码）；
5. 求解球壳自重问题，并输出应力张量。

---

## 第 0 章 学习地图

### 0.1 全书地图

| 章 | 内容 | 难度 | 对应能力 |
| --- | --- | --- | --- |
| 第 1 章 | FEniCSx 是什么 + 环境自检 | 🟢 | 热身 |
| 第 2 章 | 第一个求解程序：泊松方程 | 🟢 | 1 |
| 第 3 章 | 函数空间：标量/矢量/自由度 | 🟡 | 2 |
| 第 4 章 | 边界条件：物理组对接 | 🟡 | 3 |
| 第 5 章 | 弱形式与 UFL 语法 | 🔴 | 4 |
| 第 6 章 | 线弹性：从泊松到弹性力学 | 🔴 | 4 |
| 第 7 章 | 自重施加与求解器参数 | 🟡 | 4 |
| 第 8 章 | 应力后处理输出 | 🟡 | 5 |
| 第 9 章 | C1 实战：球壳自重线弹性 | 🔴 | 全部 |
| 第 10 章 | 进阶：干缩、非线性、坑点 | 🔴 | 延伸 |
| 附录 | 术语表、公式、审核清单 | 🟢 | 工具 |

### 0.2 学习路线

- **主线**：第 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 章；
- **支线**：第 10 章（C2/C4 时再精读）；
- **工具**：附录。

主线约 10 个番茄钟。第 5、6 章（UFL 和线弹性）是重点，值得各花 2 个番茄钟。

### 0.3 环境自检

在 WSL 终端：

```bash
conda activate pantheon-fem
python -c "import dolfinx; print(dolfinx.__version__)"
```

预期输出（版本可能略不同）：

```text
0.8.0
```

如果报 `ModuleNotFoundError`，回文档0 补环境。

---

## 第 1 章 FEniCSx 是什么

### 1.1 一句话版本

**FEniCSx 是一个开源有限元求解框架：你把「网格 + 弱形式 + 边界条件」告诉它，它自动完成单元分析、组装、求解，返回位移场。**

### 1.2 它在流水线里的位置

```text
Gmsh（文档4）→ .msh 网格 → FEniCSx（本文档）→ 结果（.vtu）
                                     ↓
                              PyVista / Matplotlib（文档6、7）
```

FEniCSx 自动替你完成了文档3 讲的三件事：

1. **单元分析**：对每个四面体算单元刚度矩阵；
2. **组装**：拼成整体 $K u = f$；
3. **求解**：解方程组，得到节点位移。

### 1.3 为什么是 FEniCSx（而不是自己写代码）？

你当然可以自己写一个 FEM 求解器——但万神殿模型有几十万自由度、二阶四面体、复杂边界。自己写：

- 需要处理稀疏矩阵、编号、积分规则——几个月工作量；
- 容易出错，且错误隐蔽。

FEniCSx 把这些全部封装好，你只需要描述**数学问题**（弱形式），不用管底层数值细节——这就是「以数学为中心」的框架。

### 1.4 七步总骨架（本书的脊柱）

```python
# 1. 读入网格（.msh）
# 2. 定义函数空间 V
# 3. 定义边界条件（BC）
# 4. 定义试函数 u 和测试函数 v
# 5. 写弱形式 a(u,v) = L(v)
# 6. 求解
# 7. 后处理/导出
```

后面每一章都是把某一步展开讲透。

### 1.5 本章小结

1. FEniCSx = 读网格 + 写弱形式 + 求解；
2. 它自动做单元分析和组装（文档3 的三、四步）；
3. 你只需描述数学问题，不碰底层细节；
4. 七步骨架贯穿全书。

### 1.6 小练习

1. 跑通环境自检，记录版本号；
2. 说出七步骨架的每一步（默写）；
3. 用自己的话：FEniCSx 相比自己写 FEM 代码，省了什么？

---

## 第 2 章 第一个求解程序：一维/二维泊松方程

### 2.1 本章目标

跑通 FEniCSx 最经典的入门例子：**泊松方程（Poisson's equation）**，理解七步骨架的完整代码形态。

### 2.2 泊松方程是什么

$$-\nabla^2 u = f$$

- $u$：未知场（比如温度、电势、位移势）；
- $f$：源项；
- 边界上 $u = 0$（Dirichlet BC）。

**弱形式**（文档3 的套路：乘以测试函数 $v$ 再积分）：

$$\int_\Omega \nabla u \cdot \nabla v\, dx = \int_\Omega f\, v\, dx$$

左边 $a(u,v)$，右边 $L(v)$——这是 FEniCSx 代码的直接蓝本。

### 2.3 完整代码

保存为 `fem_solver/demo_poisson.py`：

```python
"""
FEniCSx 入门：单位正方形上的泊松方程
  -∇²u = f,  u = 0 on boundary
"""
from dolfinx import mesh, fem
from dolfinx.fem import petsc
import ufl
from mpi4py import MPI

# 1. 创建网格：10×10 单位正方形
domain = mesh.create_unit_square(MPI.COMM_WORLD, 10, 10)

# 2. 定义函数空间：一阶 Lagrange 标量空间
V = fem.functionspace(domain, ("Lagrange", 1))

# 3. 边界条件：所有边界 u = 0
def boundary(x):
    return (x[0] < 1e-8) | (x[0] > 1 - 1e-8) | \
           (x[1] < 1e-8) | (x[1] > 1 - 1e-8)

dofs = fem.locate_dofs_geometrical(V, boundary)
bc = fem.dirichletbc(fem.Constant(domain, 0.0), dofs, V)

# 4. 试函数和测试函数
u = ufl.TrialFunction(V)
v = ufl.TestFunction(V)

# 5. 弱形式：∫∇u·∇v dx = ∫f·v dx
f = fem.Constant(domain, 1.0)
a = ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx
L = f * v * ufl.dx

# 6. 求解
problem = petsc.LinearProblem(a, L, bcs=[bc])
uh = problem.solve()

# 7. 输出结果
# ⚠️ 口径注记：size_global 是「标量」自由度（标量元=节点数；矢量元要 ×分量）。
#    例：C1 的 ("Lagrange",2,(3,)) 打印 18242 = 节点数，真实矢量未知量 = 18242×3 = 54726。
print("求解完成，自由度 =", V.dofmap.index_map.size_global)
```

### 2.4 逐行拆解（七步对号入座）

| 行 | 代码 | 对应骨架 | 白话 |
| --- | --- | --- | --- |
| 1 | `create_unit_square` | 第 1 步 | 造一个 10×10 正方形网格 |
| 2 | `functionspace(...)` | 第 2 步 | 定义「解长什么样」的空间 |
| 3 | `locate_dofs_geometrical` | 第 3 步 | 找到边界上的自由度 |
| 4 | `dirichletbc` | 第 3 步 | 令边界自由度 = 0 |
| 5 | `ufl.TrialFunction(V)` | 第 4 步 | 试函数 u（未知） |
| 6 | `ufl.TestFunction(V)` | 第 4 步 | 测试函数 v（检验尺） |
| 7 | `ufl.inner(...)*ufl.dx` | 第 5 步 | 写弱形式左端 |
| 8 | `f * v * ufl.dx` | 第 5 步 | 写弱形式右端 |
| 9 | `petsc.LinearProblem` | 第 6 步 | 组装 + 求解 |
| 10 | `problem.solve()` | 第 6 步 | 得到解 uh |

### 2.5 运行与预期输出

```bash
conda activate pantheon-fem
cd /mnt/c/Users/tan83/Desktop/codex/pantheon-3d-fem
python fem_solver/demo_poisson.py
```

预期输出（数字可能略不同）：

```text
求解完成，自由度 = 121
```

10×10 网格 → 11×11 节点 → 121 个自由度（一阶标量），对！

### 2.6 三个必做实验

**实验 A：加密网格**。把 `10, 10` 改成 `20, 20`，自由度变成多少？（答案：441）

**实验 B：改源项**。把 `f = fem.Constant(domain, 1.0)` 改成 `f = fem.Constant(domain, 2.0)`，观察结果变化。

**实验 C：去掉边界条件**。注释掉 `bc` 和 `bcs=[bc]`，运行——大概率报「奇异矩阵」错误。这正是文档3 讲的：**没有边界条件，K 不可逆**。

### 2.7 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `ModuleNotFoundError: dolfinx` | 环境不对 | `conda activate pantheon-fem` |
| 求解报奇异矩阵 | 忘了边界条件 | 检查 bc |
| 自由度数和预期差 1 | 网格节点数算错 | 11×11=121 |
| MPI 相关报错 | WSL 环境 MPI 未配好 | 回文档0 检查 mpi4py |

### 2.8 本章小结

1. 泊松方程是 FEniCSx 的「hello world」；
2. 七步骨架：网格 → 空间 → BC → 试/测函数 → 弱形式 → 求解 → 输出；
3. `ufl.dx` 表示「在整个域上积分」；
4. 没有边界条件 = 奇异矩阵报错。

### 2.9 小练习

1. 把网格加密到 50×50，记录自由度；
2. 解释 `locate_dofs_geometrical` 在干什么（用白话）；
3. 默写七步骨架的代码关键词。

---

## 第 3 章 函数空间：解的「舞台」

### 3.1 本章目标

1. 理解函数空间 V 是什么、为什么先定义它；
2. 掌握一阶/二阶 Lagrange 空间的区别；
3. 掌握标量空间与矢量空间的写法；
4. 理解自由度（DOF）与空间的关系。

### 3.2 空间是什么：解的「允许长相」

函数空间 $V$ 规定了「解可以长什么样」。就像戏剧开演前先定舞台——**舞台定了，演员（解）只能在舞台上活动**。

`functionspace(domain, ("Lagrange", 1))` 的意思是：

- `domain`：在哪个网格上演；
- `Lagrange`：用拉格朗日插值（文档3 第 6 章讲的形函数家族）；
- `1`：单元内部位移按**一次（线性）**函数变化。

### 3.3 一阶 vs 二阶

| 阶次 | 单元内部变化 | 每单元节点数（四面体） | 精度 |
| --- | --- | --- | --- |
| 1（线性） | 直线/平面 | 4 | 较低 |
| 2（二次） | 曲线/曲面 | 10 | 高（本项目用） |

```python
# 一阶标量空间
V1 = fem.functionspace(domain, ("Lagrange", 1))

# 二阶标量空间
V2 = fem.functionspace(domain, ("Lagrange", 2))
```

**文档3 的关键结论在这里体现**：二阶 = 每个单元 10 个节点 = 形函数更高阶 = 插值更准 = 网格可以更粗。

### 3.4 标量 vs 矢量

泊松方程解的是温度/电势——**标量**（一个数）。

弹性力学解的是位移——**矢量**（三个分量 $u_x, u_y, u_z$）。

```python
# 标量空间：一个分量
V_scalar = fem.functionspace(domain, ("Lagrange", 2))

# 三维矢量空间：每个节点 3 个分量（shape=(3,)）
V_vector = fem.functionspace(domain, ("Lagrange", 2, (3,)))
```

**写法对比**：

| 空间 | 代码 | 每节点自由度 |
| --- | --- | --- |
| 一阶标量 | `("Lagrange", 1)` | 1 |
| 二阶标量 | `("Lagrange", 2)` | 1 |
| 二阶三维矢量 | `("Lagrange", 2, (3,))` | 3 |
| 二阶对称张量 | `("Lagrange", 2, (3,3))` | 6（对称） |

> **万神殿的位移空间**：`("Lagrange", 2, (3,))`——二阶 × 3 分量。这就是文档4 说的「每单元 30 自由度」的来源。

### 3.5 自由度：空间有多大

```python
print("自由度 =", V.dofmap.index_map.size_global)
```

自由度数量 = 节点数 × 每节点分量数（近似，边界可能有差异）。

**手算验证**（10×10 一阶标量）：

$$11 \times 11 \times 1 = 121$$

与第 2 章实测一致。

### 3.6 选择空间的三条经验

1. **位移用矢量空间**：`("Lagrange", 2, (3,))`；
2. **标量场（温度、压力）用标量空间**：`("Lagrange", 1/2)`；
3. **应力/应变用对称张量空间**：`("Lagrange", 1, (3,3))`（后处理用）。

### 3.7 本章小结

1. 函数空间 = 解的「舞台」，决定插值阶次和分量数；
2. 一阶 = 4 节点直边，二阶 = 10 节点曲边（本项目）；
3. 矢量空间写法：`("Lagrange", 2, (3,))`；
4. 自由度 = 节点数 × 每节点分量数。

### 3.8 小练习

1. 打印一个二阶三维矢量空间的自由度（用 10×10 网格）；
2. 解释：为什么二阶空间能「用更粗网格达到同样精度」；
3. 默写三种空间的定义代码。

---

## 第 4 章 边界条件：让 FEniCSx 认得出「哪里固定」

### 4.1 本章目标

1. 理解 Gmsh 物理组 → FEniCSx 边界条件的完整链路；
2. 掌握从 `.msh` 读取网格和物理组标签的方法；
3. 掌握 `locate_dofs_topological` + `dirichletbc` 的标准写法。

### 4.2 先看全景：物理组怎么「旅行」

```text
Gmsh:  addPhysicalGroup(2, [tag], tag=400, name="dome_base")
              ↓ 写入 .msh 文件
FEniCSx: 读取网格时拿到 网格+物理组标签
              ↓
         用 tag=400 找到拱脚面
              ↓
         在该面上所有自由度施加 u=0（Dirichlet BC）
```

文档4 第 7 章贴的每个标签，在这里全部派上用场。

### 4.3 读取网格和标签

FEniCSx 读 `.msh` 需要 `dolfinx.io.gmshio`：

```python
from dolfinx.io import gmshio
from mpi4py import MPI

# 读入 Gmsh 网格：返回 (网格, 体标签, 面标签)
domain, cell_tags, facet_tags = gmshio.read_from_msh(
    "output/meshes/c0_shell_groups.msh",
    MPI.COMM_WORLD,
    gdim=3,          # 几何维度：三维
)
```

三个返回值：

| 返回值 | 含义 | 对应 Gmsh |
| --- | --- | --- |
| `domain` | 网格对象 | 节点+单元 |
| `cell_tags` | 体上的物理组标签（1000=穹顶体） | 3D 物理组 |
| `facet_tags` | 面上的物理组标签（400=拱脚面） | 2D 物理组 |

### 4.4 查看有哪些物理组

```python
import numpy as np

# 体标签有哪些
cell_ids = np.unique(cell_tags.values)
print("体物理组:", cell_ids)

# 面标签有哪些
facet_ids = np.unique(facet_tags.values)
print("面物理组:", facet_ids)
```

预期输出（对应文档4 第 7.4 表）：

```text
体物理组: [1000]
面物理组: [200 300 400]
```

### 4.5 施加 Dirichlet 边界条件：标准三步

**目标**：拱脚面（tag=400）位移全固定（$u_x=u_y=u_z=0$）。

```python
from dolfinx import fem
import ufl

# 第 1 步：找到属于物理组 400 的「面单元」
facets = facet_tags.find(400)

# 第 2 步：由面单元找到该面上的自由度
dofs = fem.locate_dofs_topological(V, 2, facets)

# 第 3 步：令这些自由度 = 0
bc = fem.dirichletbc(fem.Constant(domain, (0.0, 0.0, 0.0)), dofs, V)
```

**参数解释**：

| 参数 | 含义 |
| --- | --- |
| `V` | 函数空间（矢量空间时自动处理 3 个分量） |
| `2` | 维度 = 面（1=线，2=面，3=体） |
| `facets` | 目标面的编号数组 |

> 注意：对矢量空间，BC 值必须是**矢量常量** `(0.0, 0.0, 0.0)`，三个分量一起固定。如果只想固定某个方向，用 `fem.Function` 写法（第 4.6 节）。

### 4.6 只固定 Z 方向（进阶）

```python
# 用函数定义：只有 z 分量 = 0，其他自由
u_bc = fem.Function(V)
u_bc.sub(2).x.array[:] = 0.0   # z 方向（下标 2）

bc = fem.dirichletbc(u_bc, dofs)
```

`sub(0/1/2)` 分别对应 $u_x, u_y, u_z$——这是 FEniCSx 里处理矢量分量的标准方式。

### 4.7 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `facet_tags.find(400)` 为空 | Gmsh 没贴 400 标签 | 回文档4 检查物理组 |
| 找不到 500/600 等标签 | 布尔后标签失效 | 回文档4 第 7.8 节 |
| `dirichletbc` 类型报错 | 值类型不对 | 用 `fem.Constant`（标量/矢量）或 `fem.Function` |
| 读取后维度不对 | `gdim` 写错 | 三维模型写 `gdim=3` |

### 4.8 本章小结

1. 链路：Gmsh 物理组 → .msh → `gmshio.read_from_msh` → 标签数组；
2. 三步 BC：`find(400)` 找面 → `locate_dofs_topological` 找自由度 → `dirichletbc` 赋值；
3. `facet_tags` 管面（边界），`cell_tags` 管体（材料）；
4. 矢量空间下标量 BC 自动作用于全部分量。

### 4.9 小练习

1. 用第 2 章的泊松程序，把 `locate_dofs_geometrical` 改成基于网格标签的方式（提示：先给单位正方形手工加标签，或用 Gmsh 导出的带标签网格）；
2. 打印 `facet_ids`，确认与文档4 第 7.4 表的编号一致；
3. 解释三步 BC 中「面 → 自由度」这一步在干什么。

---

## 第 5 章 UFL 弱形式语法：用代码写数学

### 5.1 本章目标

1. 理解 UFL（Unified Form Language）是「用 Python 写数学公式」的语言；
2. 掌握核心语法：TrialFunction / TestFunction、grad、inner、dx、ds；
3. 掌握弹性力学专用：sym、tr、Identity；
4. 能把文档3 的弱形式翻译成 UFL 代码。

### 5.2 UFL 是什么

UFL 是 FEniCSx 内置的**形式语言**：你用接近数学的写法描述弱形式，FEniCSx 自动完成积分、求导、组装。

数学公式：

$$\int_\Omega \nabla u \cdot \nabla v\, dx$$

UFL 代码：

```python
ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx
```

**几乎一一对应**，这就是 UFL 的设计哲学。

### 5.3 核心词汇表（先背这 8 个）

| UFL 代码 | 数学含义 | 白话 |
| --- | --- | --- |
| `ufl.TrialFunction(V)` | 试函数 $u$ | 未知解 |
| `ufl.TestFunction(V)` | 测试函数 $v$ | 检验尺子 |
| `ufl.grad(u)` | $\nabla u$ | 梯度（位移→应变用） |
| `ufl.inner(a, b)` | $a : b$ | 张量全收缩（对应相乘相加） |
| `ufl.sym(A)` | $\frac{1}{2}(A+A^T)$ | 对称部分 |
| `ufl.tr(A)` | $\mathrm{tr}(A)$ | 迹（对角线和） |
| `ufl.Identity(n)` | $n\times n$ 单位矩阵 | 常数张量 |
| `ufl.dx` / `ufl.ds` | 体积分/面积分 | 在整个域/边界上积分 |

### 5.4 梯度：从位移到应变

对矢量场 $u = (u_x, u_y, u_z)$，`grad(u)` 返回 3×3 矩阵：

$$\nabla u =
\begin{bmatrix}
\partial u_x/\partial x & \partial u_x/\partial y & \partial u_x/\partial z \\
\partial u_y/\partial x & \partial u_y/\partial y & \partial u_y/\partial z \\
\partial u_z/\partial x & \partial u_z/\partial y & \partial u_z/\partial z
\end{bmatrix}$$

**小变形应变**（文档3 第 7 章）：

$$\varepsilon(u) = \frac{1}{2}\big(\nabla u + (\nabla u)^T\big)$$

UFL：

```python
epsilon = ufl.sym(ufl.grad(u))
```

### 5.5 线弹性弱形式的完整翻译

文档3 第 7 章的弱形式：

$$\int_\Omega \sigma(u) : \varepsilon(v)\, dx = \int_\Omega b \cdot v\, dx + \int_\Gamma t \cdot v\, ds$$

UFL 逐段翻译：

```python
# 应变（位移 → 应变）
def epsilon(u):
    return ufl.sym(ufl.grad(u))

# 应力（本构：线弹性）
def sigma(u):
    lam = fem.Constant(domain, lam_value)
    mu  = fem.Constant(domain, mu_value)
    return lam * ufl.tr(epsilon(u)) * ufl.Identity(3) + 2 * mu * epsilon(u)

# 弱形式
a = ufl.inner(sigma(u), epsilon(v)) * ufl.dx      # 内力虚功
L = ufl.dot(b, v) * ufl.dx + ufl.dot(t, v) * ufl.ds  # 外力虚功
```

**对照表**：

| 数学 | UFL |
| --- | --- |
| $\sigma : \varepsilon$ | `ufl.inner(sigma(u), epsilon(v))` |
| $\int_\Omega (\cdot)\,dx$ | `* ufl.dx` |
| $\int_\Gamma (\cdot)\,ds$ | `* ufl.ds` |
| $\boldsymbol{I}$ | `ufl.Identity(3)` |
| $\mathrm{tr}(\varepsilon)$ | `ufl.tr(epsilon(u))` |
| $b \cdot v$ | `ufl.dot(b, v)` |

### 5.6 子域积分：dx(标签) 和 ds(标签)

默认 `ufl.dx` 在整个域积分。想只在某个物理组区域积分：

```python
a = ufl.inner(...) * ufl.dx(1000)   # 只在物理组 1000（穹顶体）积分
L = ufl.dot(t, v) * ufl.ds(400)     # 只在物理组 400（拱脚面）积分
```

**用途**：

- `dx(材料标签)`：不同区域不同材料；
- `ds(面标签)`：只在该面上施加面力。

### 5.7 常见错误

| 报错/现象 | 原因 | 解决 |
| --- | --- | --- |
| `ufl` 未定义 | 忘了 `import ufl` | 补上 |
| `TrialFunction` 报维度错 | 空间和函数的维度不匹配 | 位移用矢量空间 |
| `inner` 用法错 | 用成 `*` 标量乘法 | 张量间用 `inner`，标量用 `*` |
| 积分符号缺失 | 表达式后没写 `* ufl.dx` | 每个积分项必须带 `dx/ds` |

### 5.8 本章小结

1. UFL = 用 Python 写数学，公式和代码几乎一一对应；
2. 8 个核心词汇：Trial/Test、grad、inner、sym、tr、Identity、dx/ds；
3. 线弹性 = `sym(grad(u))` → `lambda*tr(ε)*I + 2μ*ε` → `inner(σ, ε)*dx`；
4. `dx(标签)` 指定子域，`ds(标签)` 指定边界面。

### 5.9 小练习

1. 手写：把 $\int_\Omega \varepsilon(u):\varepsilon(v)\,dx$ 翻译成 UFL；
2. 解释 `ufl.Identity(3)` 在应力公式里的作用；
3. 说出 `ufl.dx(1000)` 和 `ufl.ds(400)` 分别在哪个物理组积分。

---

## 第 6 章 线弹性：从泊松到弹性力学

### 6.1 本章目标

1. 写出完整的线弹性求解代码（矢量空间 + UFL）；
2. 掌握 Lamé 常数从 $E, \nu$ 的计算；
3. 理解「自重体积力」的 UFL 写法；
4. 学会配置求解器参数。

### 6.2 完整代码：单位立方体自重线弹性

先不看万神殿，用一个 1×1×1 立方体跑通全部要素：

```python
"""
线弹性完整示例：单位立方体，底面固定，自重
"""
from dolfinx import mesh, fem
from dolfinx.fem import petsc
import ufl
import numpy as np
from mpi4py import MPI

# ============ 1. 网格 ============
domain = mesh.create_unit_cube(MPI.COMM_WORLD, 2, 2, 2)

# ============ 2. 矢量函数空间（二阶 × 3 分量） ============
V = fem.functionspace(domain, ("Lagrange", 2, (3,)))

# ============ 3. 边界条件：底面固定 ============
def bottom(x):
    return x[2] < 1e-8      # z=0 附近

dofs = fem.locate_dofs_geometrical(V, bottom)
bc = fem.dirichletbc(fem.Constant(domain, (0.0, 0.0, 0.0)), dofs, V)

# ============ 4. 材料参数（文档3 公式） ============
E = fem.Constant(domain, 14.8e9)     # 弹性模量 Pa
nu = fem.Constant(domain, 0.2)       # 泊松比
lam = E * nu / ((1 + nu) * (1 - 2 * nu))
mu = E / (2 * (1 + nu))

# ============ 5. 弱形式 ============
u = ufl.TrialFunction(V)
v = ufl.TestFunction(V)

def epsilon(w):
    return ufl.sym(ufl.grad(w))

def sigma(w):
    return lam * ufl.tr(epsilon(w)) * ufl.Identity(3) + 2 * mu * epsilon(w)

# 自重：重力向下（-z），密度 ρ × g
rho = fem.Constant(domain, 1600.0)   # kg/m^3
g = fem.Constant(domain, 9.81)       # m/s^2
b = ufl.as_vector([0.0, 0.0, -rho * g])

a = ufl.inner(sigma(u), epsilon(v)) * ufl.dx
L = ufl.dot(b, v) * ufl.dx

# ============ 6. 求解 ============
problem = petsc.LinearProblem(a, L, bcs=[bc])
uh = problem.solve()

# ============ 7. 结果 ============
print("求解完成")
print("最大 |位移| =", np.max(np.abs(uh.x.array)))
```

### 6.3 逐块拆解

**材料与 Lamé 常数**：

```python
lam = E * nu / ((1 + nu) * (1 - 2 * nu))
mu  = E / (2 * (1 + nu))
```

这就是文档3 第 7.6 节的两个公式，直接翻译成代码。用 `fem.Constant` 包装，方便后续改参数。

**本构函数**：

```python
def sigma(w):
    return lam * ufl.tr(epsilon(w)) * ufl.Identity(3) + 2 * mu * epsilon(w)
```

$$\boldsymbol{\sigma} = \lambda\,\mathrm{tr}(\varepsilon)\boldsymbol{I} + 2\mu\varepsilon$$

逐项对应，一个字母都不差。

**自重体积力**：

```python
b = ufl.as_vector([0.0, 0.0, -rho * g])
```

- 重力方向是 $-z$（向下），所以 z 分量带负号；
- `rho` 是密度（1600 kg/m³，文档3 第 9.3 表的下区密度）；
- 真实的万神殿密度是分层的（1350/1500/1600），第 7 章处理。

### 6.4 求解器参数（什么时候需要调）

默认 `petsc.LinearProblem` 一般够用。遇到不收敛/太慢时：

```python
problem = petsc.LinearProblem(
    a, L, bcs=[bc],
    petsc_options={
        "ksp_type": "preonly",          # 直接求解
        "pc_type": "lu",                # LU 分解
    },
)
```

**建议**：小模型（C0/C1 粗网格）用 `preonly + lu` 最稳；大模型再考虑迭代求解器（`cg + amg`）。

### 6.5 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 位移全为零 | 忘记自重项或 b 写反 | 检查 L 表达式和符号 |
| 位移巨大（量级错误） | 单位混用 | 全部 SI：Pa、kg/m³、m |
| 不收敛/奇异 | 约束不足 | 检查 BC 是否覆盖刚体位移 |
| 应力是零 | 只解了位移没算应力 | 第 8 章 |

### 6.6 本章小结

1. 线弹性三件套：Lamé 常数 → sigma 函数 → `inner(σ, ε)*dx`；
2. 自重 = `ufl.as_vector([0, 0, -ρg])`；
3. 位移是主解，应力要额外后处理；
4. 求解器默认即可，小模型用 LU 最稳。

### 6.7 小练习

1. 跑通 6.2 代码，记录最大位移（提示：单位是 m，应该很小）；
2. 把密度改成 1350（顶部），观察位移变化；
3. 解释 `ufl.as_vector([0.0, 0.0, -rho*g])` 的负号。

---

## 第 7 章 分层密度与体积力：更接近万神殿

### 7.1 本章目标

1. 理解万神殿密度分层（1350/1500/1600）；
2. 学会用「空间变化函数」定义非均匀密度；
3. 理解 UFL 里函数与常量的区别。

### 7.2 万神殿的密度不是常数

文档3 第 9.3 表：穹顶上/中/下密度分别是 1350 / 1500 / 1600 kg/m³。

直接写 `rho = fem.Constant(domain, 1600.0)` 只能模拟均匀密度——C1 可以先这样，但 C2+ 要用分层。

### 7.3 用函数定义空间变化的密度

```python
# 1. 在标量空间上定义一个函数
W = fem.functionspace(domain, ("Lagrange", 1))
rho = fem.Function(W)

# 2. 按 z 坐标填充：顶部轻（1350）、底部重（1600）
#    ⚠️ dolfinx 0.8 推荐 Python callable 插值：
#    - 旧写法 ufl.ge(domain.geometry.x[:,2], 0.0) 只吃 UFL 表达式，吃 numpy 数组会报错（P-04）；
#    - 且旧版条件方向写反（P-02）：z>=0 数学上是「上半部」，应给轻密度 1350。
def rho_fill(x):                            # x: (3, N) 坐标数组
    return np.where(x[2] >= 0.0, 1350.0, 1600.0)   # 上半部(z>=0)→1350 轻
rho.interpolate(rho_fill)
```

**关键概念**：

- `fem.Constant`：全局一个值；
- `fem.Function`：每个节点一个值（可以空间变化）；
- `interpolate`：把表达式写进函数。

### 7.4 Constant vs Function：什么时候用哪个

| | Constant | Function |
| --- | --- | --- |
| 值 | 全场一个 | 每节点一个 |
| 适合 | E、ν、g | 密度分层、温度场 |
| 代码 | `fem.Constant(domain, 值)` | `fem.Function(V)` + `interpolate` |

### 7.5 本章小结

1. 密度分层 = 空间变化函数，用 `fem.Function` + `interpolate`；
2. `Constant` 全场一个值，`Function` 每节点一个值；
3. 分层密度用 `Function.interpolate(callable)`（0.8 下最稳；`ufl.conditional` 老写法见 7.3 注记）。

### 7.6 小练习

1. 用三层密度（1350/1500/1600）重写 7.3 的例子（提示：`ufl.And` 组合条件）；
2. 解释为什么要分层而不是取平均值；
3. 预测：顶部密度小，最大位移会出现在哪？

---

## 第 8 章 应力后处理：从位移到应力

### 8.1 本章目标

1. 理解为什么应力要「后处理」而不是直接解出来；
2. 学会从位移场计算应力张量（6 个分量）；
3. 学会用 `ufl` 表达式投影到函数空间并导出。

### 8.2 为什么应力是后处理

文档3 第 4.5 节讲过：FEM 的主未知量是**位移**，应力 = 位移的导数 × 材料参数。

```text
解出 uh（位移）→ ε(uh) = sym(grad(uh)) → σ = λ tr(ε) I + 2μ ε
```

所以应力不是在 `solve()` 里出来的，而是**算完位移后再算一遍**。

### 8.3 三步算应力

```python
# 第 1 步：定义应变/应力表达式（和弱形式里一样）
def epsilon(w):
    return ufl.sym(ufl.grad(w))

def sigma(w):
    return lam * ufl.tr(epsilon(w)) * ufl.Identity(3) + 2 * mu * epsilon(w)

# 第 2 步：把符号表达式「代入」已解出的位移 uh
sigma_expr = sigma(uh)

# 第 3 步：投影到函数空间（每个单元积分求值）
#    ⚠️ dolfinx 0.8 API（P-05）：
#    - Expression 第二个参数是「求值点坐标 (N,3)」而非元素；
#    - interpolate 不接受裸 UFL 表达式，必须先包成 Expression。
S = fem.functionspace(domain, ("Lagrange", 1, (3, 3)))
sigma_h = fem.Function(S)
X = S.element.interpolation_points()          # 元素插值点 (N,3)
sigma_h.interpolate(fem.Expression(sigma_expr, X))
```

**为什么不能直接用 `sigma_expr`？** 因为位移是**节点值**，应力涉及导数，需要投影到新的函数空间才能得到「可输出的函数」。

### 8.4 提取六个分量

```python
# 分量下标：0,1,2 = xx,yy,zz；3,4,5 = xy,yz,zx（按对称张量展开）
# ⚠️ 0.8 下同样要经 Expression（绑定子空间插值点）再 interpolate
Wxx = S.sub(0).collapse()[0]
sigma_xx = fem.Function(Wxx)
X_xx = Wxx.element.interpolation_points()
sigma_xx.interpolate(fem.Expression(sigma_expr[0, 0], X_xx))

# 或者直接保存整个张量场，后处理时再取分量
```

**万神殿 V2.0 的要求**：输出完整六个分量
$\{\sigma_{xx}, \sigma_{yy}, \sigma_{zz}, \tau_{xy}, \tau_{yz}, \tau_{zx}\}$——正好对应应力张量的对称展开。

### 8.5 主应力（后处理最常看）

万神殿最关心**开裂**：最大主应力 $\sigma_1$ 是否超过抗拉强度 0.08 MPa。

```python
# 用 numpy 在节点上算特征值（简化版，先取节点处的张量）
import numpy as np

sigma_nodes = sigma_h.x.array.reshape(-1, 3, 3)
principal = np.linalg.eigvalsh(sigma_nodes)   # 升序：σ1 是最后一列
s1 = principal[:, -1]
print("最大主应力范围:", s1.min() / 1e6, "~", s1.max() / 1e6, "MPa")
```

### 8.6 导出结果（.vtu 给 PyVista）

```python
from dolfinx.io import VTXWriter

# ⚠️ dolfinx 0.8（P-06）：VTXWriter 要求同元素类型——
# 位移(P2) 与应力(P1) 不能混装一个 writer，必须分开导出。
with VTXWriter(domain.comm, "output/results/c1_displacement.bp", [uh]) as w:
    w.write(0)
with VTXWriter(domain.comm, "output/results/c1_stress.bp", [sigma_h]) as w:
    w.write(0)
```

文档6 会教怎么把这个文件画成云图。

### 8.7 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 应力全为 0 | 忘了 interpolate，直接用了符号表达式 | 用 `fem.Expression(expr, X)` 包一层再 `interpolate`（X=插值点，见 8.3） |
| 应力跳变严重 | 一阶投影在单元间不连续 | 用投影 + 后处理平滑 |
| 单位吓人 | 应力单位是 Pa | 除以 1e6 转 MPa |
| 特征值报错 | 形状不对 | `reshape(-1, 3, 3)` |

### 8.8 本章小结

1. 应力 = 位移的导数，必须后处理；
2. 三步：定义 σ 表达式 → 代入 uh → 投影到函数空间；
3. 六个分量 = 张量对称展开；
4. 最大主应力 σ1 是开裂判据（对照 0.08 MPa）。

### 8.9 小练习

1. 在 6.2 的立方体例子上加应力后处理，打印 σ1 范围；
2. 解释为什么 σ1 比 σxx 更有工程意义；
3. 把应力转成 MPa 显示（除以 1e6）。

---

## 第 9 章 C1 实战：球壳自重线弹性

### 9.1 本章目标

把前 8 章全部串起来：**读入 C0 球壳网格 → 施加拱脚固支 → 自重 → 求解 → 输出应力**。

### 9.2 前置条件

- [ ] 文档4 第 14 章已生成 `output/meshes/c0_shell_groups.msh`（截断半球壳 + 物理组 200/300/400/1000/100）；
  > ⚠️ C0 的 `c0_shell.msh` 没有物理组，C1 的 `find(400)` 需要标签——必须用带组的 `c0_shell_groups.msh`（偏差 7）；
- [ ] 网格文件能用 meshio 读取；
- [ ] 拱脚面物理组 tag = 400，穹顶体 tag = 1000。

### 9.3 完整代码

保存为 `fem_solver/c1_dome_selfweight.py`：

```python
"""
C1：球壳自重线弹性
流程：读 C0 网格 → 拱脚固支 → 自重 → 求解 → 输出位移/应力
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dolfinx import mesh, fem
from dolfinx.fem import petsc
from dolfinx.io import gmshio, VTXWriter
import ufl
import numpy as np
from mpi4py import MPI
from config.params import (
    E_CONCRETE, NU_CONCRETE, DENSITY_STEPS, G,
)

# ============ 1. 读入网格（带物理组的 c0_shell_groups.msh） ============
domain, cell_tags, facet_tags = gmshio.read_from_msh(
    "output/meshes/c0_shell_groups.msh",
    MPI.COMM_WORLD,
    gdim=3,
)

# ============ 2. 函数空间：二阶三维矢量 ============
V = fem.functionspace(domain, ("Lagrange", 2, (3,)))

# ============ 3. 边界条件：拱脚面(400)固支 ============
base_facets = facet_tags.find(400)
dofs = fem.locate_dofs_topological(V, 2, base_facets)
bc = fem.dirichletbc(fem.Constant(domain, (0.0, 0.0, 0.0)), dofs, V)

# ============ 4. 材料参数 ============
E = fem.Constant(domain, E_CONCRETE)
nu = fem.Constant(domain, NU_CONCRETE)
lam = E * nu / ((1 + nu) * (1 - 2 * nu))
mu = E / (2 * (1 + nu))

# ============ 5. 自重（先用下区密度 1600，后续升级分层） ============
rho = fem.Constant(domain, DENSITY_STEPS[-1][1])
g = fem.Constant(domain, G)
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
problem = petsc.LinearProblem(
    a, L, bcs=[bc],
    petsc_options={"ksp_type": "preonly", "pc_type": "lu"},
)
uh = problem.solve()

# ============ 8. 位移统计 ============
u_mag = np.sqrt(np.sum(uh.x.array.reshape(-1, 3) ** 2, axis=1))
print(f"最大位移: {u_mag.max() * 1000:.3f} mm")

# ============ 9. 应力后处理（0.8 新 API，见 8.3 注记） ============
S = fem.functionspace(domain, ("Lagrange", 1, (3, 3)))
sigma_h = fem.Function(S)
X = S.element.interpolation_points()
sigma_h.interpolate(fem.Expression(sigma(uh), X))

sigma_nodes = sigma_h.x.array.reshape(-1, 3, 3)
principal = np.linalg.eigvalsh(sigma_nodes)
s1 = principal[:, -1]
print(f"最大主应力: {s1.max() / 1e6:.2f} MPa")
print(f"最小主应力: {principal[:, 0].min() / 1e6:.2f} MPa")

# ============ 10. 导出（位移/应力分开，见 8.6 注记） ============
from pathlib import Path as P
P("output/results").mkdir(parents=True, exist_ok=True)
with VTXWriter(domain.comm, "output/results/c1_displacement.bp", [uh]) as w:
    w.write(0)
with VTXWriter(domain.comm, "output/results/c1_stress.bp", [sigma_h]) as w:
    w.write(0)

print("✅ C1 完成，结果在 output/results/c1_*.bp")
```

> **本教材代码 vs 仓库实际代码的差异**（2026-08-15 落地时做的工程化增强，概念与本节一致）：
> 1. **E 参数化三档扫描**：仓库版把 E 做成 `solve_case(E_value)` + `--e` 命令行参数，一次跑 1.0/7.0/14.8 GPa 三档（方案 A 敏感性扫描），末尾自动做「σ 不随 E 变 + u×E 守恒」的静定校验；
> 2. **密度单层简化**：C1 用 `DENSITY_STEPS[-1][1]` 单层下区密度，分层留给 C2 升级；
> 3. 边界条件用 `facet_tags.find(400)` 前先判空并给出可读报错。

### 9.4 逐段验收点

**读网格段**：`facet_tags.find(400)` 必须返回非空数组——否则说明文档4 的物理组没贴好。

**BC 段**：固支 = 全部位移分量为 0，一个 `Constant(0.0)` 自动覆盖三个分量。

**弱形式段**：与第 6 章完全一致——C1 只是把「立方体」换成「球壳」，代码零改动。

**应力段**：主应力以 Pa 输出，转 MPa 显示；万神殿混凝土抗拉 0.08 MPa——**如果 σ1 远超 0.08 MPa，说明线弹性下受拉区已经「名义上开裂」，这是 C2+ 非线性模型要处理的信号**。

### 9.5 预期输出（量级参考）

```text
最大位移: X.XXX mm
最大主应力: X.XX MPa
最小主应力: -X.XX MPa
✅ C1 完成，结果在 output/results/c1_*.bp
```

具体数值取决于网格粗细和参数版本——**不要背数字，要会判断量级是否合理**（位移毫米级、应力 MPa 级）。

### 9.6 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `find(400)` 为空 | 物理组没贴或 tag 不对 | 打印 `np.unique(facet_tags.values)` |
| 最大位移 0 | 自重没加或 b=0 | 检查 L |
| 位移方向反了 | 重力符号错 | 确认 `-rho*g` |
| 应力超大 | 单位混用或参数错 | 检查 E 是否 14.8e9 Pa |
| 内存不足 | 网格太细 | 先粗网格（2.0m）跑通 |

### 9.7 本章小结

1. C1 = C0 网格 + 固支 + 自重 + 线弹性，代码和立方体例子同构；
2. 验收看量级：位移 mm、应力 MPa；
3. σ1 超过抗拉强度 0.08 MPa = 非线性模型的入口信号；
4. 结果导出 `.bp` 给文档6 可视化。

### 9.8 小练习

1. 跑通 C1，记录最大位移和最大主应力；
2. 把网格换粗（文档4 第 14 章 3.0m）和换细（1.0m），对比结果——这就是网格无关性验证（文档3 第 8 章）；
3. 思考：为什么固支在拱脚面而不是整个底面？

---

## 第 10 章 进阶：干缩、非线性、求解器调优

### 10.1 本章目标

1. 理解干缩荷载怎么施加（热应变类比）；
2. 理解「无拉伸本构」为什么是非线性的；
3. 掌握非线性求解的基本套路。

> 本章是 C4（全模型 + 干缩）的前置知识，C1/C2 用不到。先通读，用到再精读。

### 10.2 干缩荷载：混凝土「变干变短」

混凝土养护会失水收缩（干缩），像湿布晾干后变小。干缩应变 $\varepsilon_{sh}$ 相当于「初始应变」。

**热应变类比法**：把干缩看成「负温度变化」——两者都是自由应变，不影响应力，但被约束时会产生应力。

```python
# 干缩应变（等效），单位：无量纲
eps_sh = fem.Constant(domain, 1.23e-5)

# 应力中扣除自由应变：
def sigma_with_shrinkage(w):
    eps_total = epsilon(w)                    # 总应变（几何）
    eps_mech = eps_total - eps_sh * ufl.Identity(3)   # 力学应变 = 总 - 自由
    return lam * ufl.tr(eps_mech) * ufl.Identity(3) + 2 * mu * eps_mech
```

**物理**：如果结构能自由收缩，应变为零；被固定/约束住，收缩被阻止 → 产生拉应力 → 可能开裂。

### 10.3 无拉伸本构：混凝土「怕拉」

线弹性假设「拉压对称」，但混凝土受拉极弱（0.08 MPa），一拉就裂。

**无拉伸本构（no-tension）**：受拉时刚度退化/应力截断。

```python
# 简化版：主应力为拉时，把该方向应力清零
# 完整实现需要每步迭代 + 主应力旋转，属于研究级代码
def sigma_no_tension(w):
    s = sigma(w)
    # 伪代码：s = project(s); 若主应力>0 则截断
    return s
```

**为什么必须非线性**：因为「哪里受拉」事先不知道，要迭代求解——每一步检查应力、修正材料、再求解，直到收敛。

**迭代骨架**：

```python
from dolfinx.fem.petsc import NonlinearProblem
from dolfinx.nls.petsc import NewtonSolver

problem = NonlinearProblem(F_form, uh, bcs=[bc])
solver = NewtonSolver(domain.comm, problem)
iters, converged = solver.solve(uh)
print(f"Newton 迭代 {iters} 次, 收敛={converged}")
```

### 10.4 求解器调优速查

| 场景 | 推荐配置 |
| --- | --- |
| 小模型（<10 万自由度） | `preonly + lu` |
| 大模型 | `cg + amg`（`pc_type: hypre` 或 `gamg`） |
| 非线性 | Newton + 线搜索，必要时加阻尼 |
| 不收敛 | 先查 BC/单位，再减小步长 |

### 10.5 本章小结

1. 干缩 = 热应变类比（自由应变），被约束才产生应力；
2. 无拉伸本构 = 受拉截断 → 非线性 → Newton 迭代；
3. 非线性问题用 `NonlinearProblem` + `NewtonSolver`；
4. 求解器：小模型 LU，大模型 AMG。

### 10.6 小练习

1. 解释：为什么干缩在「自由」结构里不产生应力？
2. 说出线弹性与无拉伸本构的关键区别；
3. 思考：C1 的 σ1 若超过 0.08 MPa，下一步该做什么？

---

## 附录 A：术语表

### 核心框架

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| FEniCSx / dolfinx | 有限元求解框架 | 自动组装求解 |
| UFL | 统一形式语言 | 用 Python 写弱形式 |
| mesh | 网格 | 读入的单元集合 |
| function space | 函数空间 | 解允许「长什么样」 |
| Lagrange | 拉格朗日插值 | 最常用形函数族 |
| degree of freedom | 自由度 | 未知量 |
| trial function | 试函数 | 未知解 u |
| test function | 测试函数 | 检验 v |

### 代码元素

| 英文 | 中文 | 说明 |
| --- | --- | --- |
| `fem.functionspace` | 定义函数空间 | `("Lagrange", 2, (3,))` |
| `fem.dirichletbc` | 狄利克雷边界 | 固定位移 |
| `fem.Constant` | 常量 | 全场一个值 |
| `fem.Function` | 函数 | 每节点一个值 |
| `ufl.dx` | 体积分 | 域积分 |
| `ufl.ds` | 面积分 | 边界积分 |
| `ufl.inner` | 张量收缩 | σ:ε |
| `ufl.sym` | 对称化 | (A+Aᵀ)/2 |
| `ufl.tr` | 迹 | 对角线和 |
| `ufl.Identity(n)` | 单位矩阵 | I |
| `gmshio.read_from_msh` | 读 Gmsh 网格 | 返回网格+标签 |
| `facet_tags.find(tag)` | 按标签找面 | 边界条件用 |
| `locate_dofs_topological` | 面→自由度 | BC 第二步 |
| `VTXWriter` | 导出结果 | .bp 给 PyVista |

### 力学量

| 英文 | 中文 | 单位 |
| --- | --- | --- |
| displacement | 位移 | m |
| strain | 应变 | 无量纲 |
| stress | 应力 | Pa |
| principal stress | 主应力 | Pa |
| body force | 体积力 | N/m³ |
| Lamé constants | 拉梅常数 | Pa |
| shrinkage | 干缩 | 无量纲 |

---

## 附录 B：审核清单（交付前逐条打勾）

### 网格与空间

- [ ] `.msh` 能读入，`facet_tags` 有预期标签（200/300/400/1000）
- [ ] 位移空间为二阶三维矢量 `("Lagrange", 2, (3,))`

### 边界条件

- [ ] 拱脚面（400）固支
- [ ] 无多余约束（不超定）
- [ ] 反力可查（可用 `assemble` 检验力平衡）

### 弱形式

- [ ] 应变用 `sym(grad(u))`
- [ ] 应力公式与文档3 第 7.6 节一致
- [ ] 自重方向向下（-z）
- [ ] 所有积分项带 `dx`/`ds`

### 结果

- [ ] 位移量级合理（mm）
- [ ] 应力量级合理（MPa）
- [ ] σ1 与抗拉强度 0.08 MPa 对比有结论
- [ ] 做了网格无关性验证（至少三套网格）
- [ ] 结果导出 `.bp` 且 PyVista 可读

---

## 结课寄语

走到这里，你已经具备：

1. 读 Gmsh 网格 + 物理组；
2. 写矢量函数空间；
3. 施加 Dirichlet BC；
4. 写线弹性弱形式；
5. 求解 + 应力后处理 + 导出。

**下一步**：拿着 `output/results/c1_displacement.bp` 和 `c1_stress.bp`（位移/应力分开导出的两个文件）进入文档6——PyVista 可视化，把数字变成云图。

---

> 全书完（v2.0，2026-08-13 重写）。旧版存档于 `docs/tutorials/_legacy/`。

---

## 实战增补 · 六个求解器的完整战役（2026-08-15~17）

> 本章基于《万神殿全解》成书卷六：六求解器的架构谱系、四个 dolfinx 0.8 迁移坑（P-04~P-07）、求解器升级战、以及 57° 口径三件套。与正文互补：正文教七步骨架，本章教「骨架之上怎么打仗」。

### 增补 1：六个求解器的谱系图（架构复用）

```
c1（自重线弹性，E 常数）          → C1 三档收敛 + E 敏感性
  └→ c3（+Rankine 损伤场）        → C2+ 三档
       └→ c4（+干缩热类比）       → C4 五档扫描 + 57° 口径三件套
            └→ c4plus（+损伤×干缩）→ C4+ 三档
c5（切片对称 BC）                 → 草稿（子空间 BC + 罚函数）
c6（分区材料 + 区域干缩）         → C6/C7 全结构
```

**每个新物理只改动 30-80 行**——六脚本共享同一骨架（读网格→空间→BC→弱形式→cg+amg→应力投影→口径统计）。**如果一开始写万能求解器，8 天的战役打不完。**

### 增补 2：四个 dolfinx 0.8 迁移坑（P-04~P-07 全解）

| 坑 | 症状 | 正确写法 |
| --- | --- | --- |
| P-04 ufl 条件表达式 | `ufl.ge(x[2],0)` 吃 numpy 报错 | Python callable + `np.where` + `interpolate` |
| P-05 Expression 新 API | `(expr, W.element)` 报错 | `(expr, X)`，X=`S.element.interpolation_points()` |
| P-06 VTXWriter 混写 | 位移（P2 矢量）与应力（P1 张量）同写报错 | **分导两个 .bp** |
| P-07b 坐标布局 | `tabulate_dof_coordinates` 返回 (N,3) 按点去重，不是 9N | 运行时自适应两种布局 + 失败报清晰错 |

**生存法则**：**不信任 API 文档，运行时自适应。** dolfinx 0.8 是快速演进的框架，教材与文档都可能过时——本项目 12 个坑里 4 个是版本迁移坑。

### 增补 3：求解器升级战——LU 直接法 → cg+BoomerAMG

97 万 DOF 时 LU 直接法内存爆。升级配置（全部求解器统一）：

```python
problem = petsc.LinearProblem(a, L, bcs=[bc],
    petsc_options={"ksp_type": "cg", "pc_type": "hypre",
                   "pc_hypre_type": "boomeramg", "ksp_rtol": 1e-8})
```

实测：22 次迭代、残差 6e-2→4e-10；212 万 DOF 本机跑通。**白话**：cg=共轭梯度（不走回头路的爬山）；BoomerAMG=代数多重网格（先在粗化版本大致解一遍再细修——先看地图再走小路）。选型前的调研谱系：matrix-free / out-of-core / 低秩 / ROM / FETI-DP+ROM——**「先摸清武器库再选武器」。**

### 增补 4：fixed-point 非线性——最温柔的非线性入口

```python
for it in range(max_iter):
    uh = problem.solve()                        # 每步线弹性（cg+amg）
    s1 = eigvalsh(sigma_nodes)[:,-1]            # 算主应力
    D_new = np.maximum(1.0-(FT/s1_pos)**2, 0.0) # Rankine 更新
    D_new = np.minimum(D_new, 0.9)              # 封顶防奇异
    D_new = np.maximum(D_new, D_old)            # 不可逆
    E_field.x.array[:] = E0*(1.0-D_new)         # 退化模量场
    if max|ΔD| < 1e-3: break                    # 收敛判据
```

**白话**：猜 D=0 → 解 → 更新 D → 再解 → 直到 D 不再变。**把非线性问题拆成线性问题的序列**，不需要牛顿法切线刚度。实测 3 次迭代收敛，σ1 被「限压阀」截回 f_t 附近（0.1326→0.0799）。

### 增补 5：57° 口径三件套（c4 求解器最值钱的后处理）

**① 名义开裂区**：σ1>f_t 的点集；角度映射 angle_from_spring = 90° − arccos(z/r)（与 Masi Table 2 的 θ 口径对齐——拱脚 0° 起算）。

**② 最大连通裂缝簇（BFS 图论，8/17 关键创新）**：

```python
c2v = domain.topology.connectivity(3, 0)   # 单元→顶点表
# 每四面体 4 顶点两两连边建邻接表 → BFS 洪泛标记连通簇
# 取最大簇顶端角 = 真实裂缝带口径（剔除孤立尖角散点）
```

**为什么需要**：藻井模型的 max 单点 74.2° 是孤立奇异散点（互不相连），不是裂缝。**「单点极值 vs 连通域」的口径区分，是识破假突破的关键武器。**

**③ 环向转压带（57° 假说核心量）**：

```python
s_theta = np.einsum("ni,nij,nj->n", e_th, sigma_nodes, e_th)  # σ_θθ = e_θ·σ·e_θ
# 按 1° 纬度带取 σ_θθ 均值，最高「均值受拉」带 = 环向转压纬度 = 理论裂缝屏障
```

**铁律（8/17 八组算例）**：连通裂缝顶端 < 环向转压带，且随 ε_sh 增大同步爬升——**裂缝止于环向转压线是普适屏障**。

### 增补小练习

1. 七步骨架的哪几步在 c1 与 c4 之间完全一致？哪几步变了？
2. 复述 fixed-point 的收敛判据与「限压阀」物理。
3. 为什么 max 单点口径会虚高（74.2°）？BFS 连通簇怎么把它剔除？
4. einsum 的 "ni,nij,nj->n" 在算什么？展开成双重求和写一遍。

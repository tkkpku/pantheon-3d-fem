# 文档5 配套速查 · FEniCSx 函数与英文术语（2026-08-15）

> 用途：读文档5 时卡住就查这里。分六块：① 七步总流程；② 函数速查表；③ 核心函数详解；④ 英文术语表；⑤ 记忆口诀；⑥ 阅读路线。
>
> 一句话记忆：**FEniCSx = 读网格（gmshio）→ 搭舞台（functionspace）→ 上规矩（dirichletbc）→ 请演员（Trial/Test）→ 写方程（UFL）→ 交卷（solve）→ 出报告（interpolate/VTXWriter）**。

---

## 0. 整个文档5 其实只讲了七件事

| 步骤 | 干什么 | 通俗比喻 | 关键函数 |
| --- | --- | --- | --- |
| 1 读网格 | 把 Gmsh 的 .msh 读进来，连带物理组标签 | 收货验货：打开快递，核对货单（标签） | `gmshio.read_from_msh` |
| 2 搭舞台 | 定义函数空间 V（解长什么样） | 搭舞台：定好演员只能在台上活动 | `fem.functionspace` |
| 3 上规矩 | 施加边界条件（哪里固定） | 划红线：某些位置不许动 | `facet_tags.find`、`locate_dofs_topological`、`fem.dirichletbc` |
| 4 请演员 | 定义试函数 u 和测试函数 v | 请主角 + 拿一把检验尺子 | `ufl.TrialFunction`、`ufl.TestFunction` |
| 5 写方程 | 用 UFL 写弱形式 a(u,v)=L(v) | 把数学公式翻译成代码 | `ufl.inner`、`ufl.grad`、`ufl.dx/ds` |
| 6 交卷 | 组装 + 求解 | 自动算完交答案 | `petsc.LinearProblem`、`problem.solve()` |
| 7 出报告 | 应力后处理 + 导出 | 把位移换算成应力，打包发货 | `interpolate`、`VTXWriter` |

> 注意：第 3 步（BC）**必须有**——文档5 §2.6 实验 C：去掉 BC 会报「奇异矩阵」，因为 K 不可逆（文档3 的结论）。
> 第 7 步（应力）**不能省**：FEM 主未知量是位移，应力 = 位移的导数 × 材料参数，是算完位移后再算一遍（§8.2）。

---

## 1. 函数速查表

### 1.1 网格读入（每次必有，1 个）+ 测试网格（2 个）

| 函数 | 作用 | 参数（按顺序） | 返回值 | 出现章节 |
| --- | --- | --- | --- | --- |
| `gmshio.read_from_msh("路径.msh", MPI.COMM_WORLD, gdim=3)` | 读 Gmsh 网格 | 文件路径；MPI 通信子；几何维度 | **(网格, 体标签, 面标签)** | §4.3、§9.3 |
| `mesh.create_unit_square(MPI.COMM_WORLD, 10, 10)` | 造单位正方形网格（练习用） | 通信子；x/y 方向分段数 | 网格 | §2.3 |
| `mesh.create_unit_cube(MPI.COMM_WORLD, 2, 2, 2)` | 造单位立方体网格（练习用） | 通信子；三方向分段数 | 网格 | §6.2 |

**白话**：`read_from_msh` 是 C1 的「收货」动作——它一次吐回三样东西：网格本体、体上的物理组标签（1000=穹顶体）、面上的物理组标签（400=拱脚面）。**文档4 贴的每个标签在这里全部派上用场**（§4.2）。

### 1.2 函数空间（搭舞台，2 个）

| 函数 | 作用 | 白话 | 出现章节 |
| --- | --- | --- | --- |
| `fem.functionspace(domain, ("Lagrange", 2, (3,)))` | 定义函数空间 | 定「解长什么样」：二阶 × 3 分量 | §3.2、§3.4 |
| `V.dofmap.index_map.size_global` | 查自由度总数 | 数一数这个舞台能站多少个「演员位」 | §3.5 |

**四种空间写法对比**（§3.4 表）：

| 空间 | 代码 | 每节点自由度 |
| --- | --- | --- |
| 一阶标量 | `("Lagrange", 1)` | 1 |
| 二阶标量 | `("Lagrange", 2)` | 1 |
| **二阶三维矢量（万神殿位移）** | `("Lagrange", 2, (3,))` | 3 |
| 二阶对称张量（后处理用） | `("Lagrange", 1, (3,3))` | 6（对称） |

### 1.3 边界条件（上规矩，4 个）

| 函数 | 作用 | 白话 | 出现章节 |
| --- | --- | --- | --- |
| `facet_tags.find(400)` | 按物理组编号找面单元 | 在点名册里查「400 号」有哪些面 | §4.5 |
| `fem.locate_dofs_topological(V, 2, facets)` | 由面单元找面上的自由度 | 从「哪些面」推到「哪些演员位」 | §4.5 |
| `fem.locate_dofs_geometrical(V, boundary)` | 按坐标位置找自由度（练习用） | 按位置圈人：z<1e-8 的都算边界 | §2.3 |
| `fem.dirichletbc(fem.Constant(domain, (0,0,0)), dofs, V)` | 令这些自由度 = 定值 | 给指定演员位下「不许动」命令 | §4.5 |

**标准三步 BC**（§4.5，C1 直接用）：

```python
facets = facet_tags.find(400)                        # 第 1 步：找面
dofs = fem.locate_dofs_topological(V, 2, facets)     # 第 2 步：面 → 自由度
bc = fem.dirichletbc(fem.Constant(domain, (0.0, 0.0, 0.0)), dofs, V)  # 第 3 步：赋值
```

### 1.4 试/测试函数与 UFL 弱形式（核心词汇，先背这 8 个）

| UFL 代码 | 数学含义 | 白话 |
| --- | --- | --- |
| `ufl.TrialFunction(V)` | 试函数 $u$ | 未知解（主角） |
| `ufl.TestFunction(V)` | 测试函数 $v$ | 检验尺子 |
| `ufl.grad(u)` | $\nabla u$ | 梯度（位移→应变） |
| `ufl.inner(a, b)` | $a : b$ | 张量全收缩（对应相乘相加） |
| `ufl.dot(a, b)` | $a \cdot b$ | 向量点积（体积力×位移） |
| `ufl.sym(A)` | $\frac{1}{2}(A+A^T)$ | 对称部分（小变形应变） |
| `ufl.tr(A)` | $\mathrm{tr}(A)$ | 迹（对角线和） |
| `ufl.Identity(n)` | $n\times n$ 单位矩阵 | 常数张量（本构里用） |
| `ufl.dx` / `ufl.ds` | 体积分 / 面积分 | 在整个域 / 边界上积分 |
| `ufl.as_vector([...])` | 构造向量 | 如 `[0, 0, -rho*g]`（自重） |
| `ufl.conditional(cond, a, b)` | 条件表达式 | 按坐标切区域（密度分层） |

> **每个积分项必须带 `dx`/`ds`**（§5.7 常见错误 4）——表达式后忘了写 `* ufl.dx` 是新手第一坑。

> 📐 数学逐步说明：∇u 的 9 个数是什么 → 附录 A.1；泊松弱形式完整推导 → 附录 A.6；dx(标签)/ds(标签) 的数学意义 → 附录 A.10

### 1.5 常量 vs 函数（2 个 + 2 个配套）

| 函数 | 作用 | 白话 | 出现章节 |
| --- | --- | --- | --- |
| `fem.Constant(domain, 值)` | 全场一个值 | 全局统一价签（E、ν、g 用它） | §6.2、§7.4 |
| `fem.Function(V)` | 每节点一个值 | 每个演员位单独标价（密度分层用它） | §7.3 |
| `fem.Expression(表达式, W.element)` | 把表达式变成可插值对象 | 把公式转成「填表模板」 | §7.3 |
| `func.interpolate(expr)` | 把表达式写进函数 | 按模板填表 | §7.3 |

### 1.6 求解（2 个）+ 求解器选项

| 函数 | 作用 | 白话 | 出现章节 |
| --- | --- | --- | --- |
| `petsc.LinearProblem(a, L, bcs=[bc])` | 组装 + 求解线性问题 | 自动拼 K、f，解 Ku=f | §2.3、§6.2 |
| `problem.solve()` | 执行求解 | 得到位移 uh | §2.3 |

**求解器选项**（§6.4、§10.4）：

| 场景 | 推荐配置 |
| --- | --- |
| 小模型（<10 万自由度，C0/C1 粗网格） | `{"ksp_type": "preonly", "pc_type": "lu"}`（最稳） |
| 大模型 | `cg + amg`（`pc_type: hypre` 或 `gamg`） |
| 非线性（C4 干缩/无拉伸） | `NonlinearProblem` + `NewtonSolver`（§10.3） |

### 1.7 后处理与导出（3 个）

| 函数                                                       | 作用        | 白话                  | 出现章节      |
| -------------------------------------------------------- | --------- | ------------------- | --------- |
| `fem.Function(S)` + `interpolate(sigma_expr)`            | 投影应力到函数空间 | 把符号表达式「落地」成可输出的函数   | §8.3      |
| `np.linalg.eigvalsh(张量)`                                 | 节点上算主应力   | 求应力张量的特征值（σ1 是最后一列） | §8.5      |
| `VTXWriter(comm, "路径.bp", [uh, sigma_h])` + `w.write(0)` | 导出结果      | 打包发货给 PyVista       | §8.6、§9.3 |

---

## 2. 核心函数详解（C1 之前必须吃透的 7 个）

### 2.1 `gmshio.read_from_msh` —— 收货验货

**语法**：

```python
domain, cell_tags, facet_tags = gmshio.read_from_msh(
    "output/meshes/c0_shell.msh",
    MPI.COMM_WORLD,
    gdim=3,          # 几何维度：三维
)
```

**返回值的坑**：一次返回**三个**东西，顺序不能错：

| 返回值 | 含义 | 对应 Gmsh |
| --- | --- | --- |
| `domain` | 网格对象（节点+单元） | 网格文件本体 |
| `cell_tags` | 体上的物理组标签（1000=穹顶体） | 3D 物理组 |
| `facet_tags` | 面上的物理组标签（200/300/400） | 2D 物理组 |

**验货动作**（§4.4）：读进来先打印确认标签没丢：

```python
import numpy as np
print("体物理组:", np.unique(cell_tags.values))   # 预期 [1000]
print("面物理组:", np.unique(facet_tags.values))  # 预期 [200 300 400]
```

> **gdim 写错 = 维度不对**（§4.7）。三维模型必须 `gdim=3`。

### 2.2 `fem.functionspace` —— 搭舞台

```python
V = fem.functionspace(domain, ("Lagrange", 2, (3,)))
#                                ↑          ↑   ↑
#                           形函数族   阶次  分量数
```

三要素拆解（§3.2–3.4）：

- `Lagrange`：拉格朗日插值（文档3 第 6 章的形函数家族）；
- `2`：二阶——单元内部位移按**二次**变化，四面体 10 节点，曲线/曲面贴合更好；
- `(3,)`：矢量空间——每节点 3 个分量（$u_x, u_y, u_z$）。

**一阶 vs 二阶**（§3.3）：

| 阶次 | 单元内部变化 | 每单元节点数（四面体） | 精度 |
| --- | --- | --- | --- |
| 1（线性） | 直线/平面 | 4 | 较低 |
| 2（二次） | 曲线/曲面 | 10 | 高（本项目用） |

**为什么二阶能「用更粗网格达到同样精度」**：形函数阶次更高 → 插值更准 → 网格可以更粗（§3.3）。

> 📐 数学逐步说明：自由度 11×11=121 怎么算 → 附录 A.8

### 2.3 BC 三步 —— 物理组怎么「旅行」

完整链路（§4.2）：

```text
Gmsh: addPhysicalGroup(2, [tag], tag=400, name="dome_base")
              ↓ 写入 .msh 文件
FEniCSx: gmshio 读取 → facet_tags
              ↓
facet_tags.find(400) → 找到拱脚面
              ↓
locate_dofs_topological(V, 2, facets) → 面上的自由度
              ↓
dirichletbc(...) → 令这些自由度 = 0
```

**`locate_dofs_topological` 的三个参数**（§4.5）：`V` 函数空间（矢量空间自动处理 3 个分量）、`2` 维度（1=线，2=面，3=体）、`facets` 目标面编号数组。

> 对矢量空间，BC 值必须是**矢量常量** `(0.0, 0.0, 0.0)`——一个 `Constant` 自动覆盖三个分量（§9.4 验收点）。

### 2.4 `fem.dirichletbc` —— 上规矩的两种姿势

**姿势 A：全部固定**（C1 拱脚固支）：

```python
bc = fem.dirichletbc(fem.Constant(domain, (0.0, 0.0, 0.0)), dofs, V)
```

**姿势 B：只固定某个方向**（§4.6 进阶）：

```python
u_bc = fem.Function(V)
u_bc.sub(2).x.array[:] = 0.0   # z 方向（下标 2）
bc = fem.dirichletbc(u_bc, dofs)
```

`sub(0/1/2)` 分别对应 $u_x, u_y, u_z$——这是 FEniCSx 处理矢量分量的标准方式。

### 2.5 `fem.Constant` vs `fem.Function` —— 统一价签 vs 逐个标价

| | Constant | Function |
| --- | --- | --- |
| 值 | 全场一个 | 每节点一个 |
| 适合 | E、ν、g | 密度分层、温度场 |
| 代码 | `fem.Constant(domain, 值)` | `fem.Function(V)` + `interpolate` |

**密度分层示例**（§7.3，C2+ 用）：

```python
W = fem.functionspace(domain, ("Lagrange", 1))
rho = fem.Function(W)
rho_expr = fem.Expression(
    ufl.conditional(
        ufl.ge(domain.geometry.x[:, 2], 0.0),   # z >= 0
        fem.Constant(domain, 1600.0),           # 下半部 1600
        fem.Constant(domain, 1350.0),           # 上半部 1350
    ),
    W.element,
)
rho.interpolate(rho_expr)
```

### 2.6 UFL 线弹性翻译 —— 数学 → 代码逐项对照

文档3 第 7 章的弱形式（§5.5）：

$$\int_\Omega \sigma(u) : \varepsilon(v)\, dx = \int_\Omega b \cdot v\, dx + \int_\Gamma t \cdot v\, ds$$

> 📐 数学逐步说明：弱形式从平衡方程的完整推导 → 附录 A.7；λ、μ 从 E、ν 的推导 → 附录 A.5

```python
def epsilon(w):                                # 应变：位移 → 应变
    return ufl.sym(ufl.grad(w))

def sigma(w):                                  # 应力：本构（线弹性）
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))   # Lamé 常数（§6.3）
    mu  = E / (2 * (1 + nu))
    return lam * ufl.tr(epsilon(w)) * ufl.Identity(3) + 2 * mu * epsilon(w)

a = ufl.inner(sigma(u), epsilon(v)) * ufl.dx   # 内力虚功（左端）
L = ufl.dot(b, v) * ufl.dx                     # 外力虚功（右端，自重）
```

**对照表**（§5.5）：

| 数学                         | UFL                               |
| -------------------------- | --------------------------------- |
| $\sigma : \varepsilon$     | `ufl.inner(sigma(u), epsilon(v))` |
| $\int_\Omega (\cdot)\,dx$  | `* ufl.dx`                        |
| $\int_\Gamma (\cdot)\,ds$  | `* ufl.ds`                        |
| $\boldsymbol{I}$           | `ufl.Identity(3)`                 |
| $\mathrm{tr}(\varepsilon)$ | `ufl.tr(epsilon(u))`              |
| $b \cdot v$                | `ufl.dot(b, v)`                   |

**自重方向**：重力向下（-z），所以 `b = ufl.as_vector([0.0, 0.0, -rho * g])`——**负号写反 = 位移方向反了**（§9.6）。

**子域积分**（§5.6）：`ufl.dx(1000)` 只在穹顶体积分（不同材料）、`ufl.ds(400)` 只在拱脚面积分（面力）。

### 2.7 应力后处理 —— 为什么不能直接用 `sigma_expr`

三步（§8.3）：

```python
# 第 1 步：定义应变/应力表达式（和弱形式里一样）
def epsilon(w):
    return ufl.sym(ufl.grad(w))
def sigma(w):
    return lam * ufl.tr(epsilon(w)) * ufl.Identity(3) + 2 * mu * epsilon(w)

# 第 2 步：把符号表达式「代入」已解出的位移 uh
sigma_expr = sigma(uh)

# 第 3 步：投影到函数空间（每个单元积分求值）
S = fem.functionspace(domain, ("Lagrange", 1, (3, 3)))
sigma_h = fem.Function(S)
sigma_h.interpolate(sigma_expr)
```

**为什么不能直接用 `sigma_expr`**：位移是**节点值**，应力涉及导数——符号表达式只是「公式」，必须投影（interpolate）到新的函数空间才能得到**可输出的函数**（§8.3）。

> 📐 数学逐步说明：应变为什么是 sym(grad(u))（含 ½ 的来历）→ 附录 A.3；主应力为什么是特征值 → 附录 A.9

**主应力判据**（§8.5，万神殿最关心）：

```python
sigma_nodes = sigma_h.x.array.reshape(-1, 3, 3)
principal = np.linalg.eigvalsh(sigma_nodes)   # 升序：σ1 是最后一列
s1 = principal[:, -1]
print("最大主应力范围:", s1.min() / 1e6, "~", s1.max() / 1e6, "MPa")
```

> **σ1 对照抗拉强度 0.08 MPa**——超了说明线弹性下受拉区已「名义上开裂」，这是 C2+ 非线性模型的入口信号（§9.4）。

---

## 3. 英文术语表

### 3.1 核心框架

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| FEniCSx / dolfinx | 有限元求解框架 | 你给「网格+弱形式+BC」，它自动单元分析、组装、求解 |
| UFL | 统一形式语言 | 用接近数学的写法描述弱形式 |
| function space | 函数空间 | 解允许「长什么样」的舞台 |
| Lagrange | 拉格朗日插值 | 最常用形函数族 |
| degree of freedom (DOF) | 自由度 | 未知量（= 节点数 × 每节点分量数） |
| trial function | 试函数 | 未知解 u |
| test function | 测试函数 | 检验尺子 v |
| weak form | 弱形式 | 乘测试函数再积分得到的方程形态 |
| variational form | 变分形式 | 弱形式的另一个名字 |
| bilinear form | 双线性型 | 弱形式左端 a(u,v) |
| linear form | 线性型 | 弱形式右端 L(v) |
| assembly | 组装 | 拼整体方程 K u = f |
| mesh | 网格 | 读入的单元集合 |

### 3.2 代码元素

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| `gmshio` | Gmsh 网格 IO 模块 | `read_from_msh` 读网格+标签 |
| `read_from_msh` | 读 .msh | 返回 (网格, 体标签, 面标签) |
| `fem.functionspace` | 定义函数空间 | `("Lagrange", 2, (3,))` |
| `fem.dirichletbc` | 狄利克雷边界 | 固定某处位移 |
| `fem.Constant` | 常量 | 全场一个值 |
| `fem.Function` | 函数 | 每节点一个值 |
| `interpolate` | 插值/投影 | 把表达式写进函数 |
| `locate_dofs_topological` | 拓扑定位自由度 | 由面单元找自由度（BC 第二步） |
| `locate_dofs_geometrical` | 几何定位自由度 | 按坐标位置找自由度 |
| `facet_tags.find(tag)` | 按标签找面 | 边界条件第一步 |
| `cell_tags` | 体标签 | 材料分区用（1000=穹顶体） |
| `facet_tags` | 面标签 | 边界条件用（400=拱脚面） |
| `TrialFunction` | 试函数 | 未知解 u |
| `TestFunction` | 测试函数 | 检验 v |
| `LinearProblem` | 线性问题对象 | 组装+求解一体化 |
| `VTXWriter` | 结果导出器 | 写 .bp 给 PyVista |
| `petsc_options` | 求解器选项 | 如 `ksp_type`/`pc_type` |

### 3.3 UFL 语法

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| `ufl.grad` | 梯度 | ∇u，位移→应变 |
| `ufl.inner` | 张量收缩 | σ:ε（对应相乘相加） |
| `ufl.dot` | 点积 | 向量内积 b·v |
| `ufl.sym` | 对称化 | (A+Aᵀ)/2，小变形应变 |
| `ufl.tr` | 迹 | 对角线和 |
| `ufl.Identity(n)` | 单位矩阵 | 本构公式里的 I |
| `ufl.dx` | 体积分 | 域积分（可带标签 dx(1000)） |
| `ufl.ds` | 面积分 | 边界积分（可带标签 ds(400)） |
| `ufl.as_vector` | 构造向量 | 自重 [0,0,-ρg] |
| `ufl.conditional` | 条件表达式 | 按坐标切区域 |
| `ufl.ge` | 大于等于 | 条件判断 z≥0 |

### 3.4 力学量

| 英文 | 中文 | 单位 |
| --- | --- | --- |
| displacement | 位移 | m |
| strain (ε) | 应变 | 无量纲 |
| stress (σ) | 应力 | Pa |
| principal stress | 主应力 | Pa（特征值，σ1 最大） |
| body force | 体积力 | N/m³ |
| Lamé constants (λ, μ) | 拉梅常数 | Pa（由 E、ν 算） |
| Young's modulus (E) | 弹性模量 | Pa（混凝土 14.8e9） |
| Poisson's ratio (ν) | 泊松比 | 无量纲（混凝土 0.2） |
| density (ρ) | 密度 | kg/m³（1350/1500/1600 分层） |
| shrinkage | 干缩 | 无量纲（自由应变） |
| no-tension | 无拉伸本构 | 受拉截断，非线性 |
| Dirichlet BC | 狄利克雷边界条件 | 直接规定某处位移值 |
| boundary condition | 边界条件 | 哪里固定/哪里受力 |
| fixed support | 固支 | 全部位移分量为 0 |

### 3.5 周边库

| 英文                | 中文     | 一句话解释                              |
| ----------------- | ------ | ---------------------------------- |
| mpi4py / MPI      | 并行通信库  | `MPI.COMM_WORLD` 通信子               |
| petsc             | 求解器后端  | 线性代数求解（LU/AMG）                     |
| numpy             | 数值计算库  | `np.unique`、`np.linalg.eigvalsh`   |
| dolfinx.fem.petsc | 求解器接口  | `LinearProblem`、`NonlinearProblem` |
| dolfinx.nls.petsc | 非线性求解器 | `NewtonSolver`（C4 用）               |
| .bp               | 结果文件格式 | dolfinx 0.8 的导出格式，PyVista 可读       |

---

## 4. 记忆口诀

**函数 = 中文动作**：

| 英文函数 | 中文动作 | 联想 |
| --- | --- | --- |
| read_from_msh | 收货 | 开箱验货（网格+标签） |
| functionspace | 搭台 | 定舞台（阶次×分量） |
| find | 点名 | 按标签找人（find(400)=找拱脚面） |
| locate_dofs | 定位 | 面 → 自由度 |
| dirichletbc | 上铐 | 固定不许动 |
| TrialFunction / TestFunction | 请主角 / 拿尺 | u 未知 / v 检验 |
| grad / sym / tr | 求导 / 对称 / 取迹 | 应变三连 |
| inner / dot | 收缩 / 点积 | 张量 / 向量乘法 |
| dx / ds | 体积分 / 面积分 | 域 / 边界积分 |
| Constant / Function | 统一价 / 逐个价 | 全场一个值 / 每节点一个值 |
| solve | 交卷 | 解方程 |
| interpolate | 落地 | 公式 → 可输出函数 |
| VTXWriter | 发货 | 导出 .bp |

**标准流程顺序**（C1 球壳）：

```text
read_from_msh → functionspace(("Lagrange",2,(3,)))
→ find(400) → locate_dofs_topological → dirichletbc
→ TrialFunction/TestFunction → epsilon/sigma 定义 → a/L 弱形式
→ LinearProblem(..., preonly+lu) → solve → 位移统计
→ 投影 sigma_h → eigvalsh 主应力 → VTXWriter 导出
```

**三个高频翻车点**（老板版速读 §使用说明）：

1. **单位必须全 SI**：Pa、kg/m³、m——混用 = 位移巨大/应力量级错（§6.5）；
2. **BC 值类型**：dolfinx 0.8 用 `fem.Constant`，矢量空间必须是 `(0.0, 0.0, 0.0)` 三件套（§4.5 注意）；
3. **物理组标签对得上**：400=拱脚、1000=穹顶体——Gmsh 没贴好，`find(400)` 返回空（§9.6）。

**验收量级**（§9.5 老板速读）：

| 量 | 量级 | 对照 |
| --- | --- | --- |
| 位移 | mm 级 | 最大 \|位移\| × 1000 显示 |
| 应力 | MPa 级 | ÷ 1e6 显示 |
| σ1 | 对照 0.08 MPa | 超 = 非线性模型信号 |

---

## 5. 给你的阅读路线（文档5 第 1–9 章）

1. **§1–§2**：先跑通泊松方程（`demo_poisson.py`），只看七步骨架 + 4 个函数：`functionspace`、`dirichletbc`、`Trial/TestFunction`、`LinearProblem`；
2. **§3**：吃透函数空间——**一阶 vs 二阶**、**标量 vs 矢量**，默写 `("Lagrange", 2, (3,))`；
3. **§4**：吃透 BC 三步 + 物理组旅行链路——这是 C1 与文档4 对接的心脏；
4. **§5–§6**：UFL 八个核心词汇 + 线弹性翻译——最花时间的两章（各 2 个番茄钟）；
5. **§8**：应力后处理三步——C1 验收的最后一环；
6. **§9**：C1 实战代码逐段过——第 6 章立方体代码换成球壳网格，**代码零改动**（§9.4）。

读完标准：不看文档，能默写 C1 主流程（上面「标准流程顺序」），并说清 `read_from_msh` 三个返回值、BC 三步、`sigma_h.interpolate` 为什么必要。

---

## 6. ⚠️ 文档5 原文两处注意

1. **输出格式表述不一致**：§1.2 流程图写「结果（.vtu）」，但 §8.6/§9.3 代码实际导出 `.bp`（dolfinx 0.8 的 VTXWriter 格式）。以 `.bp` 为准，PyVista 可读（文档6 处理）。
2. **§9.3 C1 代码小瑕疵**：文件头已 `from pathlib import Path` 做 `sys.path` 引导，第 10 段又 `from pathlib import Path as P`——重复导入，不影响运行，但合并成一处更干净。

> 另：文档5 依赖 `config/params.py`（E_CONCRETE、NU_CONCRETE、DENSITY_STEPS、G）——C1 跑之前确认该文件存在且单位是 SI（Pa/kg/m³）。

---

## 附录 A：数学教科书逐步说明（2026-08-15 增补）

> 用途：文档5 里每个「数学部分」的教科书级推导，逐步展开、每步给理由。你数学底子（微积分、线性代数）够用，这里补的是**「为什么」这一层**。
> 记号约定：位移 $u=(u,v,w)$ 三分量；下标逗号表导数，如 $\partial u/\partial x = u_{,x}$；张量分量写法与矩阵写法并用。

### A.1 记号准备：$\nabla u$ 到底是哪 9 个数

**目标**：看懂 `ufl.grad(u)` 的数学含义（§5.4）。

位移是矢量场 $u = (u_x, u_y, u_z)$，它的梯度是一个 **3×3 矩阵**，第 $i$ 行第 $j$ 列 = 第 $i$ 个分量对第 $j$ 个坐标的偏导：

$$\nabla u =
\begin{bmatrix}
\dfrac{\partial u_x}{\partial x} & \dfrac{\partial u_x}{\partial y} & \dfrac{\partial u_x}{\partial z} \\[6pt]
\dfrac{\partial u_y}{\partial x} & \dfrac{\partial u_y}{\partial y} & \dfrac{\partial u_y}{\partial z} \\[6pt]
\dfrac{\partial u_z}{\partial x} & \dfrac{\partial u_z}{\partial y} & \dfrac{\partial u_z}{\partial z}
\end{bmatrix}$$

**逐步理解**（3 层）：

1. **它描述「邻居怎么动」**：$x$ 点附近一个微元 $\mathrm{d}x = (\mathrm{d}x_1, \mathrm{d}x_2, \mathrm{d}x_3)$，它的位移增量是
$$\mathrm{d}u_i = \sum_{j=1}^{3} \frac{\partial u_i}{\partial x_j}\, \mathrm{d}x_j$$
矩阵的第 $j$ 列就是「往 $j$ 方向挪一点，位移跟着变多少」。
2. **对角线是拉伸**：$\partial u_x/\partial x$ = 位移在 $x$ 方向的变化率 = $x$ 方向的伸长率（一维的 $\varepsilon = du/dx$ 就是它，见 A.2）。
3. **非对角线是剪切+转动混合**：$\partial u_y/\partial x$ 描述「$x$ 方向相邻点的 $y$ 向位移差」——里面既有剪切变形也有刚体转动（怎么拆，见 A.3）。

**自检**：写出 $\nabla u$ 第 2 行第 1 列的元素是什么？（答案：$\partial u_y/\partial x$，即 $v_{,x}$）

### A.2 一维应变：为什么 $\varepsilon = du/dx$

**目标**：从几何推出应变定义（§4.3 文档3 的公式，这里补推导）。

**逐步推导**：

1. 一根杆，取 $x$ 处长度 $\mathrm{d}x$ 的微元。变形后 $x$ 点走到 $x+u(x)$，$x+\mathrm{d}x$ 点走到 $x+\mathrm{d}x+u(x+\mathrm{d}x)$；
2. 微元**变形后的长度**：
$$[x+\mathrm{d}x+u(x+\mathrm{d}x)] - [x+u(x)] = \mathrm{d}x + [u(x+\mathrm{d}x) - u(x)]$$
3. **伸长量** = 变形后长度 − 原长 = $u(x+\mathrm{d}x) - u(x)$；
4. 应变 = 伸长量 ÷ 原长（相对变形）：
$$\varepsilon = \frac{u(x+\mathrm{d}x) - u(x)}{\mathrm{d}x}$$
5. 令 $\mathrm{d}x \to 0$，商趋近导数：
$$\varepsilon = \frac{\mathrm{d}u}{\mathrm{d}x} \qquad \text{（均匀拉伸时 } u(x)=\varepsilon x \text{，斜率就是应变）}$$

**为什么用相对变形**：1 cm 伸长对 1 m 杆和 100 m 杆意义完全不同（§4.2 文档3）——应变消除尺寸影响。

**自检**：$u(x) = 0.001x$（即每米伸长 1 mm），$\varepsilon = ?$（答案：0.001，无量纲）

### A.3 小变形应变张量：为什么是 $\frac{1}{2}(\nabla u + \nabla u^T)$

**目标**：看懂 `ufl.sym(ufl.grad(u))`（§5.4）——为什么取对称部分、为什么有 ½。

**逐步推导**：

1. **任何矩阵都能拆成对称 + 反对称两部分**（线代事实）：
$$\nabla u = \underbrace{\tfrac{1}{2}\big(\nabla u + \nabla u^T\big)}_{\text{对称部分 } \varepsilon} + \underbrace{\tfrac{1}{2}\big(\nabla u - \nabla u^T\big)}_{\text{反对称部分 } \omega}$$

2. **反对称部分 = 刚体转动，不产生应力**。二维例子：$u_x = -\theta y,\ u_y = \theta x$（绕原点转 $\theta$ 角）。
$$\nabla u = \begin{bmatrix}0 & -\theta \\ \theta & 0\end{bmatrix}$$
这是纯转动——物体没变形，只是转了个身。它的梯度**全是反对称的**，对称部分为零 → 应变零 → 应力零（合理！转一下不产生应力）。

3. **对称部分 = 真实变形**。二维纯剪切：$u_x = \gamma y,\ u_y = 0$（上表面相对下表面错动 $\gamma$）。
$$\nabla u = \begin{bmatrix}0 & \gamma \\ 0 & 0\end{bmatrix} \;\Rightarrow\; \varepsilon = \frac{1}{2}\begin{bmatrix}0 & \gamma \\ \gamma & 0\end{bmatrix}$$
所以 $\varepsilon_{xy} = \gamma/2$。

4. **½ 从哪来**：工程上习惯用**剪切角** $\gamma_{xy}$（正方形微元角度的总变化量）描述剪切，而 $\gamma_{xy} = \partial u_x/\partial y + \partial u_y/\partial x$（两个边的转动角之和，画图可验证）。张量应变取**一半**：$\varepsilon_{xy} = \tfrac{1}{2}\gamma_{xy}$——这样它作为张量在坐标旋转下才服从正确的变换法则。**记忆：工程剪应变 $\gamma = 2\varepsilon$，差个 2。**

5. **三个正应变 + 三个剪应变**（文档3 §5.4 的 6 个分量）：
$$\varepsilon_{xx} = \frac{\partial u}{\partial x},\quad \varepsilon_{yy} = \frac{\partial v}{\partial y},\quad \varepsilon_{zz} = \frac{\partial w}{\partial z}$$
$$\varepsilon_{xy} = \frac{1}{2}\Big(\frac{\partial u}{\partial y} + \frac{\partial v}{\partial x}\Big),\quad \varepsilon_{yz} = \frac{1}{2}\Big(\frac{\partial v}{\partial z} + \frac{\partial w}{\partial y}\Big),\quad \varepsilon_{zx} = \frac{1}{2}\Big(\frac{\partial w}{\partial x} + \frac{\partial u}{\partial z}\Big)$$

**自检**：$u = (0, 0, 0.001z)$（均匀竖向拉伸），写出 $\varepsilon$ 矩阵（答案：只有 $\varepsilon_{zz}=0.001$，其余全零）。

### A.4 应力张量为什么对称：力矩平衡

**目标**：看懂文档3 §5.4 的 $\tau_{xy} = \tau_{yx}$（9 个分量 → 6 个）。

**逐步推导**（取平面微元，单位厚度）：

1. 微元 $x$ 方向边长 $\mathrm{d}x$、$y$ 方向边长 $\mathrm{d}y$。面上有剪应力：右面 $\tau_{xy}$（沿 $y$ 向）、顶面 $\tau_{yx}$（沿 $x$ 向）；
2. 对中心取**力矩平衡**（微元不转）：
$$\tau_{xy}\,(\mathrm{d}y \cdot 1)\,\mathrm{d}x = \tau_{yx}\,(\mathrm{d}x \cdot 1)\,\mathrm{d}y$$
（左 = 右面剪力 × 力臂 $\mathrm{d}x$；右 = 顶面剪力 × 力臂 $\mathrm{d}y$）；
3. 约掉 $\mathrm{d}x\,\mathrm{d}y$：$\tau_{xy} = \tau_{yx}$ ✓

**结论**：对称性来自**角动量平衡**（不是假设，是力学定律）。所以独立分量 9 → 6。FEniCSx 里 `("Lagrange", 1, (3,3))` 存应力/应变，对称部分自动处理。

**自检**：$\sigma_{ij}$ 角标规则——$\tau_{xy}$ 表示什么？（答案：作用在垂直于 $x$ 的面上、沿 $y$ 方向的剪应力）

### A.5 拉梅常数：从 $E, \nu$ 推出 $\lambda, \mu$（完整代数）

**目标**：看懂代码 `lam = E*nu/((1+nu)*(1-2*nu)); mu = E/(2*(1+nu))`（§6.3）——为什么是这两个式子。

**第 0 步：三维胡克定律长什么样**

各向同性线弹性材料，应力与应变成正比，且只有两个独立材料常数。最一般的写法：

$$\sigma_{ij} = \lambda\,\delta_{ij}\,\varepsilon_{kk} + 2\mu\,\varepsilon_{ij}$$

（$\delta_{ij}$ 是 Kronecker 记号：$i=j$ 时 1，否则 0；$\varepsilon_{kk} = \varepsilon_{xx}+\varepsilon_{yy}+\varepsilon_{zz}$ 是体积应变——**求和约定**：重复下标自动求和。）

矩阵形式就是代码里的：$\boldsymbol{\sigma} = \lambda\,\mathrm{tr}(\varepsilon)\,\boldsymbol{I} + 2\mu\,\varepsilon$。

**为什么只有两个常数**：各向同性 = 材料没有「偏爱方向」，此时连接两个对称张量（$\sigma$ 和 $\varepsilon$）的线性映射只有一个自由标量函数，拆成「体积部分」（$\lambda$）和「形状部分」（$\mu$）两块——这就是 $\lambda$、$\mu$ 的物理身份。

**第 1 步：$E$ 和 $\nu$ 是什么（试验定义）**

单轴拉伸试验：只沿 $z$ 方向拉，应力 $\sigma_{zz} = \sigma_0$，其余应力分量为零。

实测两个量（这是**定义**，不是推导）：

- 弹性模量：$E \equiv \dfrac{\sigma_0}{\varepsilon_{zz}}$（轴向应力 ÷ 轴向应变）
- 泊松比：$\nu \equiv -\dfrac{\varepsilon_{xx}}{\varepsilon_{zz}} = -\dfrac{\varepsilon_{yy}}{\varepsilon_{zz}}$（横向收缩 ÷ 轴向伸长，取负号使 $\nu>0$）

所以单轴试验下：$\varepsilon_{zz} = \sigma_0/E$，$\varepsilon_{xx} = \varepsilon_{yy} = -\nu\sigma_0/E$，剪应变全零。

**第 2 步：把试验结果代回本构**

本构的 $zz$ 分量（$i=j=z$）：$\sigma_{zz} = \lambda(\varepsilon_{xx}+\varepsilon_{yy}+\varepsilon_{zz}) + 2\mu\varepsilon_{zz}$

代入试验值：
$$\sigma_0 = \lambda\Big(-\frac{\nu\sigma_0}{E} - \frac{\nu\sigma_0}{E} + \frac{\sigma_0}{E}\Big) + 2\mu\frac{\sigma_0}{E} = \lambda\frac{\sigma_0(1-2\nu)}{E} + 2\mu\frac{\sigma_0}{E}$$

两边除以 $\sigma_0$（≠0）：
$$\boxed{1 = \frac{\lambda(1-2\nu)}{E} + \frac{2\mu}{E}} \qquad \text{(I)}$$

本构的 $xx$ 分量（$\sigma_{xx} = 0$）：
$$0 = \lambda(\varepsilon_{xx}+\varepsilon_{yy}+\varepsilon_{zz}) + 2\mu\varepsilon_{xx} = \lambda\frac{\sigma_0(1-2\nu)}{E} + 2\mu\Big(-\frac{\nu\sigma_0}{E}\Big)$$

除以 $\sigma_0/E$：
$$\boxed{0 = \lambda(1-2\nu) - 2\mu\nu} \qquad \text{(II)}$$

**第 3 步：解二元一次方程组**

由 (II)：$\lambda(1-2\nu) = 2\mu\nu$。代入 (I)：
$$1 = \frac{2\mu\nu}{E} + \frac{2\mu}{E} = \frac{2\mu(1+\nu)}{E} \;\Rightarrow\; \boxed{\mu = \frac{E}{2(1+\nu)}}$$

代回 (II)：$\lambda(1-2\nu) = 2\mu\nu = \dfrac{E\nu}{1+\nu} \;\Rightarrow\; \boxed{\lambda = \dfrac{E\nu}{(1+\nu)(1-2\nu)}}$

**第 4 步：验证**

- 量纲：$E$ 是 Pa，$\lambda,\mu$ 都是 Pa ✓（代码里 `lam`、`mu` 与 `E` 同单位）；
- 数值（万神殿混凝土 $E=14.8$ GPa, $\nu=0.2$）：$\mu = 14.8/(2\times1.2) = 6.167$ GPa；$\lambda = 14.8\times0.2/(1.2\times0.6) = 4.111$ GPa；
- 特例：$\nu \to 0.5$（不可压缩）时 $\lambda \to \infty$——公式分母 $(1-2\nu)\to 0$，与「橡胶不可压缩、$\lambda$ 巨大」的物理一致 ✓。

**自检**：用手算验证 $\lambda = 4.111$ GPa（按上面数字走一遍）。

### A.6 泊松方程：从强形式到弱形式的完整推导

**目标**：看懂 `a = ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx`（§2.3）——为什么弱形式长这样。

**强形式**（每点严格成立）：$-\nabla^2 u = f$ 于 $\Omega$ 内，$u = 0$ 于边界 $\partial\Omega$。

**逐步推导**：

1. **乘测试函数** $v$（先假设 $v$ 在边界上为零，$v|_{\partial\Omega}=0$）：
$$-\nabla^2 u \cdot v = f \cdot v$$

2. **全区域积分**：$$\int_\Omega -\nabla^2 u\, v\, \mathrm{d}x = \int_\Omega f\, v\, \mathrm{d}x$$

3. **分部积分**（格林第一公式——把二阶导数降成一阶）：
$$\int_\Omega -\nabla^2 u\, v\, \mathrm{d}x = \int_\Omega \nabla u \cdot \nabla v\, \mathrm{d}x - \int_{\partial\Omega} \frac{\partial u}{\partial n}\, v\, \mathrm{d}s$$
> 一维类比就是「分部积分」：$\int -u''v = \int u'v' - [u'v]_{\text{端点}}$。二维/三维的 $\int_{\partial\Omega}(\partial u/\partial n)v$ 就是「端点项」的推广。

4. **边界项消失**：因为 $v|_{\partial\Omega} = 0$，边界积分 = 0。

5. **得到弱形式**：
$$\boxed{\int_\Omega \nabla u \cdot \nabla v\, \mathrm{d}x = \int_\Omega f\, v\, \mathrm{d}x}$$
左端 = UFL 的 `ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx`，右端 = `f * v * ufl.dx`——**代码就是公式的直译**。

**两个关键收获**：

- **「弱」在哪**：导数阶数从 2 降到 1——对解的光滑性要求降低（原来要二阶可导，现在一阶可导+平方可积即可）。这是 FEM 能用分片多项式（形函数）逼近的前提；
- **边界条件去哪了**：$u=0$ 是「强制」施加的（`dirichletbc`）；$v=0$ 让边界项消失——固定边界的测试函数自动「消化」了边界积分。

**自检**：如果边界条件是 $u=g\neq 0$，推导哪里会变？（提示：$v$ 还是取边界为零——强制 BC 用 `dirichletbc` 直接赋值，弱形式本身不变）

### A.7 线弹性：从平衡方程到虚功方程的完整推导

**目标**：看懂 `a = ufl.inner(sigma(u), epsilon(v)) * ufl.dx`（§6.2）——为什么应力跟**应变**收缩，而不是跟 $\nabla v$。

**强形式**（每点平衡）：$\mathrm{div}\,\boldsymbol{\sigma} + b = 0$，即分量形式 $\sigma_{ij,j} + b_i = 0$（求和约定，逗号表导数）。

**逐步推导**：

1. **点乘虚拟位移** $v$ 并积分：
$$\int_\Omega (\sigma_{ij,j} + b_i)\, v_i\, \mathrm{d}x = 0$$

2. **对第一项分部积分**（乘积法则 $(\sigma_{ij}v_i)_{,j} = \sigma_{ij,j}v_i + \sigma_{ij}v_{i,j}$，两边积分 + 散度定理）：
$$\int_\Omega \sigma_{ij,j}\, v_i\, \mathrm{d}x = -\int_\Omega \sigma_{ij}\, v_{i,j}\, \mathrm{d}x + \int_{\partial\Omega} \sigma_{ij}n_j\, v_i\, \mathrm{d}s$$

3. **面力项**：$\sigma_{ij}n_j = t_i$（面力 = 应力矢量，柯西公式）——这是**自然边界条件**，自动出现；
4. **整理**：
$$\int_\Omega \sigma_{ij}\, v_{i,j}\, \mathrm{d}x = \int_\Omega b_i v_i\, \mathrm{d}x + \int_{\partial\Omega} t_i v_i\, \mathrm{d}s$$

5. **关键一步：利用 $\sigma$ 对称**。把 $v_{i,j}$ 拆成对称+反对称（A.3 的分解）：
$$v_{i,j} = \underbrace{\tfrac{1}{2}(v_{i,j}+v_{j,i})}_{\varepsilon_{ij}(v)} + \underbrace{\tfrac{1}{2}(v_{i,j}-v_{j,i})}_{\omega_{ij}(v)}$$
$\sigma_{ij}$ 对称（A.4）与反对称部分收缩为零：$\sigma_{ij}\omega_{ij} = 0$。所以：
$$\sigma_{ij}\, v_{i,j} = \sigma_{ij}\, \varepsilon_{ij}(v) = \boldsymbol{\sigma} : \boldsymbol{\varepsilon}(v)$$

6. **得到虚功方程**：
$$\boxed{\int_\Omega \boldsymbol{\sigma} : \boldsymbol{\varepsilon}(v)\, \mathrm{d}x = \int_\Omega b \cdot v\, \mathrm{d}x + \int_{\partial\Omega} t \cdot v\, \mathrm{d}s}$$
左 = 内力虚功，右 = 外力虚功（体力 + 面力）。**物理**：对任意虚拟位移 $v$，外力做的虚功 = 内力吸收的虚功（能量守恒的力学写法，文档3 §7.3）。

**为什么代码里是 `sigma(u)` 配 `epsilon(v)`**：因为应力对称，收缩时只有对称的应变部分「接得住」——这就是 `ufl.sym(ufl.grad(v))` 出现在弱形式里而**不是** `ufl.grad(v)` 的原因（§5.5 的 `epsilon` 函数）。

**自检**：如果忘记取对称（直接用 `grad(v)`），弱形式会怎样？（提示：数学上不成立——反对称部分白收缩，数值上会得到错误/不稳定的刚度矩阵）

### A.8 自由度：11×11 = 121 是怎么来的

**目标**：看懂 §2.5 的预期输出「自由度 = 121」和 §3.5 的 $V.dofmap.index_map.size\_global$。

**逐步推导**：

1. 10×10 网格 → 每个方向 10 段 → 节点数 = (10+1)×(10+1) = 121 个节点；
2. 一阶标量空间：每个节点 1 个未知量（一个数 $u$）；
3. 总自由度 = 节点数 × 每节点自由度 = 121 × 1 = **121** ✓；
4. 二阶四面体 + 位移（万神殿）：每个节点 3 个分量 → 每单元 10 节点 × 3 = **30 自由度/单元**（§3.4 文档3）；10 万节点 → 30 万自由度——这就是为什么需要稀疏求解器。

**自检**：20×20 一阶标量网格自由度？（答案：21×21 = 441，文档5 §2.6 实验 A 的答案）

### A.9 主应力：为什么是特征值问题

**目标**：看懂 `np.linalg.eigvalsh(sigma_nodes)` 和「σ1 是最后一列」（§8.5）。

**逐步推导**：

1. **问题**：同一个应力状态，换个坐标系看剪应力可能消失。找一组坐标轴，使该点只有正应力——这组轴方向上的应力就叫**主应力**；
2. **数学化**：设 $n$ 是要找的方向。该方向面上的应力矢量 = $\boldsymbol{\sigma} n$。要求「只有正应力、无剪应力」= 应力矢量与 $n$ 平行：
$$\boldsymbol{\sigma}\, n = \sigma\, n$$
这就是**特征值问题**：$n$ 是特征向量，$\sigma$ 是特征值；
3. **为什么一定有解**：$\boldsymbol{\sigma}$ 是对称矩阵（A.4），对称矩阵**必可对角化且特征值为实数**（线代定理）——三个特征值 $\sigma_1 \ge \sigma_2 \ge \sigma_3$ 就是三个主应力，对应的特征向量就是主方向（互相正交）；
4. **物理意义**：$\sigma_1$ = 该点能看到的**最大拉应力**。万神殿混凝土抗拉只有 0.08 MPa——$\sigma_1$ 超过它就「名义开裂」，所以要算它（§8.5）；
5. **代码对应**：`eigvalsh` = 对称矩阵特征值（用专门算法，比通用 `eig` 快且稳）；返回**升序**排列 → σ1（最大）在**最后一列**：`principal[:, -1]`。

**自检**：某点 $\sigma_{xx}=5$ MPa, $\sigma_{yy}=0$, $\tau_{xy}=3$ MPa（其余 0）。用 2×2 特征值手算 σ1（提示：特征多项式 $\det(\sigma - \sigma I)=0$，答案：$\sigma_{1,2} = \frac{5}{2} \pm \frac{\sqrt{25+36}}{2} \approx 6.41$ 或 $-1.41$ MPa）。

### A.10 子域积分：$dx(1000)$ 和 $ds(400)$ 的数学意义

**目标**：看懂 §5.6 的 `ufl.dx(1000)` / `ufl.ds(400)`。

**逐步说明**：

1. 积分可加性：$\displaystyle\int_\Omega = \sum_k \int_{\Omega_k}$——把整个域切成若干子域分别积分再相加；
2. FEniCSx 的 `ufl.dx` 默认在整个域积；`ufl.dx(1000)` 只对**物理组 1000 的单元**积分（不同材料分区：$\int_{\Omega_{1000}} \sigma:\varepsilon\, dx$ 用 1000 区的材料参数）；
3. `ufl.ds` 是边界积分（面积分），`ufl.ds(400)` 只在物理组 400 的**面单元**上积（面力：$\int_{\Gamma_{400}} t\cdot v\, ds$）；
4. 背后机制：网格读入时每个单元/面都带着物理组标签（`cell_tags`/`facet_tags`），积分时 FEniCSx 按标签筛选单元/面，等价于数学上的区域分解。

**自检**：想给拱脚面（400）施加面力 $t$，UFL 怎么写？（答案：`ufl.dot(t, v) * ufl.ds(400)`）

### A.11 干缩与自由应变：为什么「自由」就没应力（C4 预习）

**目标**：看懂 §10.2 的 `eps_mech = eps_total - eps_sh * I`。

**逐步说明**：

1. 总应变拆成两部分：$\varepsilon_{总} = \varepsilon_{力学} + \varepsilon_{自由}$。自由应变（干缩/热胀）**不产生应力**——它只是「想变形」；
2. 应力只由**力学应变**产生：$\sigma = \lambda\,\mathrm{tr}(\varepsilon_{力学})I + 2\mu\varepsilon_{力学}$；
3. 干缩类比：湿布晾干变小——如果布自由放着，收缩不产生内力；如果把布两头钉死，收缩被阻止 → 产生拉应力；
4. 代码：`eps_mech = eps_total - eps_sh * ufl.Identity(3)`（$\varepsilon_{sh}I$ 是各向同性自由应变，三个方向一样），应力公式里的 `eps_total` 换成 `eps_mech`；
5. 数学验证：自由收缩时 $\varepsilon_{总} = \varepsilon_{sh}I$ → $\varepsilon_{力学}=0$ → $\sigma = 0$ ✓（与「自由不产生应力」一致）。

**自检**：为什么干缩应变前面乘 `Identity(3)` 而不是标量？（答案：应变是张量，要凑成对角张量 $\varepsilon_{sh}\delta_{ij}$）

---

*本速查由AI 助手于 2026-08-15 起草，素材全部取自文档5 v2.0 正文；你精读后审阅，发现与原文不一致处以文档5 为准。数学附录记号与文档3（第 4/5/7 章、附录 A）保持一致。*

---

## 实战增补 · dolfinx 0.8 战役 API 速查（2026-08 实测）

> 本章收录六个求解器实战中实测验证的 API、参数与数据布局（含 P-04~P-07 修正版）。与正文速查互补：正文是官方口径，本章是实测口径。

### 增补 1：核心 API 实测签名

| API | 实测用法 | 坑/备注 |
| --- | --- | --- |
| `gmshio.read_from_msh(path, MPI.COMM_WORLD, gdim=3)` | 读网格+物理组 | 返回 (domain, cell_tags, facet_tags)；`facet_tags.find(400)` 取拱脚面 |
| `fem.functionspace(domain, ("Lagrange", 2, (3,)))` | CG2 矢量空间 | 总纲锁定单元 |
| `fem.locate_dofs_topological(V, 2, facets)` | 面上的自由度 | 子空间版本返回 **list**，需 `np.concatenate([np.asarray(a).reshape(-1) for a in dofs_y])` 摊平（P-07 系列） |
| `fem.dirichletbc(fem.Constant(domain,(0.,0.,0.)), dofs, V)` | 固支 | **必须 fem.Constant**（ufl.Constant 报 dtype/rank 错） |
| `fem.Expression(expr, X)` | 应力投影 | X=`S.element.interpolation_points()`——**0.8 新 API**（旧 `(expr, W.element)` 失效，P-05） |
| `S.tabulate_dof_coordinates()` | 自由度坐标 | 张量空间**按点去重**返回 (N,3)，非 9N——运行时自适应布局（P-07b） |
| `VTXWriter(comm, path, [fn])` | 导出 .bp | **同元素类型分导**（位移 P2 矢量 / 应力 P1 张量分开，P-06） |
| `domain.topology.connectivity(3, 0)` | 单元→顶点表 | BFS 连通域分析的建图基础 |

### 增补 2：NumPy 后处理武器库（求解器统计层实战）

| 用法 | 作用 | 实测案例 |
| --- | --- | --- |
| `uh.x.array.reshape(-1,3)` | PETSc 解向量 → 每节点 3 分量 | u_mag = sqrt(sum(..., axis=1)) |
| `np.linalg.eigvalsh(sigma_nodes)` | 对称矩阵特征值（升序） | 最后一列 σ1、第一列 σ3 |
| `np.einsum("ni,nij,nj->n", e_th, sig, e_th)` | 环向应力投影 σ_θθ | 转压带统计 |
| `np.where(x[2]>=0.0, 1350.0, 1600.0)` | callable 场赋值 | 密度分层（P-04 修正法） |
| `interpolate(lambda x: fill(x)[0])` | 函数式插值 | 分区材料场（c6：E/rho 按 z 三层） |
| BFS（collections.deque） | 连通域分解 | 最大连通裂缝簇口径 |

### 增补 3：PETSc 求解器选项速查（实测）

| 选项 | 值 | 场景 |
| --- | --- | --- |
| ksp_type | cg | 共轭梯度迭代法（时间换内存） |
| pc_type / pc_hypre_type | hypre / boomeramg | 代数多重网格预处理 |
| ksp_rtol | 1e-8 | 相对残差容限（实测残差 6e-2→4e-10） |
| （默认 LU） | mumps | 小模型直解；97 万 DOF 起内存爆 |

### 增补 4：弱形式 UFL 速查（实战全案）

| 表达式 | 数学 | 实测位置 |
| --- | --- | --- |
| `ufl.sym(ufl.grad(w))` | ε=½(∇w+∇wᵀ) | 所有求解器 |
| `ufl.tr(...)` / `ufl.Identity(3)` | 迹 / 单位张量 | 本构 |
| `ufl.inner(sigma(u), epsilon(v))*ufl.dx` | 内虚功 | 左端 a |
| `ufl.dot(b, v)*ufl.dx` | 外虚功（自重） | 右端 L |
| `-eps_sh*(3*lam+2*mu)*ufl.div(v)*ufl.dx` | **干缩等效荷载** | P-07 符号修正版 |
| `ufl.Measure("ds", domain, subdomain_data=facet_tags)` | 面测度 | C5 罚函数 `a += gamma*(n·u)(n·v)*ds(600)` |

### 增补 5：数据布局铁律（P-07b 教训）

- **D 场与应力 P1 空间 dof 编号一致**（同网格同族）→ 直接 `D_field.x.array[:] = ...` 向量写入，免插值；
- **统计坐标系 = 自由度坐标系 ≠ 网格节点坐标系**（二阶网格含边中点）；
- **任何布局假设用 assert 守护**：`assert D_field.x.array.size == n_pts, "损伤场与应力点布局不一致"`。

### 增补小练习

1. 写出「读网格→固支→自重→求解→主应力」的七步伪代码（每步一行 API）。
2. 解释 tabulate_dof_coordinates 为什么可能返回两种布局，代码怎么自适应。
3. 罚函数项 `gamma*(n·u)(n·v)*ds(600)` 里 gamma 越大越接近什么？

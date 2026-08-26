# 文档4 · Gmsh 三维几何建模与网格划分完全教程（重构版）

> **项目**：万神殿穹顶三维 FEM 重构
> **版本**：v2.0 轮次 1/14（2026-08-13 起逐轮重写）
> **前置要求**：文档0（环境已搭好）、文档3（有限元基础已读完）
> **配套环境**：WSL2 Ubuntu 22.04 + `pantheon-fem` conda 环境
> **学习方式**：**每章必须亲手运行示例**。只看不跑，等于没读。

---

## 写给你的使用说明（30 秒读完）

这本教材和旧版最大的区别：**不再一次倒出一大锅知识，而是每一章只讲一个主题，讲透为止**。

- 每一章的结构固定：**学习目标 → 白话引入 → 概念讲解 → 完整示例 → 逐行拆解 → 运行验证 → 常见问题 → 小练习 → 本章小结**；
- 每个英文术语第一次出现时，旁边就有中文和一句话解释；
- 每个示例都标注了「在哪运行、怎么运行、应该看到什么」；
- 每章末尾的练习是**必做**的，它们是下一章的垫脚石；
- 卡住超过 15 分钟，先看本章「常见问题」，再去找你身边的 AI 助手。

### 🎩 老板版速读（60 秒，Leader 必读）

你不需要会写 Gmsh 代码，但必须能**验收 AI 写的建模脚本**。只记四件事：

1. **六步骨架**：开机 → 建模型 → 建几何 → 同步 → 撒网 → 存盘 → 关机（`synchronize` 漏掉 = 几何消失）；
2. **球壳 = 外球 cut 内球**；布尔运算后 tag 会变，必须从结果里重新取；
3. **物理组编号约定**：200 内表面 / 300 外表面 / 400 拱脚 / 1000 穹顶体（AI 贴错，FEniCSx 就找不到边界）；
4. **验收三问**：能跑通？生成的是壳不是两个球？参数来自 `params.py`（无魔法数字）？

其余细节（rotate 角度、包围盒、藻井）用到时查本教材或指挥手册 §5。

**本教程共 14 轮，当前进度**：

| 轮次 | 内容 | 状态 |
| --- | --- | --- |
| 1 | 学习地图 + Gmsh 是什么 + 第一个程序（立方体） | ✅ 本轮 |
| 2 | 几何实体：点/线/面/体 + 球、方块、圆柱、圆锥台 | 待写 |
| 3 | 布尔运算入门：并集、交集、差集（小方块图解） | 待写 |
| 4 | 球壳 = 外球 − 内球（核心专题） | 待写 |
| 5 | 网格专题：尺寸控制、1D/2D/3D、节点与单元 | 待写 |
| 6 | 物理组专题：给面/体贴标签 | 待写 |
| 7 | 导出与预览：.msh、Gmsh GUI、PyVista | 待写 |
| 8 | 参数化球面与变厚度球壳（数学铺垫） | 待写 |
| 9 | C0 实战：从零写球壳脚本 | 待写 |
| 10 | Oculus 开口与藻井专题 | 待写 |
| 11 | 鼓座、基座与几何装配 | 待写 |
| 12 | 网格局部加密与 28 周期对称 | 待写 |
| 13 | 二阶网格、网格质量评估与完整案例 | 待写 |
| 14 | 全书统稿：术语表、练习答案、坑点索引、审核清单 | 待写 |

---

## 第 0 章 出发之前：学习地图

### 0.1 学完这本书，你能做什么？

学完本教程，你将能独立完成以下五件事：

1. 用 Gmsh 的 Python 接口（API）创建**参数化三维几何**——改一个数字，模型自动变；
2. 用**布尔运算**把球、方块、圆柱组合成复杂形状（球壳、藻井、鼓座）；
3. 给几何**划分网格**，并控制网格的粗细；
4. 给不同的面和体**贴物理组标签**，让求解器 FEniCSx 认得它们；
5. 把网格**导出**为 `.msh` 文件，并在 PyVista 里预览。

一句话版本：**从「只有参数」到「有了可以交给 FEniCSx 求解的网格文件」**。

### 0.2 全书地图

| 章节 | 内容 | 难度 | 与 C0 的关系 |
| --- | --- | --- | --- |
| 第 1 章 | Gmsh 是什么 + 环境自检 | 🟢 入门 | 热身 |
| 第 2 章 | 第一个 Gmsh 程序：立方体 | 🟢 入门 | 热身 |
| 第 3 章 | 几何实体与基本几何体 | 🟢 入门 | 球体直接用 |
| 第 4 章 | 布尔运算入门 | 🟢 入门 | 球壳的核心 |
| 第 5 章 | 球壳 = 外球 − 内球 | 🟡 重点 | **C0 心脏** |
| 第 6 章 | 网格划分基础 | 🟢 入门 | C0 需要 |
| 第 7 章 | 物理组标记 | 🟡 重点 | C0 需要 |
| 第 8 章 | 导出与预览 | 🟢 入门 | C0 验收 |
| 第 9 章 | 参数化球面与变厚度 | 🟡 重点 | C0 直接相关 |
| 第 10 章 | C0 实战：球壳脚本 | 🔴 实战 | **C0 验收** |
| 第 11 章 | Oculus 开口与藻井 | 🟡 项目 | 后续算例 |
| 第 12 章 | 鼓座与几何装配 | 🟡 项目 | C2 算例 |
| 第 13 章 | 加密、对称、二阶网格 | 🔴 进阶 | 后续算例 |
| 第 14 章 | 术语表与坑点索引 | 🟢 工具 | 随时查 |

> 🟢 = 入门必读　🟡 = 重点必读　🔴 = 实战/进阶

### 0.3 学习路线（主线 vs 支线）

- **主线**（必须精读，逐章完成练习）：第 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 章。这十章直接支撑 C0 球壳脚本。
- **支线**（先通读了解，用到再回来精读）：第 11 → 12 → 13 章。藻井、鼓座、对称切片是后续算例的事。
- **工具**（不按顺序读，卡住就查）：第 14 章。

**主线约 10 个番茄钟**（每个 25 分钟）：

| 番茄钟 | 内容 |
| --- | --- |
| 1–2 | 第 1–2 章：跑通第一个程序 |
| 3–4 | 第 3–4 章：几何体 + 布尔入门 |
| 5–6 | 第 5 章：球壳（重点，可放慢） |
| 7 | 第 6 章：网格 |
| 8 | 第 7 章：物理组 |
| 9 | 第 8–9 章：导出 + 参数化 |
| 10 | 第 10 章：C0 实战 |

### 0.4 出发前检查单

开始之前，请确认：

- [ ] WSL2 里能打开 Ubuntu 终端；
- [ ] `pantheon-fem` 环境能激活（终端提示符前有 `(pantheon-fem)`）；
- [ ] 能在 WSL 里进入项目目录 `/mnt/c/Users/tan83/Desktop/codex/pantheon-3d-fem`；
- [ ] 手边有 VS Code（WSL 远程模式）或任意文本编辑器。

如果以上有任意一项没确认，先去文档0 补齐，再回来。

---

## 第 1 章 Gmsh 是什么

### 1.1 一句话版本

**Gmsh 是一个免费开源的三维网格生成器：你告诉它「几何长什么样」，它帮你切成成千上万个小块（网格），供有限元求解器计算。**

### 1.2 为什么有限元需要网格？（先讲道理）

有限元方法的核心思想是：**把连续的整体，切成有限个小块，用每块上的近似解拼出整体解**。

打个比方。你想算一块披萨每一处的温度分布，但数学上直接算整块披萨太难。于是你把披萨切成很多小三角块：

- 每一小块很小，可以认为它内部的温度近似不变或线性变化；
- 把所有小块的结果拼起来，就得到整块披萨的温度场；
- 切得越细（网格越密），结果越接近真实，但计算量越大。

**网格（mesh）就是这些小块的总称。** 生成网格这件事，就是 Gmsh 的看家本领。

### 1.3 Gmsh 在项目流水线里的位置

整个万神殿 FEM 项目是一条流水线：

```text
参数（config/params.py）
   ↓
几何建模（Gmsh）          ← 本教程负责
   ↓
网格划分（Gmsh）
   ↓
.msh 网格文件
   ↓
有限元求解（FEniCSx）     ← 文档5 负责
   ↓
结果可视化（PyVista / Matplotlib）  ← 文档6、7 负责
```

Gmsh 负责流水线的**前两站**：把参数变成几何，把几何切成网格。

### 1.4 为什么要用 Python 接口，而不是鼠标点界面？

Gmsh 有两种用法：

| 用法 | 适合场景 | 本项目用不用 |
| --- | --- | --- |
| GUI 图形界面 | 临时看一眼模型、手动调整 | 偶尔预览 |
| Python 接口（API） | 参数化、自动化、可复现 | **主力** |

万神殿穹顶的几何非常复杂：变厚度球壳、140 个藻井、鼓座、28 周期对称。用鼠标在 GUI 里画，画到天亮也画不完，还无法复现。用代码写，**改一个参数重跑一次，模型就自动更新**——这就是「参数化」。

### 1.5 Gmsh 的两个关键英文词（先混个脸熟）

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| API | 应用程序接口 | 别人写好的「遥控器按钮」，我们按按钮就行 |
| GUI | 图形界面 | 用鼠标点的窗口 |
| tag | 编号 | Gmsh 给每个几何实体发的整数身份证号 |
| entity | 实体 | 点、线、面、体的统称 |

### 1.6 第一次握手：验证环境（必做）

在 WSL 终端里，先激活环境并进入项目目录：

```bash
conda activate pantheon-fem
cd /mnt/c/Users/tan83/Desktop/codex/pantheon-3d-fem
```

然后运行下面的 5 行小脚本（这是**环境自检**，不是正式程序）：

```python
import gmsh
print("Gmsh 版本:", gmsh.__version__)
gmsh.initialize()
print("初始化成功 ✅")
gmsh.finalize()
print("关闭成功 ✅")
```

把代码保存为 `tools/env_gmsh_check.py`，然后运行：

```bash
python tools/env_gmsh_check.py
```

**预期输出**（版本号可能略有不同）：

```text
Gmsh 版本: 4.15.2
初始化成功 ✅
关闭成功 ✅
```

**如果报错，对照排查**：

| 报错 | 原因 | 解决 |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'gmsh'` | 没在 `pantheon-fem` 环境里运行，或 gmsh 没装 | 先 `conda activate pantheon-fem`；再 `pip install gmsh` |
| `NameError: name 'gmsh' is not defined` | import 那行写错了 | 检查第一行必须是 `import gmsh` |
| 提示找不到文件 | 当前目录不对 | 先 `cd` 到项目目录，或使用绝对路径 |

> **为什么要先握手？** 环境不对，后面所有示例都会卡在第一步。花 3 分钟确认环境，能省后面 3 小时。

### 1.7 本章小结

1. Gmsh = 免费开源三维网格生成器，负责「几何 → 网格」；
2. 有限元 = 把连续体切成小块近似求解，网格是这些小块；
3. 本项目用 Python 接口（API）而不是 GUI，因为要参数化和自动化；
4. `gmsh.initialize()` 开机，`gmsh.finalize()` 关机。

---

## 第 2 章 第一个 Gmsh 程序：画一个立方体

### 2.1 本章目标

跑通第一个完整的 Gmsh 程序，并理解它的**六步骨架**。这六步会出现在本书**每一个**程序里。

### 2.2 完整程序（先整体看一遍）

新建文件 `geometry/demo_cube.py`，内容如下：

```python
"""
第一个 Gmsh 程序：创建一个 1m x 1m x 1m 的立方体，
划分网格，导出为 .msh 文件。

运行方法：
    cd /mnt/c/Users/tan83/Desktop/codex/pantheon-3d-fem
    conda activate pantheon-fem
    python geometry/demo_cube.py
"""

import gmsh

# ---------- 1. 开机 ----------
gmsh.initialize()

# ---------- 2. 新建模型并命名 ----------
gmsh.model.add("cube_demo")

# ---------- 3. 创建几何：一个立方体 ----------
# 参数依次是：左下角坐标 (x, y, z) 和三个方向的边长 (dx, dy, dz)
cube = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
print("立方体 tag =", cube)

# OCC 内核采用「延迟评估」：上面的命令先记在小本本上，
# 调用 synchronize() 才真正执行。这是必须的一步！
gmsh.model.occ.synchronize()

# ---------- 4. 设置网格尺寸并划分网格 ----------
# CharacteristicLength = 特征长度 = 单元边长的目标大小
# 0.2 表示每个单元边长约 0.2 m
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 0.2)
gmsh.model.mesh.generate(3)   # 3 = 三维体网格

# ---------- 5. 导出 ----------
gmsh.write("output/meshes/cube_demo.msh")
print("已导出: output/meshes/cube_demo.msh")

# ---------- 6. 关机 ----------
gmsh.finalize()
```

### 2.3 逐行拆解（重点！）

整个程序只有六个动作，请对照代码看这张表：

| 行 | 函数 | 白话 | 备注 |
| --- | --- | --- | --- |
| 1 | `import gmsh` | 把 Gmsh 请进 Python | 所有脚本第一行 |
| 2 | `gmsh.initialize()` | **开机** | 不调用，后面全报错 |
| 3 | `gmsh.model.add("cube_demo")` | 新建一个模型，起名 | 名字随便起，别用中文 |
| 4 | `gmsh.model.occ.addBox(...)` | **加一块长方体坯料** | 返回整数 tag（身份证号） |
| 5 | `gmsh.model.occ.synchronize()` | **提交作业**：让 Gmsh 真正执行 | 忘记它 = 几何「凭空消失」 |
| 6 | `gmsh.option.setNumber(...)` | 拧旋钮：设网格粗细 | 0.2 = 单元边长约 0.2m |
| 7 | `gmsh.model.mesh.generate(3)` | **撒网**：生成三维网格 | 1=线，2=面，3=体 |
| 8 | `gmsh.write(...)` | **存盘**：导出 .msh 文件 | 给 FEniCSx 吃的文件 |
| 9 | `gmsh.finalize()` | **关机** | 好习惯 |

**重点理解 addBox 的参数**：

```python
gmsh.model.occ.addBox(0, 0, 0,   # 左下角坐标 x, y, z
                      1, 1, 1)   # 三个方向的边长 dx, dy, dz
```

这个立方体：

- 左下角在原点 `(0, 0, 0)`；
- 向 x 方向长 1 m，向 y 方向长 1 m，向 z 方向长 1 m；
- 所以它的体对角线顶点在 `(1, 1, 1)`。

**重点理解 `synchronize`（第 5 行）**：

OCC 内核的工作方式是「延迟评估」：你喊一声「我要加一个方块」，Gmsh 先记下来，等你喊「synchronize」才真的动手。好处是：连续做很多几何操作时可以一次性批量处理，速度快。坏处是：忘了 synchronize，后面查几何就是空的。

**经验法则：每次几何操作之后、查询或下一步操作之前，都要 `synchronize()`。**

### 2.4 运行前的小准备

脚本要把网格写到 `output/meshes/` 目录，这个目录可能还不存在。先创建它：

```bash
mkdir -p output/meshes
```

然后运行：

```bash
python geometry/demo_cube.py
```

### 2.5 预期输出

```text
立方体 tag = 1
已导出: output/meshes/cube_demo.msh
```

（第一次运行 Gmsh 可能会打印一些初始化信息，不影响结果。）

运行后检查文件：

```bash
ls -lh output/meshes/cube_demo.msh
```

正常情况下会看到一个几 KB 到几十 KB 的 `.msh` 文件。

### 2.6 三个小实验（动手！）

**实验 A：把立方体变成长方体**

把 `addBox` 的参数改成 `(0, 0, 0, 2, 1, 0.5)`，重跑。想一想：这个长方体向每个方向各长多少？左下角在哪？

**实验 B：把网格变细**

把 `Mesh.CharacteristicLengthMax` 从 `0.2` 改成 `0.05`，重跑，再用 `ls -lh` 看文件大小。

问题：网格变细后，文件变大了还是变小了？为什么？

**实验 C：改名**

把 `cube_demo` 改成 `my_first_cube`，把导出文件名改成 `output/meshes/my_first_cube.msh`，重跑。注意：模型名和文件名是两回事，都可以自己起。

### 2.7 常见问题（先自查，再求助）

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `ModuleNotFoundError` | 环境不对 | `conda activate pantheon-fem` |
| `Tag was not found` 之类的几何报错 | 忘了 `synchronize()` | 在 addBox 后补一行 |
| 运行成功但没看到文件 | 目录不存在 | `mkdir -p output/meshes` |
| 运行成功但文件很大/很小 | 网格太细/太粗 | 调 `CharacteristicLengthMax` |
| 中文乱码 | 文件编码问题 | 用 VS Code 保存为 UTF-8 |

### 2.8 本章小结

1. 所有 Gmsh 程序都是六步：**开机 → 建模型 → 建几何 → 撒网 → 存盘 → 关机**；
2. `addBox(x, y, z, dx, dy, dz)`：左下角 + 三个方向的长度；
3. `synchronize()` 是几何操作的「提交按钮」，**必须调用**；
4. `Mesh.CharacteristicLengthMax` 控制网格粗细：数字越小，网格越密，文件越大，计算越慢；
5. `mesh.generate(3)` 生成三维体网格；`write(...)` 导出文件；`finalize()` 关机。

### 2.9 小练习（必做）

1. 不看教材，默写出 Gmsh 程序的六步骨架（只写函数名）；
2. 创建两个立方体：一个边长 1 m，一个边长 0.5 m，放在不同的位置（提示：`addBox` 的第一个参数就是位置）；
3. 用一句话向室友解释：什么是网格？为什么 FEM 需要网格？

---

## 第 3 章 几何实体与基本几何体

### 3.1 本章目标

1. 理解 Gmsh 的「点 → 线 → 面 → 体」四级实体体系；
2. 学会创建四种基本几何体：球、方块、圆柱、圆锥台；
3. 亲手创建万神殿穹顶的 22.03 m 内球。

### 3.2 先建立直觉：Gmsh 里的世界只有四种东西

Gmsh 的几何世界，从上到下只有四级实体（entity）：

| 维度 | 实体 | 长什么样 | 用途 |
| --- | --- | --- | --- |
| 0 | 点（Point） | 一个坐标位置 | 控制点、角点 |
| 1 | 线（Curve） | 一条线/弧 | 面的边界 |
| 2 | 面（Surface） | 一块平面或曲面 | 体的表面、物理组标记 |
| 3 | 体（Volume） | 一个封闭的三维区域 | 实际分析的对象 |

**类比**：就像搭积木的四个层级——先有点（积木的角），连线（积木的棱），围面（积木的面），最后围成体（一块积木）。

**为什么你要先懂这个？** 因为后面的布尔运算、物理组标记，全都靠「维度 + 编号」来指认实体。比如 `(3, 5)` 的意思就是「3 维（体），编号 5」。

每个实体创建后都会返回一个整数 **tag**（编号）。记住两件事：

- tag 是 Gmsh 内部发的身份证号，**不要自己猜**，永远用变量保存返回值；
- 布尔运算之后 tag 会变，后面第 5 章专门讲。

### 3.3 第一个球：万神殿的 22.03 m 内球

#### 3.3.1 完整代码

新建 `geometry/demo_sphere.py`：

```python
"""
创建万神殿穹顶内球：半径 22.03 m（Aliberti 2017）
"""
import gmsh

gmsh.initialize()
gmsh.model.add("sphere_demo")

# addSphere(球心 x, 球心 y, 球心 z, 半径 r)
sphere = gmsh.model.occ.addSphere(0, 0, 0, 22.03)
print("球体 tag =", sphere)

gmsh.model.occ.synchronize()

# 网格先设粗一点（演示用），后面章节讲网格
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 2.0)
gmsh.model.mesh.generate(3)

gmsh.write("output/meshes/sphere_demo.msh")
print("已导出: output/meshes/sphere_demo.msh")

gmsh.finalize()
```

#### 3.3.2 逐行拆解

| 代码 | 白话 |
| --- | --- |
| `addSphere(0, 0, 0, 22.03)` | 球心在原点，半径 22.03 米 |
| `sphere = ...` | 把返回的 tag 存进变量，后面要用 |
| `synchronize()` | 提交几何操作（第 2 章强调过，每次都要） |

**运行**：

```bash
conda activate pantheon-fem
cd /mnt/c/Users/tan83/Desktop/codex/pantheon-3d-fem
python geometry/demo_sphere.py
```

**预期输出**（开头可能有一堆 `Info` 日志，正常）：

```text
球体 tag = 1
已导出: output/meshes/sphere_demo.msh
```

> **为什么用 22.03？** 这是从 Aliberti (2017) 论文核对来的穹顶内半径。这个数以后会频繁出现在代码里，但**绝不直接写死在代码中**——第 9 章会教你从 `config/params.py` 导入。

### 3.4 方块、圆柱、圆锥台：三个标准坯料

#### 3.4.1 方块 addBox（藻井用）

```python
# addBox(左下角 x, 左下角 y, 左下角 z, 边长 dx, dy, dz)
coffer = gmsh.model.occ.addBox(0, 0, 0, 3.88, 0.23, 4.08)
```

这个方块：左下角在原点，沿 x 长 3.88 m、沿 y 深 0.23 m、沿 z 高 4.08 m——这就是第一层藻井的近似尺寸（后面第 11 章详讲）。

**要点**：`addBox` 的三个长度分别是 x、y、z 方向，**不是**「长宽高随便填」，顺序错了形状就错。

#### 3.4.2 圆柱 addCylinder（鼓座/Oculus 用）

```python
# addCylinder(底面圆心 x, y, z, 轴向 dx, dy, dz, 半径 r)
drum = gmsh.model.occ.addCylinder(0, 0, -20,   # 底面圆心
                                   0, 0, 30,    # 沿 z 轴向上 30 m
                                   22.03)       # 半径 22.03 m
```

这个圆柱从 z = -20 延伸到 z = -20 + 30 = 10，半径 22.03 m。

**三个信息缺一不可**：底面圆心（放哪）、轴向向量（朝哪长、多长）、半径（多粗）。

#### 3.4.3 圆锥台 addCone（变厚度替代方案）

```python
# addCone(底面圆心 x, y, z, 轴向 dx, dy, dz, 底半径 r_bottom, 顶半径 r_top)
cone = gmsh.model.occ.addCone(0, 0, 0,    # 底面圆心
                              0, 0, 10,   # 沿 z 轴向上 10 m
                              r_bottom,   # 底面半径
                              r_top)      # 顶面半径
```

- 顶半径 = 0：尖锥；
- 顶半径 > 0：圆锥台（像水桶）；
- 顶半径 = 底半径：其实就是圆柱（addCone 的通用形式）。

### 3.5 一个程序创建四种几何体（综合示例）

把四种坯料放进同一个模型，看看它们各自的 tag：

```python
import gmsh

gmsh.initialize()
gmsh.model.add("primitives_demo")

sphere = gmsh.model.occ.addSphere(0, 0, 0, 10)
box    = gmsh.model.occ.addBox(15, 0, 0, 3, 3, 3)
cyl    = gmsh.model.occ.addCylinder(0, 15, 0, 0, 0, 8, 2)
cone   = gmsh.model.occ.addCone(15, 15, 0, 0, 0, 6, 3, 1)

gmsh.model.occ.synchronize()

print("球 tag:", sphere)
print("方块 tag:", box)
print("圆柱 tag:", cyl)
print("圆锥台 tag:", cone)

gmsh.finalize()
```

**预期输出**：

```text
球 tag: 1
方块 tag: 2
圆柱 tag: 3
圆锥台 tag: 4
```

注意：这个脚本没有划分网格、没有导出，只有几何——它演示的是「**加坯料 + 拿 tag**」这个最基础动作。

### 3.6 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `addSphere` 报错参数不对 | 参数个数或顺序错 | 检查是不是 `(x, y, z, r)` 四个数 |
| 圆柱方向不对 | 轴向向量写错 | 想沿 z 轴就写 `0,0,长度` |
| 打印 tag 是 0 或很大 | 可能是同步后 tag 变化 | 在 `synchronize()` 之后重新获取实体（第 7 章教） |
| 忘了同步就导出 | 文件里是空的 | 在 add 之后补 `synchronize()` |

### 3.7 本章小结

1. Gmsh 只有四级实体：点(0) → 线(1) → 面(2) → 体(3)；
2. `addSphere / addBox / addCylinder / addCone` 是四个标准坯料函数；
3. 每个函数都返回 tag，**永远用变量保存**，不要自己猜编号；
4. 圆柱 = 底面圆心 + 轴向 + 半径；圆锥台多一个顶半径；
5. 几何操作后必须 `synchronize()`。

### 3.8 小练习

1. 创建一个半径 5 的球、一个 `(10, 0, 0)` 到 `(13, 3, 3)` 的方块（提示：用 addBox 的六个参数算一下）；
2. 创建一个「水桶」：底面半径 4、顶面半径 2、高 10；
3. 回答：`(2, 7)` 在 Gmsh 里表示什么？（答案见第 3.2 节）

---

## 第 4 章 布尔运算入门：焊、交、切

### 4.1 本章目标

1. 理解三种布尔运算：并集（fuse）、交集（intersect）、差集（cut）；
2. 会用「两个小方块」的玩具例子验证每一种运算；
3. 理解布尔运算的返回值和参数 removeObject / removeTool。

### 4.2 先建立直觉：集合论的三板斧

布尔运算的名字听着吓人，其实就是**集合论**的三个操作。你初中就学过：

| 运算 | 函数 | 集合论说法 | 白话 | 比喻 |
| --- | --- | --- | --- | --- |
| 并集 | `fuse` | A ∪ B | 两块料焊成一块 | 两块橡皮泥捏一起 |
| 交集 | `intersect` | A ∩ B | 只留重叠部分 | 只保留两个圈压住的部分 |
| 差集 | `cut` | A − B | 从 A 里挖掉 B | 用模具 B 从 A 上切一刀 |

**为什么 Gmsh 需要布尔运算？** 因为现实世界的复杂形状（球壳、藻井、鼓座）几乎都是基本几何体「加减拼」出来的。

### 4.3 玩具例子：两个小方块

设两个方块：

- 方块 A：`addBox(0, 0, 0, 2, 1, 1)`，从原点伸出，长 2；
- 方块 B：`addBox(1, 0, 0, 2, 1, 1)`，从 x=1 伸出，长 2。

它们在 x 方向**重叠 1 个单位**（x 从 1 到 2 是公共部分）。

先创建模型并获取 tag：

```python
import gmsh

gmsh.initialize()
gmsh.model.add("bool_demo")

A = gmsh.model.occ.addBox(0, 0, 0, 2, 1, 1)   # 方块 A
B = gmsh.model.occ.addBox(1, 0, 0, 2, 1, 1)   # 方块 B
gmsh.model.occ.synchronize()
```

### 4.4 并集 fuse（焊）

```python
# 把 A 和 B 焊成一个整体
result = gmsh.model.occ.fuse([(3, A)], [(3, B)])
gmsh.model.occ.synchronize()

print("并集结果:", result[0])
```

**预期输出**（tag 数字可能不同）：

```text
并集结果: [(3, 1)]
```

原来两个方块，焊完后**只剩一个体**——重叠部分不再重复计数，整个形状像一个「L 形」（其实是一条长 3 的长方体）。

### 4.5 交集 intersect（只留重叠）

重新运行（注释掉 fuse，改用 intersect）：

```python
result = gmsh.model.occ.intersect([(3, A)], [(3, B)])
gmsh.model.occ.synchronize()

print("交集结果:", result[0])
```

**预期输出**：

```text
交集结果: [(3, 1)]
```

这次剩下的体是 A、B 的公共部分：边长 1 的小方块（x 从 1 到 2）。

### 4.6 差集 cut（切）—— 最常用！

```python
result = gmsh.model.occ.cut([(3, A)], [(3, B)])
gmsh.model.occ.synchronize()

print("差集结果:", result[0])
```

**预期输出**：

```text
差集结果: [(3, 1)]
```

这次剩下的是「A 中不属于 B 的部分」：x 从 0 到 1 的一段，即**切掉 B 之后剩下的 A**。

### 4.7 关键：搞清楚返回值的结构

上面三个函数（`fuse` / `intersect` / `cut`）的返回值结构完全一样，都是：

```python
result = (outDimTags, outDimTagsMap)
```

我们只需要 **`result[0]`**，它是一个列表，每个元素是 `(dim, tag)`：

```python
for dim, tag in result[0]:
    print(dim, tag)   # 例如 3 1
```

> **为什么是这个结构？** 因为一次运算可能产出多个实体（比如切出两块），所以 Gmsh 用列表装下所有结果。`result[1]`（映射表）是进阶信息，本书用不到。

### 4.8 removeObject / removeTool：切完之后谁留下？

这是全书最容易懵的一对参数，我们用一张表讲透：

```python
gmsh.model.occ.cut(
    [(3, A)],         # 第一个参数 = object（主体）
    [(3, B)],         # 第二个参数 = tool（工具）
    removeObject=True,  # 是否删除主体 A 的原体
    removeTool=True,    # 是否删除工具 B 的原体
)
```

| 参数 | 管谁 | True 的意思 | False 的意思 |
| --- | --- | --- | --- |
| `removeObject` | 主体（第一个参数，如 A） | 运算后把 A 原体删掉 | A 原体保留 |
| `removeTool` | 工具（第二个参数，如 B） | 运算后把 B 原体删掉 | B 原体保留 |

**关键理解**：布尔运算会**新造一个结果体**，结果体永远保留。这两个参数只管「原来的 A、B 要不要留」。

**为什么通常两个都设 True？** 因为我们要的就是结果，原体留着会造成重复、干扰后续操作。

> ⚠️ 旧版文档4 在此处有一句笔误：「removeObject=False 保留内球，removeTool=True 删除内球」——这句话自相矛盾，**请以本表为准**。

### 4.9 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 切完结果为空 | 两个体根本没相交 | 先 `getBoundingBox` 检查重叠（第 7 章教） |
| 结果里有多个体 | 切碎成多块，正常 | 遍历 `result[0]` 逐个处理 |
| 想用旧 tag 却报错 | 布尔后 tag 已变 | 永远从 `result[0]` 里重新取 |
| 忘记 remove 参数导致多余实体 | 默认其实也是 True | 显式写出参数，养成习惯 |

### 4.10 本章小结

1. 并集 `fuse`（A∪B）、交集 `intersect`（A∩B）、差集 `cut`（A−B）；
2. 三者返回结构相同：`result[0]` 是结果实体列表，元素是 `(dim, tag)`；
3. `removeObject` 管主体原体，`removeTool` 管工具原体，结果体永远保留；
4. 布尔运算后 tag 会变，必须从结果里重新获取；
5. **球壳 = 外球 cut 内球**，第 5 章实战。

### 4.11 小练习

1. 用两个重叠的方块，分别跑 fuse / intersect / cut，打印 `result[0]`，观察三个结果各是什么形状；
2. 把 cut 的 `removeObject=False, removeTool=False` 试一次，数一数模型里现在有几个体（提示：用 `gmsh.model.getEntities(dim=3)`）；
3. 用自己的话回答：为什么球壳要用 cut 而不是 fuse？

---

## 第 5 章 球壳 = 外球 − 内球（C0 核心）

### 5.1 本章目标

1. 亲手创建「两同心球夹壳」——C0 算例的几何本体；
2. 掌握布尔差集后的「重新找 tag」套路；
3. 理解本项目 C0 的参数：内半径 22.03 m、厚度从 params.py 读取。

### 5.2 先建立直觉：球壳是什么

球壳 = 空心球，像篮球的外皮、台球的壳。数学上就是：

```text
球壳 = 外球 − 内球（两个球同心，内球半径 = 外球半径 − 厚度）
```

万神殿穹顶近似于一个内半径 22.03 m、厚度约 5.90 m 的球壳（拱脚处最厚，第 9 章讲变厚度）。

### 5.3 C0 的完整脚本（第 1 版：参数写死在代码里）

> 正式代码应从 `config/params.py` 读参数（第 9 章教）。这里先用两个常量演示原理，**避免第一次就引入 import 复杂度**。

新建 `geometry/c0_spherical_shell.py`（今天你本来就要写它！）：

```python
"""
C0 球壳几何脚本（第 1 版：先跑通，再参数化）

目标：两同心球夹壳
  - 内球半径 R_INNER = 22.03 m
  - 厚度 T = 5.90 m
  - 外球半径 = R_INNER + T
"""
import gmsh

# ============ 参数区（第 9 章会换成从 params.py 导入） ============
R_INNER = 22.03   # 内球半径 [m]（Aliberti 2017）
T_SHELL = 5.90    # 壳厚 [m]（Mark & Hutchinson 1986）
R_OUTER = R_INNER + T_SHELL   # 外球半径

# ============ 主流程 ============
gmsh.initialize()
gmsh.model.add("c0_shell")

# 1. 创建外球和内球（同心，都在原点）
outer_sphere = gmsh.model.occ.addSphere(0, 0, 0, R_OUTER)
inner_sphere = gmsh.model.occ.addSphere(0, 0, 0, R_INNER)
print("外球 tag:", outer_sphere, " 内球 tag:", inner_sphere)

gmsh.model.occ.synchronize()

# 2. 外球 − 内球 = 球壳
result = gmsh.model.occ.cut(
    [(3, outer_sphere)],   # 主体：外球
    [(3, inner_sphere)],   # 工具：内球
    removeObject=True,     # 删除外球原体
    removeTool=True,       # 删除内球原体
)
gmsh.model.occ.synchronize()

# 3. 关键套路：从结果里重新找「体」的 tag
shell_tag = None
for dim, tag in result[0]:
    if dim == 3:           # 3 = 体
        shell_tag = tag
        break

print("球壳体 tag:", shell_tag)

# 4. 撒网（先粗一点，能跑通就行）
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 2.0)
gmsh.model.mesh.generate(3)

# 5. 导出
gmsh.write("output/meshes/c0_shell_v1.msh")
print("已导出: output/meshes/c0_shell_v1.msh")

gmsh.finalize()
```

### 5.4 逐块拆解（四步套路）

**第一步：建两个球**。外球半径 = 内半径 + 厚度，两个球同心，都在原点 `(0,0,0)`。

**第二步：布尔差集**。`cut` 的主体是外球，工具是内球。两个 remove 都设 True：外球、内球的原体都删掉，只留壳。

**第三步：找新 tag（重点！）**。布尔运算后，旧的外球 tag 和内球 tag 都**作废**了。壳是新实体，必须从 `result[0]` 里重新找：

```python
for dim, tag in result[0]:
    if dim == 3:
        shell_tag = tag
        break
```

为什么 `dim == 3`？因为 `result[0]` 里可能有面、有线（切出来的边界），我们只要**体**。

**第四步：撒网导出**。先用 2.0 m 的粗网格验证流程，后面第 6 章再调。

### 5.5 预期输出

```text
外球 tag: 1  内球 tag: 2
球壳体 tag: 1
已导出: output/meshes/c0_shell_v1.msh
```

（注意：球壳体 tag 恰好也是 1，是 Gmsh 内部重新编号的结果，**不要**因为数字巧合就以为可以猜 tag。）

### 5.6 三个必须做的小实验

**实验 A：厚度变薄**

把 `T_SHELL` 改成 `1.0`，重跑。文件大小会变大还是变小？（提示：壳越薄，同样网格尺寸下单元越扁，可能变慢变多。）

**实验 B：看看如果忘了 synchronize**

把第一次 `synchronize()` 注释掉再跑，观察报错信息，然后改回来。

**实验 C：不删除原体**

把 `removeObject=False, removeTool=False`，重跑，然后用下面代码数一数有几个体：

```python
print(gmsh.model.getEntities(dim=3))
```

（会看到 3 个体：外球原体、内球原体、壳。这就是「原体残留」的效果，通常不要这样。）

### 5.7 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 切完 `shell_tag` 还是 None | 忘记遍历 `result[0]` 或判断条件写错 | 检查循环代码 |
| 模型里没有球壳 | 忘记 `synchronize()` | 在 cut 前补同步 |
| 球壳变成两个球 | 参数传反了 | 确认主体是外球、工具是内球 |
| 文件特别大或卡住 | 网格太细或壳太薄 | 先 `CharacteristicLengthMax=2.0` 跑通 |

### 5.8 本章小结

1. 球壳 = 外球 `cut` 内球，两球同心；
2. 外球半径 = 内半径 + 厚度；
3. 布尔后旧 tag 作废，**从 `result[0]` 重新找体 tag**；
4. C0 参数：R_INNER=22.03，T_SHELL=5.90（第 9 章改从 params.py 导入）。

### 5.9 小练习

1. 默写球壳的「四步套路」：建球 → 切 → 找 tag → 撒网导出；
2. 把脚本改造成函数 `create_shell(r_inner, thickness)`，返回 `shell_tag`；
3. 回答：为什么第 3 步不能用 `outer_sphere` 变量直接当壳的 tag？

---

## 第 6 章 网格专题：撒网的艺术

### 6.1 本章目标

1. 掌握网格尺寸的三种控制方法；
2. 理解 1D / 2D / 3D 网格的区别；
3. 学会查询网格信息（节点数、单元数、单元类型）；
4. 知道网格算法选项存在，先不深究。

### 6.2 先建立直觉：网格 = 渔网，尺寸 = 网眼大小

把几何体想象成一条鱼，网格就是罩住它的渔网：

- **网眼大**：网格粗，单元少，算得快，但精度低；
- **网眼小**：网格细，单元多，算得慢，但精度高；
- **好渔夫**：鱼身大处用粗网，鱼嘴、鱼鳍等细节处用细网——这就是「局部加密」。

网格的每个网眼叫**单元（element）**，网眼的每个绳结叫**节点（node）**。在三维 FEM 里，单元通常是**四面体（tetrahedron）**——像金字塔，四个顶点就是四个节点。

### 6.3 网格尺寸控制：三种方法

#### 方法一：全局最大尺寸（最常用）

```python
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 0.5)
```

含义：**任何单元边长不超过 0.5 m**。这是「一刀切」的粗网上限。

#### 方法二：全局最小尺寸（防呆）

```python
gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 0.1)
```

含义：单元边长不小于 0.1 m，防止 Gmsh 在某些尖角处把网格切到无穷细、算不动。

#### 方法三：按曲率自动加密（球壳必备）

```python
gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
```

含义：曲面**弯得越厉害的地方自动加密**。球壳这种大曲率结构非常需要。

> **经验组合**（C0 起步用）：
>
> ```python
> gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 2.0)
> gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
> ```

### 6.4 三种维度的网格：generate(1/2/3)

`gmsh.model.mesh.generate(dim)` 的 dim 决定生成到哪一维：

| dim | 生成什么 | 什么时候用 |
| --- | --- | --- |
| 1 | 只在线上布节点 | 调试、画线 |
| 2 | 在面上生成三角形 | 表面网格、预览 |
| 3 | 在体里生成四面体 | **FEM 最终需要** |

**关键**：`generate(3)` 会自动包含 1D 和 2D 的网格，不用三次都调。

### 6.5 查询网格：节点和单元

撒完网，怎么知道网有多大？用两个查询函数：

```python
# 1. 获取所有节点
node_tags, node_coords, node_params = gmsh.model.mesh.getNodes()
print("节点数:", len(node_tags))

# 2. 获取所有单元
elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements()
n_elements = sum(len(tags) for tags in elem_tags)
print("单元数:", n_elements)

# 3. 单元类型编号 → 名字
for et, tags in zip(elem_types, elem_tags):
    name = gmsh.model.mesh.getElementTypeName(et)
    print(f"单元类型 {et} ({name}): {len(tags)} 个")
```

**预期输出**（以第 5 章球壳粗网格为例，数字不同）：

```text
节点数: 10942
单元数: 45678
单元类型 4 (Tetrahedron 4): 45678 个
```

这里 `单元类型 4` 是 **4 节点一阶四面体**；`11` 是 **10 节点二阶四面体**（第 13 章讲）。

**三个返回值的含义**：

| 函数 | 第 1 个返回值 | 第 2 个 | 第 3 个 |
| --- | --- | --- | --- |
| `getNodes()` | 节点编号列表 | 节点坐标（xyz 展平） | 参数坐标（一般不管） |
| `getElements()` | 单元类型列表 | 每类的单元编号 | 每类单元的节点连接关系 |

### 6.6 网格算法：先知道有旋钮，别急着拧

Gmsh 提供了好几种「切网手法」：

```python
# 二维算法
gmsh.option.setNumber("Mesh.Algorithm", 6)      # 6 = Frontal-Delaunay（默认，质量好）
# gmsh.option.setNumber("Mesh.Algorithm", 5)    # 5 = Delaunay

# 三维算法
gmsh.option.setNumber("Mesh.Algorithm3D", 1)    # 1 = Delaunay（默认）
# gmsh.option.setNumber("Mesh.Algorithm3D", 4)  # 4 = Frontal
# gmsh.option.setNumber("Mesh.Algorithm3D", 7)  # 7 = MMG3D（实验性）
```

**你现在只需要知道**：默认算法（2D: Frontal-Delaunay，3D: Delaunay）质量已经不错，**先别改**。等第 13 章学了网格质量评估，如果发现畸形单元，再回来换算法。

### 6.7 完整示例：球壳 + 网格统计

把第 5 章的脚本升级，加一段网格统计：

```python
import gmsh

R_INNER = 22.03
T_SHELL = 5.90
R_OUTER = R_INNER + T_SHELL

gmsh.initialize()
gmsh.model.add("c0_shell_mesh")

outer = gmsh.model.occ.addSphere(0, 0, 0, R_OUTER)
inner = gmsh.model.occ.addSphere(0, 0, 0, R_INNER)
gmsh.model.occ.synchronize()

result = gmsh.model.occ.cut([(3, outer)], [(3, inner)])
gmsh.model.occ.synchronize()

shell_tag = None
for dim, tag in result[0]:
    if dim == 3:
        shell_tag = tag
        break

# ---- 网格设置 ----
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 2.0)
gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
gmsh.model.mesh.generate(3)

# ---- 网格统计 ----
node_tags, _, _ = gmsh.model.mesh.getNodes()
elem_types, elem_tags, _ = gmsh.model.mesh.getElements()
n_elements = sum(len(t) for t in elem_tags)

print(f"节点数: {len(node_tags)}")
print(f"单元数: {n_elements}")

for et, tags in zip(elem_types, elem_tags):
    print(f"  类型 {et} ({gmsh.model.mesh.getElementTypeName(et)}): {len(tags)}")

gmsh.write("output/meshes/c0_shell_mesh.msh")
gmsh.finalize()
```

### 6.8 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 网格生成极慢 | 尺寸太小或 FromCurvature 过激 | 调大 `CharacteristicLengthMax` |
| 单元数 0 | 忘了 `generate(3)` | 补上 |
| 想数单元却报错 | `elem_tags` 是列表套列表 | 用 `sum(len(t) for t in elem_tags)` |
| 模型里出现三角形网格 | 只 `generate(2)` 了 | 用 `generate(3)` |

### 6.9 本章小结

1. 网格尺寸三件套：Max（上限）、Min（下限）、FromCurvature（按曲率加密）；
2. `generate(3)` 一次搞定 1D+2D+3D；
3. `getNodes()` 数节点，`getElements()` 数单元；
4. 单元类型 4 = 一阶四面体，11 = 二阶四面体；
5. 算法旋钮先认识，默认别动。

### 6.10 小练习

1. 跑通 6.7 的完整示例，记录节点数和单元数；
2. 把 `CharacteristicLengthMax` 从 2.0 改成 1.0，对比节点数和单元数，观察「网格变细，数量大约翻几倍」；
3. 用自己的话解释：为什么 FromCurvature 对球壳特别有用？

---

## 第 7 章 物理组：给面/体贴身份证

### 7.1 本章目标

1. 理解为什么 FEM 必须有物理组；
2. 学会 `addPhysicalGroup` 的用法；
3. 学会用 `getEntities` + `getBoundingBox` 按位置识别面——这是项目实战的核心技能。

### 7.2 先建立直觉：没有身份证，FEniCSx 就「六亲不认」

想象你把球壳网格交给 FEniCSx，并说：「请在这个壳上算位移，底部固定，受自重。」

FEniCSx 会反问三个问题：

1. 哪个面是**底部**？（要固定它）
2. 哪个面是**内表面**、哪个是**外表面**？（后处理要看）
3. 哪个体是**穹顶**？（要赋予材料属性）

如果没有事先标记，FEniCSx 看到的是几百个匿名面，**一个也认不出来**。

物理组（Physical Group）就是解决这个问题的：**把一批面（或体）打包，起个编号、起个名字**，然后 FEniCSx 按编号认领。

### 7.3 addPhysicalGroup 用法

```python
gmsh.model.addPhysicalGroup(
    dim,          # 维度：2 = 面，3 = 体
    tag_list,     # 要打包的实体编号列表，如 [42] 或 [1, 2, 3]
    tag=400,      # 自己约定的物理组编号（身份证号）
    name="dome_base",  # 名字（方便人看）
)
```

示例：

```python
# 给拱脚面（假设它的实体 tag 是 42）贴标签
gmsh.model.addPhysicalGroup(2, [42], tag=400, name="dome_base")

# 给穹顶体贴标签
gmsh.model.addPhysicalGroup(3, [shell_tag], tag=1000, name="dome_body")
```

**注意区分两个 tag**：

| tag 类型 | 谁发的 | 干什么 |
| --- | --- | --- |
| 实体 tag | Gmsh 创建实体时自动发 | 指认某个几何实体 |
| 物理组 tag | **我们自己约定** | 给一组实体起编号，供 FEniCSx 识别 |

### 7.4 本项目的物理组编号约定（务必背下来）

| 物理组 tag | 名字 | 类型 | 含义 | 用途 |
| --- | --- | --- | --- | --- |
| 100 | `oculus_edge` | 2D 面 | Oculus 边缘 | 自由边 |
| 200 | `dome_inner` | 2D 面 | 穹顶内表面 | 可视化 |
| 300 | `dome_outer` | 2D 面 | 穹顶外表面 | 可视化 |
| 400 | `dome_base` | 2D 面 | 拱脚面 | C1 固支 |
| 500 | `dome_interface` | 2D 面 | 穹顶-鼓座交界面 | C2 绑定 |
| 600 | `drum_outer` | 2D 面 | 鼓座外表面 | 可视化 |
| 700 | `drum_bottom` | 2D 面 | 鼓座底面 | 固支 |
| 1000 | `dome_body` | 3D 体 | 穹顶体 | 材料属性 |
| 2000 | `drum_body` | 3D 体 | 鼓座体 | 材料属性 |

> 这个表和文档5 里的 FEniCSx 代码是配套的，编号错一个，求解时就找不到边界。

### 7.5 核心难题：怎么知道哪个实体 tag 是「底面」？

布尔运算之后，实体的 tag 会变，**不能靠猜**。业界标准做法是**按位置识别**：

1. 用 `getEntities(dim=2)` 列出所有面；
2. 用 `getBoundingBox(dim, tag)` 量每个面的位置；
3. 按「在哪、多大」判断它是什么面。

```python
# 获取所有面的 tag
surfaces = gmsh.model.getEntities(dim=2)

for dim, tag in surfaces:
    # 量包围盒：返回 (x_min, y_min, z_min, x_max, y_max, z_max)
    bbox = gmsh.model.occ.getBoundingBox(dim, tag)
    z_min, z_max = bbox[2], bbox[5]
    z_center = (z_min + z_max) / 2

    if abs(z_center + 22.03) < 0.01:     # 在 z = -22.03 附近 → 底面（拱脚）
        base_faces.append(tag)
```

**这段代码的三个要点**：

1. `getBoundingBox` 返回 6 个数：最小/最大的 x、y、z；
2. 判断依据是**位置**而不是 tag 数字；
3. 容差 `< 0.01`：浮点坐标不会恰好相等，留 1 cm 的余量。

### 7.6 完整示例：球壳 + 物理组

给第 5 章的球壳标记三个面（内、外、底面）和一个体：

```python
import gmsh

R_INNER = 22.03
T_SHELL = 5.90
R_OUTER = R_INNER + T_SHELL

gmsh.initialize()
gmsh.model.add("c0_shell_groups")

outer = gmsh.model.occ.addSphere(0, 0, 0, R_OUTER)
inner = gmsh.model.occ.addSphere(0, 0, 0, R_INNER)
gmsh.model.occ.synchronize()

result = gmsh.model.occ.cut([(3, outer)], [(3, inner)])
gmsh.model.occ.synchronize()

shell_tag = None
for dim, tag in result[0]:
    if dim == 3:
        shell_tag = tag
        break

# ---- 按位置识别面 ----
inner_faces, outer_faces, base_faces = [], [], []
for dim, tag in gmsh.model.getEntities(dim=2):
    bbox = gmsh.model.occ.getBoundingBox(dim, tag)
    x_min, y_min, z_min, x_max, y_max, z_max = bbox
    z_center = (z_min + z_max) / 2
    r_center = ((x_min + x_max) / 2) ** 2
    r_center += ((y_min + y_max) / 2) ** 2
    r_center += z_center ** 2
    r_center = r_center ** 0.5

    if abs(z_center + 22.03) < 0.01:          # 拱脚底面
        base_faces.append(tag)
    elif r_center > R_INNER + T_SHELL / 2:    # 离球心远 → 外表面
        outer_faces.append(tag)
    elif r_center < R_INNER + T_SHELL / 2:    # 离球心近 → 内表面
        inner_faces.append(tag)

# ---- 贴标签 ----
gmsh.model.addPhysicalGroup(2, inner_faces, tag=200, name="dome_inner")
gmsh.model.addPhysicalGroup(2, outer_faces, tag=300, name="dome_outer")
gmsh.model.addPhysicalGroup(2, base_faces,  tag=400, name="dome_base")
gmsh.model.addPhysicalGroup(3, [shell_tag], tag=1000, name="dome_body")

print(f"内表面 {len(inner_faces)} 个面, 外表面 {len(outer_faces)} 个面, 底面 {len(base_faces)} 个面")

gmsh.model.mesh.generate(3)
gmsh.write("output/meshes/c0_shell_groups.msh")
gmsh.finalize()
```

### 7.7 判断逻辑怎么想出来的？（思维过程）

「哪个面是底面？」——球壳有两个「横截面」式的面：拱脚底面在 `z = -22.03` 附近，Oculus 顶面（如果有）在 `z ≈ +21.57`。所以按 z 位置判断。

「哪个面是内/外？」——内表面上的点到球心的距离 ≈ 22.03，外表面上的点 ≈ 27.93。所以按**到原点的距离**判断，用两个半径的平均值 `22.03 + 5.90/2 ≈ 24.98` 分界。

**这就是「位置识别法」**：用包围盒算几何量，再和已知参数比。

### 7.8 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| FEniCSx 找不到某个物理组 | 布尔之后才贴的标签，tag 已失效 | **所有布尔完成后再** `addPhysicalGroup` |
| 某个面被漏掉 | 判断条件没覆盖它 | 打印每个面的 bbox 人工核对 |
| 一个面进了两个组 | 判断条件有重叠 | 用 `elif` 保证互斥 |
| 物理组编号冲突 | 编号重复 | 查 7.4 表，编号唯一 |

### 7.9 本章小结

1. 物理组 = 给面/体打包编号，FEniCSx 靠它认边界和材料；
2. `addPhysicalGroup(dim, tags, tag=编号, name=名字)`；
3. 实体 tag 自动发、物理组 tag 自己定，两者别混；
4. 位置识别法：`getEntities` + `getBoundingBox` 按位置找面；
5. 铁律：**所有布尔运算完成后再贴标签**。

### 7.10 小练习

1. 跑通 7.6 示例，打印三个面组的数量；
2. 把底面判断改成「距离球心 z 坐标 +22.03 的面」（即顶面），看会选出什么；
3. 用自己的话解释：为什么「先切完、再贴标签」是铁律？

---

## 第 8 章 导出与预览：让模型「看得见」

### 8.1 本章目标

1. 理解 `.msh` 文件是什么、怎么导出；
2. 掌握两个常用导出选项（版本号、保存所有实体）；
3. 学会三种「看模型」的方式：Gmsh GUI、PyVista、Meshio 读文件。

### 8.2 先建立直觉：.msh 是什么

`.msh` 是 Gmsh 的网格文件格式，**纯文本**，里面记录：

- 节点的坐标；
- 单元由哪些节点组成；
- 物理组编号（FEniCSx 认领用的身份证）。

它是 Gmsh 和 FEniCSx 之间的「交接文件」：Gmsh 写完，FEniCSx 读入。

> 你可以打开 `.msh` 用记事本看一眼，会看到类似 `$Nodes`、`$Elements` 的段落——别慌，不用读懂，工具会解析。

### 8.3 导出：gmsh.write

```python
gmsh.write("output/meshes/dome.msh")
```

一句话：把当前模型写进文件。Gmsh 会根据扩展名自动选择格式。

**两个常用导出选项**：

```python
# 1. 保存所有实体（包括内部面）
gmsh.option.setNumber("Mesh.SaveAll", 1)

# 2. 用 MSH 4.1 格式（FEniCSx 兼容性好，推荐）
gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
```

**经验**：C0 起步就固定用这两行，减少后续 FEniCSx 读网格的兼容性问题。

### 8.4 方式一：Gmsh 自带 GUI 预览

在脚本里加一行（放在 `write` 之后、`finalize` 之前）：

```python
gmsh.fltk.run()
```

运行后 Gmsh 会弹出图形窗口，你可以用鼠标旋转、缩放查看几何和网格。

**注意**：在 WSL2 里需要 WSLg 支持图形界面；如果弹不出窗口，不要卡在这，直接跳到方式二。

### 8.5 方式二：PyVista 预览（推荐）

PyVista 是 Python 的三维可视化库（文档6 会详讲）。用 Meshio 读 `.msh`，再用 PyVista 画：

```python
import pyvista as pv
import meshio

# 1. 读 .msh 文件
msh = meshio.read("output/meshes/c0_shell_v1.msh")

# 2. 取出四面体单元（二阶时是 tetra10）
tetra_cells = None
for cell in msh.cells:
    if cell.type == "tetra":
        tetra_cells = cell.data
        break

if tetra_cells is not None:
    # 3. 转成 PyVista 非结构化网格并画图
    grid = pv.UnstructuredGrid([("tetra", tetra_cells)], msh.points)
    grid.plot(show_edges=True, color="lightblue",
              title="万神殿穹顶网格预览")
```

**逐行解释**：

| 行 | 作用 |
| --- | --- |
| `meshio.read(...)` | 把 .msh 读进内存 |
| `for cell in msh.cells` | 遍历文件里各种单元类型 |
| `cell.type == "tetra"` | 只要四面体（`tetra10` 是二阶四面体） |
| `pv.UnstructuredGrid(...)` | 把节点+单元组装成 PyVista 对象 |
| `grid.plot(...)` | 弹窗画图 |

> **单词小抄**：`show_edges=True` = 显示单元边线；`color="lightblue"` = 浅蓝色；`title=...` = 窗口标题。

### 8.6 方式三：命令行查看（无 GUI 时的兜底）

如果图形窗口都弹不出来，至少可以用 `meshio` 验证文件能读、并打印摘要：

```python
import meshio

msh = meshio.read("output/meshes/c0_shell_v1.msh")
print("节点数:", len(msh.points))
for cell in msh.cells:
    print("单元类型:", cell.type, "数量:", len(cell.data))
```

**能打印出数字 = 文件有效**，预览只是锦上添花。

### 8.7 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 文件是 0 KB | 忘记 `generate(3)` 或没 `synchronize` | 检查主流程顺序 |
| GUI 弹不出来 | WSLg 未启用 | 用 PyVista 或 meshio 兜底 |
| `ImportError: meshio` | 环境缺包 | `pip install meshio pyvista` |
| 只有点没有单元 | `Mesh.SaveAll` 等选项设置时机不对 | 选项放在 `generate` 之前 |

### 8.8 本章小结

1. `.msh` = 节点 + 单元 + 物理组的文本文件，是 Gmsh→FEniCSx 的交接文件；
2. 导出用 `gmsh.write`，C0 固定加 `Mesh.MshFileVersion=4.1` 和 `Mesh.SaveAll=1`；
3. 三种预览：Gmsh GUI（`fltk.run`）、PyVista（推荐）、meshio 摘要（兜底）；
4. **能读出数字 = 文件有效**。

### 8.9 小练习

1. 用第 7 章的球壳脚本导出 `c0_shell_groups.msh`，用 meshio 打印摘要；
2. 用 PyVista 画一次球壳网格，截图保存（`grid.screenshot("preview.png")`）；
3. 用记事本打开 .msh，找到 `$PhysicalNames` 段落，看看物理组名字是不是都写进去了。

---

## 第 9 章 参数化球面与变厚度：从硬编码到参数文件

### 9.1 本章目标

1. 理解球坐标与笛卡尔坐标的换算；
2. 理解「参数化」为什么重要；
3. 学会从 `config/params.py` 导入参数；
4. 理解变厚度球壳的简化建模方案。

### 9.2 为什么要参数化？

第 5 章里，22.03 和 5.90 直接写在脚本里，这叫**硬编码（hardcode）**。

问题：万一论文参数修正了（比如厚度从 5.90 改成 6.10），你要**打开脚本、找到数字、改掉、再祈祷没改错地方**。如果参数出现在 10 个脚本里，就要改 10 次。

参数化 = **所有参数集中到一个文件，脚本只负责「读参数」**。改一处，全项目生效。

万神殿项目已经把参数集中在 `config/params.py`，里面直接定义了模块级常量 `R_INNER`、`T_BASE` 等。C0 需要的两个参数：

```python
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS

R_INNER   # 22.03，穹顶内半径 [m]
T_BASE    # 5.90，拱脚处厚度 [m]
```

> **规则**：脚本里不允许出现 22.03、5.90 这种「魔法数字」，一律从 `params.py` 导入。

#### 9.2.1 路径引导：为什么脚本开头要加三行？（重要！）

直接 `from config.params import ...` 有一个坑：**Python 只会从脚本所在目录找模块**。脚本放在 `geometry/` 下时，它找不到项目根目录的 `config/` 包，运行会报：

```text
ModuleNotFoundError: No module named 'config'
```

解决办法（文档2 的规范做法）：在脚本开头把**项目根目录**加进模块搜索路径：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS
```

**逐行解释**：

| 行 | 干什么 |
| --- | --- |
| `Path(__file__).resolve()` | 当前脚本的绝对路径 |
| `.parent.parent` | 上两级 = 项目根目录（geometry/ → 项目根） |
| `sys.path.insert(0, ...)` | 把项目根目录加入模块搜索路径的最前面 |

> 以后凡是写 `from config.params import ...`，脚本开头**必须带这三行**。本书所有示例默认遵守。

### 9.3 球坐标：描述球面上的一点

地球仪上定位一个城市，需要「纬度、经度」。球面上定位一个点也一样，需要两个角度：

| 名字 | 符号 | 中文 | 从哪量 |
| --- | --- | --- | --- |
| 子午角 | φ（phi） | 从球顶（Z 轴）往下量 | 0° = 正上方，90° = 赤道 |
| 环向角 | θ（theta） | 在水平面里转的角度 | 从 X 轴逆时针 |

再加上半径 r，一个球面上的点就由 `(r, φ, θ)` 确定——这就是**球坐标**。

**换算到笛卡尔坐标**（本书的核心公式）：

```text
x = r · sin(φ) · cos(θ)
y = r · sin(φ) · sin(θ)
z = r · cos(φ)
```

用 Python 写：

```python
import numpy as np

def spherical_to_cartesian(r, phi, theta):
    """球坐标 → 笛卡尔坐标"""
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)
    return x, y, z
```

**验证**：φ = 90°（赤道），θ = 0° → `(r, 0, 0)`，对！φ = 0°（球顶）→ `(0, 0, r)`，对！

### 9.4 弧度 vs 角度：程序员最容易翻的车

Python 的 `np.sin`、`np.cos` 用的都是**弧度**，不是度。

| 单位 | 一圈 | 直角 | 关系 |
| --- | --- | --- | --- |
| 度（degree） | 360° | 90° | 常见 |
| 弧度（radian） | 2π ≈ 6.283 | π/2 ≈ 1.571 | Python 默认 |

换算：

```python
import numpy as np

角度转弧度 = np.radians(90)     # ≈ 1.5708
弧度转角度 = np.degrees(np.pi/2)  # 90.0
```

**自查问题**：`np.sin(90)` 是多少？——答案是 0.894，不是 1！因为 90 被当成 90 弧度。这是新手最常见的 bug。

### 9.5 万神殿的 Oculus：一个 arcsin 例子

穹顶顶部有个直径 8.95 m 的圆洞（Oculus）。想知道 Oculus 边缘在球面上对应哪个子午角 φ，用**反正弦**：

```python
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS

# Oculus 半径 = 直径/2；弦长对应 2·R_INNER·sin(φ)
phi_oculus = np.arcsin(D_OCULUS / (2 * R_INNER))
```

代入数值：`arcsin(8.95 / 44.06) = arcsin(0.2031) ≈ 0.2045 弧度 ≈ 11.7°`

**白话**：从球顶往下量 11.7°，就是 Oculus 洞的边缘。

再算 Oculus 边缘的 z 坐标：

```python
z_oculus = R_INNER * np.cos(phi_oculus)   # ≈ 21.57 m
```

这个 21.57 m 在切割 Oculus 开口时（第 11 章）直接有用。

### 9.6 变厚度球壳：厚薄不一样的壳

真实的万神殿穹顶**不是等厚的**：

- 顶部（Oculus 附近）：厚约 1.50 m；
- 底部（拱脚）：厚约 5.90 m；
- 中间逐渐变化——这叫**变厚度**。

严格做法：外表面不再是球面，而是随 φ 变化的曲面（NURBS，进阶内容）。

**C0 的简化方案**（先跑通，后精修）：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS

# 平均厚度
T_AVG = (T_OCULUS + T_BASE) / 2     # (1.50 + 5.90)/2 = 3.70 m

# 用平均厚度做一个等厚球壳
R_OUTER_APPROX = R_INNER + T_AVG       # 22.03 + 3.70 = 25.73 m

outer = gmsh.model.occ.addSphere(0, 0, 0, R_OUTER_APPROX)
inner = gmsh.model.occ.addSphere(0, 0, 0, R_INNER)
gmsh.model.occ.cut([(3, outer)], [(3, inner)])
```

**代价**：顶部实际偏厚（近似 3.70 vs 真实 1.50），底部实际偏薄（3.70 vs 5.90），误差约 ±2 m。

**你要知道**：C0 用这个近似完全够——它是「跑通流程」的算例，不是最终精度模型。注释里写明「简化：平均厚度近似」即可。

### 9.7 C0 参数化脚本（第 2 版）

把第 5 章的硬编码升级为参数导入：

```python
"""
C0 球壳几何脚本 v2：参数从 config/params.py 导入
"""
import gmsh
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS

gmsh.initialize()
gmsh.model.add("c0_shell_v2")

T_AVG = (T_OCULUS + T_BASE) / 2
R_OUTER = R_INNER + T_AVG

outer = gmsh.model.occ.addSphere(0, 0, 0, R_OUTER)
inner = gmsh.model.occ.addSphere(0, 0, 0, R_INNER)
gmsh.model.occ.synchronize()

result = gmsh.model.occ.cut([(3, outer)], [(3, inner)])
gmsh.model.occ.synchronize()

shell_tag = None
for dim, tag in result[0]:
    if dim == 3:
        shell_tag = tag
        break

gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 2.0)
gmsh.model.mesh.generate(3)
gmsh.write("output/meshes/c0_shell_v2.msh")

print(f"球壳完成: R_INNER={R_INNER}, T_AVG={T_AVG:.2f}, tag={shell_tag}")
gmsh.finalize()
```

### 9.8 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `ModuleNotFoundError: config` | 运行目录不对 | 必须在项目根目录运行 |
| `np.sin` 结果不对 | 角度/弧度混用 | 全部用弧度，打印自查 |
| 找不到 `T_OCULUS` | 参数名记错 | 打开 `config/params.py` 核对 |
| 数值和文档对不上 | 读的旧参数 | `git pull` 或检查本地改动 |

### 9.9 本章小结

1. 参数化 = 参数集中到 `params.py`，脚本只读不写死；
2. 球坐标 `(r, φ, θ)` → 笛卡尔：`x = r sinφ cosθ` 等三式；
3. Python 三角函数的单位是**弧度**，`np.degrees/np.radians` 互换；
4. Oculus 子午角 = `arcsin(D/(2R))` ≈ 11.7°；
5. C0 变厚度用平均厚度近似（±2 m 误差，可接受），注释注明即可。

### 9.10 小练习

1. 手工算：φ = 45°，θ = 45°，r = 22.03 的 x、y、z（用计算器或 Python 验证）；
2. 在 `params.py` 里找到 `T_OCULUS` 和 `T_BASE`，说出它们的值和含义；
3. 把 v2 脚本跑通，确认打印的 `T_AVG = 3.70`。

---

## 第 10 章 C0 实战：从零写球壳脚本

### 10.1 本章目标

1. 独立完成 `geometry/c0_spherical_shell.py`——**你亲手写**；
2. 脚本要求：参数从 `params.py` 导入、两同心球夹壳、能生成网格和导出；
3. 掌握一个工程脚本该有的「骨架」：参数区、函数封装、主流程、自测。

### 10.2 任务描述（验收标准）

**任务**：编写 `geometry/c0_spherical_shell.py`，实现 C0 算例的几何部分。

**验收标准**：

- [ ] 脚本无报错运行；
- [ ] 生成球壳体（不是两个球）；
- [ ] 参数全部来自 `config/params.py`（无硬编码魔法数字）；
- [ ] 导出 `output/meshes/c0_shell.msh`；
- [ ] 你能向 AI 助手解释每一行代码在干什么。

### 10.3 脚手架（AI 助手提供骨架，你填肉）

```python
"""
C0 球壳几何脚本

功能：生成两同心球夹壳（简化等厚近似），划分网格并导出。
运行：在项目根目录执行  python geometry/c0_spherical_shell.py
"""
import gmsh
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS


def build_shell():
    """创建球壳几何，返回壳体的实体 tag"""
    # TODO 1: 计算平均厚度和外球半径
    # TODO 2: 创建外球和内球（球心在原点）
    # TODO 3: 同步 + 布尔差集（外球 - 内球）
    # TODO 4: 从 result[0] 中找到体的 tag 并返回
    pass


def set_mesh_and_export(shell_tag):
    """设置网格参数、撒网、导出"""
    # TODO 5: 设置网格尺寸（Max=2.0，FromCurvature=1）
    # TODO 6: 生成三维网格
    # TODO 7: 导出 output/meshes/c0_shell.msh
    pass


def main():
    gmsh.initialize()
    gmsh.model.add("c0_shell")

    shell_tag = build_shell()
    assert shell_tag is not None, "球壳 tag 不能为空，检查布尔运算"

    set_mesh_and_export(shell_tag)
    gmsh.finalize()
    print("✅ C0 球壳几何完成")


if __name__ == "__main__":
    main()
```

### 10.4 分步引导（每步先想后写）

**TODO 1：算平均厚度和外球半径**

想：params.py 里有 `T_OCULUS`（顶部厚 1.50）和 `T_BASE`（拱脚厚 5.90）。平均厚度取两者均值，外球半径 = 内半径 + 平均厚度。

写：

```python
t_avg = (T_OCULUS + T_BASE) / 2
r_outer = R_INNER + t_avg
```

**TODO 2：创建两个球**

想：球心都在原点，半径分别 `r_outer` 和 `R_INNER`。

写：

```python
outer = gmsh.model.occ.addSphere(0, 0, 0, r_outer)
inner = gmsh.model.occ.addSphere(0, 0, 0, R_INNER)
```

**TODO 3：同步 + 差集**

想：布尔之前必须同步；主体是外球，工具是内球；两个 remove 都设 True。

写：

```python
gmsh.model.occ.synchronize()
result = gmsh.model.occ.cut([(3, outer)], [(3, inner)],
                            removeObject=True, removeTool=True)
gmsh.model.occ.synchronize()
```

**TODO 4：找壳的 tag**

想：遍历 `result[0]`，只要 `dim == 3` 的实体。

写：

```python
for dim, tag in result[0]:
    if dim == 3:
        return tag
return None
```

**TODO 5–7：网格与导出**

想：网格选项放在 `generate` 之前；导出路径是相对项目根目录的。

写：

```python
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 2.0)
gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
gmsh.model.mesh.generate(3)
gmsh.write("output/meshes/c0_shell.msh")
```

### 10.5 你自己验证（先自查再求助）

运行：

```bash
conda activate pantheon-fem
cd /mnt/c/Users/tan83/Desktop/codex/pantheon-3d-fem
mkdir -p output/meshes
python geometry/c0_spherical_shell.py
```

**通过标准**：

```text
✅ C0 球壳几何完成
```

然后验证文件：

```bash
ls -lh output/meshes/c0_shell.msh
```

再用 meshio 确认里面有体单元（参考第 8.6 节）。

### 10.6 如果报错，按这个顺序自查

1. `ModuleNotFoundError: config` → 在项目根目录运行，别在别的目录；
2. `tag not found` → 检查 `synchronize()` 是否齐全；
3. `shell_tag is None` → 检查 result[0] 遍历逻辑；
4. 其他 → 把完整报错贴给 AI 助手，陪你逐行看。

### 10.7 本章小结

1. 工程脚本三件套：**参数区（导入）、函数封装、主流程 + 自测**；
2. 每个函数只做一件事：`build_shell` 建几何、`set_mesh_and_export` 撒网导出；
3. `if __name__ == "__main__"` 让脚本既能单独跑、也能被 import；
4. 验收标准：无报错 + 球壳体 + 参数化 + 能导出。

### 10.8 小练习（做完才算 C0 过关）

1. 向 AI 助手口头解释：为什么 `build_shell` 要返回 `shell_tag`？直接在里面导出行不行？
2. 把网格尺寸改成 1.0，重跑，记录节点数变化；
3. 在脚本里加一行注释，注明「简化：平均厚度近似，误差约 ±2m」。

---

## 第 11 章 Oculus 开口与藻井：走向真正的万神殿

### 11.1 本章目标

1. 学会用圆柱切出 Oculus 圆洞；
2. 理解藻井（coffer）是什么、为什么用方块近似；
3. 学会「旋转 + 平移」把方块摆到球面上——位置计算的完整思路。

> 本章是支线（后续算例用），C0 不需要。你可以通读一遍，用到再精读。

### 11.2 Oculus 开口：用圆柱「切掉」球顶

穹顶顶部有个直径 8.95 m 的圆洞。方法很朴素：**放一个比洞大的圆柱，从球壳顶穿过去，然后 cut**。

```python
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS

# 1. 算 Oculus 边缘的子午角和 z 坐标（第 9 章学过）
phi_oculus = np.arcsin(D_OCULUS / (2 * R_INNER))
z_oculus = R_INNER * np.cos(phi_oculus)     # ≈ 21.57 m

# 2. 放一个圆柱：底面在洞口下方 1 m，向上伸 30 m，半径留 2 m 余量
r_cut = D_OCULUS / 2 + 2.0                  # 6.475 m
cut_cyl = gmsh.model.occ.addCylinder(
    0, 0, z_oculus - 1,
    0, 0, 30,
    r_cut,
)

gmsh.model.occ.synchronize()

# 3. 球壳 − 圆柱 = 带洞的穹顶
result = gmsh.model.occ.cut(
    [(3, dome_shell_tag)],
    [(3, cut_cyl)],
    removeObject=True,
    removeTool=True,
)
gmsh.model.occ.synchronize()
```

**为什么圆柱要「比洞口大」**？半径 +2 m、底面下移 1 m、向上 30 m——保证圆柱**完全穿透**球壳，切出来的洞边缘才干净。如果圆柱刚好卡在洞口大小，浮点误差会导致切不干净。

### 11.3 藻井：内表面上的 140 个凹槽

万神殿穹顶内表面有 5 层、每层 28 个、共 **140 个方形凹槽**（藻井）。真实藻井是带斜度的倒梯形，但 V2.0 初始版本用**长方体近似**。

```python
# 一个藻井的近似：底宽 3.88、深度 0.23、高度 4.08
coffer = gmsh.model.occ.addBox(0, 0, 0, 3.88, 0.23, 4.08)
```

**难点**：藻井不是朝上的，而是**嵌在球面内表面**上的——每个藻井的方向都不一样。所以不能直接 addBox，要：

1. 在原点建一个标准方块；
2. **旋转**到球面方向；
3. **平移**到内表面位置。

### 11.4 旋转 + 平移：把方块摆到球面上

先算藻井中心在球面上的位置（第 9 章球坐标公式的实战应用）：

```python
# 藻井中心位置（第 9 章的 spherical_to_cartesian）
x_c, y_c, z_c = spherical_to_cartesian(R_INNER, phi_center, theta_center)
```

然后把原点处的方块转过去、挪过去：

```python
# 1. 在原点建方块（绕 z 轴旋转前，方块方向是标准的）
box = gmsh.model.occ.addBox(-w_avg/2, -h/2, -depth, w_avg, h, depth)

# 2. 旋转：绕 z 轴转 theta_center 度
gmsh.model.occ.rotate(
    [(3, box)],
    0, 0, 0,          # 旋转中心：原点
    0, 0, 1,          # 旋转轴：z 轴
    np.degrees(theta_center),   # ⚠️ rotate 用「度」！
)

# 3. 平移：挪到藻井中心位置
gmsh.model.occ.translate(
    [(3, box)],
    x_c, y_c, z_c,
)
```

**两个最容易错的点**：

1. `rotate` 的角度单位是**度**，而 `np.cos(theta_center)` 用的是**弧度**——代码里 `np.degrees(...)` 就是干这个的；
2. 旋转中心、旋转轴、平移距离，三个参数都是**相对当前状态**计算的，顺序错了形状就歪。

### 11.5 批量挖除 140 个藻井

```python
def cut_all_coffers(dome_tag):
    """从穹顶挖除全部 5×28 个藻井"""
    all_coffers = []
    for level in range(5):
        for sector in range(28):
            tag = create_coffer_cutout(level, sector)
            all_coffers.append((3, tag))

    gmsh.model.occ.synchronize()

    # 一次 cut 全部！比逐个 cut 高效得多
    result = gmsh.model.occ.cut(
        [(3, dome_tag)],
        all_coffers,
        removeObject=True,
        removeTool=True,
    )
    gmsh.model.occ.synchronize()
    return result[0]
```

**为什么能一次切 140 个**？`cut` 的第二个参数是**工具列表**，Gmsh 会一次性做完所有差集——这是「列表参数」的威力。

### 11.6 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| Oculus 洞没切穿 | 圆柱不够长/不够粗 | 加余量（+2 m、30 m 高） |
| 藻井方向歪 | rotate 角度单位写错 | 检查是否 `np.degrees` |
| 藻井跑到球外面 | translate 坐标算错 | 打印 `(x_c, y_c, z_c)` 核对 |
| 切完模型炸了 | 藻井方块没完全嵌入壳内 | 检查 depth 方向和位置 |
| 计算很慢 | 140 个逐个 cut | 合并成一个 cut 列表 |

### 11.7 本章小结

1. Oculus = 圆柱穿透 + cut，圆柱必须留余量；
2. 藻井 = 方块「旋转 + 平移」到球面内表面；
3. rotate 用度、np 三角函数用弧度，**时刻警惕单位**；
4. 批量挖除 = 一个 cut + 工具列表，别逐个切。

### 11.8 小练习

1. 修改 Oculus 切割的余量参数，看看半径 +0.1 m 会发生什么（提示：可能切不干净）；
2. 解释：为什么 `rotate` 要在 `translate` **之前**？（提示：旋转中心）
3. 数一数：5 层 × 28 扇区 = 多少藻井？

---

## 第 12 章 鼓座与几何装配：fragment 的「拼而不焊」

### 12.1 本章目标

1. 学会用「外圆柱 − 内圆柱」创建环形墙体（鼓座）；
2. 理解 `fuse` 与 `fragment` 的本质区别；
3. 理解「conformal mesh」（交界面上节点共享）为什么重要。

> 本章是 C2 算例的前置知识，C0 不需要。

### 12.2 鼓座：一个巨大的环形墙

穹顶下面有一个环形墙体（鼓座），像一个大甜甜圈立在地上。建模方法：**两个圆柱做差集**。

```python
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS

# 外圆柱：大半径、全高
outer_cyl = gmsh.model.occ.addCylinder(
    0, 0, drum_z_bottom,
    0, 0, drum_height,
    drum_outer_r,          # 外半径
)

# 内圆柱：小半径、略微加高（保证切穿）
inner_cyl = gmsh.model.occ.addCylinder(
    0, 0, drum_z_bottom - 1,
    0, 0, drum_height + 2,
    drum_inner_r,          # 内半径
)

gmsh.model.occ.synchronize()

# 外柱 − 内柱 = 环形墙体
result = gmsh.model.occ.cut(
    [(3, outer_cyl)],
    [(3, inner_cyl)],
    removeObject=True,
    removeTool=True,
)
gmsh.model.occ.synchronize()

drum_tag = None
for dim, tag in result[0]:
    if dim == 3:
        drum_tag = tag
        break
```

**和球壳完全同构**：球壳 = 外球 − 内球，鼓座 = 外柱 − 内柱。学会了第 5 章，这里就是换汤不换药。

> 内圆柱「底面低 1 m、高度多 2 m」——和 Oculus 圆柱一个道理：**工具要完全穿透主体**，切面才干净。

### 12.3 装配：穹顶 + 鼓座

现在有两个体：穹顶和鼓座。把它们放在一起，有两条路：

#### 路 A：fuse（焊死）——不行！

```python
gmsh.model.occ.fuse([(3, dome_tag)], [(3, drum_tag)])
```

结果：两个体变成一个体，**交界面消失**。FEniCSx 无法区分「穹顶」和「鼓座」，无法分别给材料、无法分析传力。

#### 路 B：fragment（拼装）——正确！

```python
all_volumes = gmsh.model.getEntities(dim=3)
gmsh.model.occ.fragment(
    [(3, tag) for _, tag in all_volumes],
    [],
)
gmsh.model.occ.synchronize()
```

结果：两个体**保持独立**，但交界面被切成完全匹配的两张面，网格划分时**共享同一批节点**。

### 12.4 对比表：fuse vs fragment

| 对比项 | fuse | fragment |
| --- | --- | --- |
| 体的数量 | 1 个 | 保持多个 |
| 交界面 | 消失 | 保留 |
| 交界面网格 | 无 | 共享节点（conformal） |
| 能否分别贴物理组 | 不能 | 能 |
| 适用 | 只要一个整体 | 多部件装配（本项目） |

**conformal（共形/协调）是什么**：交界面两侧的网格节点**一一重合**，像两块乐高严丝合缝。如果节点不重合，FEniCSx 无法直接在交界面上建立连接，需要额外处理——所以 fragment 至关重要。

### 12.5 完整装配骨架

```python
def assemble_full_model():
    """穹顶 + 鼓座装配，返回 (dome_tag, drum_tag)"""
    dome_tag = build_dome_with_coffers_and_oculus()
    drum_tag = build_drum_geometry()

    gmsh.model.occ.synchronize()

    all_volumes = gmsh.model.getEntities(dim=3)
    gmsh.model.occ.fragment(
        [(3, tag) for _, tag in all_volumes],
        [],
    )
    gmsh.model.occ.synchronize()

    return dome_tag, drum_tag
```

### 12.6 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 装配后只有一个体 | 用了 fuse | 改成 fragment |
| 交界面网格错位 | 没 fragment、两体独立划分 | 装配后再统一 generate |
| 不知道交界面是哪个面 | 面太多 | 按位置识别（第 7 章方法） |
| fragment 后 tag 又变了 | 正常 | 重新获取实体、再贴物理组 |

### 12.7 本章小结

1. 鼓座 = 外圆柱 − 内圆柱，和球壳同构；
2. 工具体要完全穿透主体（加余量）；
3. `fuse` 焊死（交界面消失），`fragment` 拼装（交界面保留且 conformal）；
4. 多部件装配必须用 fragment，才能分别贴标签、分析传力。

### 12.8 小练习

1. 画一个甜甜圈：外半径 5、内半径 3、高 2，跑通并导出；
2. 解释：为什么 `fragment` 后还要再 `synchronize()`；
3. 用自己的话回答：conformal 网格对 FEM 意味着什么？

---

## 第 13 章 加密、对称、二阶网格与质量评估

### 13.1 本章目标

1. 学会「全局粗、局部细」的加密思路；
2. 理解 28 周期对称切片的意义（知道即可）；
3. 学会二阶网格设置和网格质量评估——**这是工程验收的关键**。

### 13.2 为什么需要局部加密？

球壳的应力分布不均匀：藻井凹角、穹顶-鼓座交界面附近应力梯度大，需要细网格；大片光滑区域用粗网格就行。

**策略**：全局粗（`CharacteristicLengthMax` 大）+ 局部细（`setSize` 或曲率加密）。

```python
# 全局：1.0 m
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 1.0)

# 局部：在凹角点加密到 0.15 m
gmsh.model.mesh.setSize(
    gmsh.model.getEntities(0),     # 所有点
    [(x, y, z, 0.15)],             # (坐标, 局部尺寸)
)
```

`setSize` 的第二个参数是「坐标 + 尺寸」元组列表——在指定坐标附近把网眼设成 0.15 m。

### 13.3 28 周期对称：只算 1/28

万神殿穹顶有 28 重旋转对称：28 个扇区、28 组藻井。建模时只切出 **1/28**（角度 360°/28 ≈ 12.857°），计算量直接缩小约 28 倍。

```python
import numpy as np

angle = 2 * np.pi / 28        # 扇区角 = π/14 ≈ 0.2244 弧度
```

**关键细节**：切割面必须沿着**子午肋**（藻井之间的分隔带），不能从藻井正中间切过去，否则藻井剩半个。

> 对称边界条件（法向位移为零）在文档5 用 Dirichlet BC 实现。你现在只需知道「能切、为什么切」，实现细节在文档5。

### 13.4 二阶网格：从直边到曲边

一阶四面体：4 个节点，边是直线，适合近似直边几何。

二阶四面体：10 个节点（4 顶点 + 6 边中点），边可以弯曲，**贴合球面更好、精度更高**。

```python
gmsh.option.setNumber("Mesh.ElementOrder", 2)
gmsh.model.mesh.generate(3)
```

**代价**：节点数约为原来的 3–5 倍，求解更慢、文件更大。本项目固定用二阶（弯曲壳体必须）。

### 13.5 网格质量评估：查「病单元」

撒完网要体检：有些单元又扁又长（畸形），会污染求解精度。

Gmsh 用 **Gamma 质量指标**（0~1）：

- 1.0 = 正四面体（完美）；
- 0.5 以上 = 良好；
- 0.1 以下 = 严重畸形，必须处理。

```python
# 获取所有单元质量
quality = gmsh.model.mesh.getQuality()

n_total = len(quality)
n_bad  = sum(1 for q in quality if q < 0.1)
n_good = sum(1 for q in quality if q > 0.5)

print(f"总单元: {n_total}")
print(f"高质量 (>0.5): {n_good} ({100*n_good/n_total:.1f}%)")
print(f"低质量 (<0.1): {n_bad} ({100*n_bad/n_total:.1f}%)")
```

**工程验收标准**：低质量单元比例 < 1%。

### 13.6 质量不好怎么办？三板斧

```python
# 1. 开优化器（默认其实会跑，显式写出来）
gmsh.option.setNumber("Mesh.Optimize", 1)

# 2. 网格平滑
gmsh.option.setNumber("Mesh.Smoothing", 10)

# 3. 局部加密（前面学的 setSize）或换算法（第 6 章）
```

如果还不行，通常是几何问题：凹角太尖、薄片太薄。给凹角加小圆角（半径 ≥ 0.05 m）是常用手段。

### 13.7 完整示例：二阶球壳 + 质量报告

```python
import gmsh
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS

gmsh.initialize()
gmsh.model.add("c0_shell_quality")

t_avg = (T_OCULUS + T_BASE) / 2
r_outer = R_INNER + t_avg

outer = gmsh.model.occ.addSphere(0, 0, 0, r_outer)
inner = gmsh.model.occ.addSphere(0, 0, 0, R_INNER)
gmsh.model.occ.synchronize()

result = gmsh.model.occ.cut([(3, outer)], [(3, inner)])
gmsh.model.occ.synchronize()

# 网格：二阶 + 粗尺寸（质量评估示例用）
gmsh.option.setNumber("Mesh.ElementOrder", 2)
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 3.0)
gmsh.model.mesh.generate(3)

# 质量报告
quality = gmsh.model.mesh.getQuality()
print(f"单元数: {len(quality)}")
print(f"平均质量: {np.mean(quality):.3f}")
print(f"最小质量: {np.min(quality):.3f}")

gmsh.finalize()
```

### 13.8 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `getQuality()` 报错 | 没生成网格 | 先 `generate(3)` |
| 低质量单元 >1% | 几何太尖/太薄 | 加圆角、加密、换算法 |
| 二阶网格特别慢 | 单元数暴涨 | 先粗网格调试 |
| 对称切片藻井被切坏 | 切面穿过藻井 | 沿子午肋切 |

### 13.9 本章小结

1. 加密策略：全局粗 + 局部细（`setSize` / 曲率加密）；
2. 28 对称：只算 1/28，切面沿子午肋；
3. 二阶网格：`Mesh.ElementOrder=2`，10 节点，精度高但更贵；
4. 质量指标 Gamma：>0.5 良好，<0.1 畸形，低质量 <1% 为验收线；
5. 质量三板斧：Optimize、Smoothing、局部加密。

### 13.10 小练习

1. 跑 13.7 示例，记录平均质量和最小质量；
2. 把 `ElementOrder` 改回 1，对比单元数和平均质量的变化；
3. 解释：为什么弯曲壳体必须用二阶单元？

---

## 第 14 章 最小完整案例：简化穹顶全流程

### 14.1 本章目标

把本书所有知识串成**一个可独立运行的程序**：均匀厚度球壳 + Oculus 开口 + 物理组 + 二阶网格 + 导出。

### 14.2 完整代码

保存为 `geometry/minimal_dome_demo.py`（这是本书的「毕业设计」）：

```python
#!/usr/bin/env python3
"""
万神殿简化穹顶 · 最小完整案例

流程：
  1. 创建均匀厚度球壳（R_inner=22.03, t=平均厚度）
  2. 切割 Oculus 开口（直径 8.95 m）
  3. 标记物理组（内表面、外表面、拱脚面）
  4. 划分二阶四面体网格
  5. 导出 .msh + PyVista 预览

运行：
  cd /mnt/c/Users/tan83/Desktop/codex/pantheon-3d-fem
  conda activate pantheon-fem
  python geometry/minimal_dome_demo.py
"""
import numpy as np
import gmsh
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.params import R_INNER, T_BASE, T_OCULUS, D_OCULUS


def create_shell():
    """均匀厚度球壳（平均厚度近似），返回壳体的 tag"""
    t_avg = (T_OCULUS + T_BASE) / 2
    r_outer = R_INNER + t_avg

    outer = gmsh.model.occ.addSphere(0, 0, 0, r_outer)
    inner = gmsh.model.occ.addSphere(0, 0, 0, R_INNER)
    gmsh.model.occ.synchronize()

    result = gmsh.model.occ.cut([(3, outer)], [(3, inner)])
    gmsh.model.occ.synchronize()

    for dim, tag in result[0]:
        if dim == 3:
            return tag
    raise RuntimeError("球壳创建失败")


def cut_oculus(shell_tag):
    """在球顶切出 Oculus 圆洞，返回新壳 tag"""
    phi_oculus = np.arcsin(D_OCULUS / (2 * R_INNER))
    z_oculus = R_INNER * np.cos(phi_oculus)

    r_cut = D_OCULUS / 2 + 2.0
    cut_cyl = gmsh.model.occ.addCylinder(
        0, 0, z_oculus - 1,
        0, 0, 30,
        r_cut,
    )
    gmsh.model.occ.synchronize()

    result = gmsh.model.occ.cut(
        [(3, shell_tag)],
        [(3, cut_cyl)],
        removeObject=True,
        removeTool=True,
    )
    gmsh.model.occ.synchronize()

    for dim, tag in result[0]:
        if dim == 3:
            return tag
    raise RuntimeError("Oculus 切割失败")


def mark_groups(shell_tag):
    """按 bbox 特征标记物理组（2026-08-15 修 P-03）：
    内表面200 / 外表面300 / 拱脚面400(z=0环) / Oculus边缘100 / 体1000

    ⚠️ P-03 坑：早期版本按「bbox 中心离球心距离」判断内/外表面——
    对整块球面（如外球面片）的 bbox 中心在球心附近，判断全部失效。
    正解：按「形状特征」判断——薄面(环) vs 球面片 + x 半宽。
    """
    inner, outer, base, oculus = [], [], [], []

    for dim, tag in gmsh.model.getEntities(dim=2):
        bbox = gmsh.model.occ.getBoundingBox(dim, tag)
        z_span = bbox[5] - bbox[2]
        half_w = (bbox[3] - bbox[0]) / 2  # x 半宽 = z=0 截面半径（球面片）

        if z_span < 0.01:                # 薄面 = 环
            if abs(bbox[2]) < 0.01:
                base.append(tag)         # z≈0 → 拱脚环面
            else:
                oculus.append(tag)       # z≈21.57 → Oculus 边缘环面
        elif half_w > R_INNER + 1.0:
            outer.append(tag)            # 半宽≈25.73 → 外球面片
        else:
            inner.append(tag)            # 半宽≈22.03 → 内球面片

    gmsh.model.addPhysicalGroup(2, inner,  tag=200, name="dome_inner")
    gmsh.model.addPhysicalGroup(2, outer,  tag=300, name="dome_outer")
    gmsh.model.addPhysicalGroup(2, base,   tag=400, name="dome_base")
    gmsh.model.addPhysicalGroup(2, oculus, tag=100, name="oculus_edge")
    gmsh.model.addPhysicalGroup(3, [shell_tag], tag=1000, name="dome_body")

    print(f"物理组: 内{len(inner)}面 外{len(outer)}面 拱脚{len(base)}面 "
          f"Oculus{len(oculus)}面 体1")


def main():
    output_dir = Path("output/meshes")
    output_dir.mkdir(parents=True, exist_ok=True)

    gmsh.initialize()
    gmsh.model.add("pantheon_minimal_dome")

    print("[1/4] 创建球壳...")
    shell_tag = create_shell()

    print("[2/4] 切割 Oculus...")
    shell_tag = cut_oculus(shell_tag)

    print("[3/4] 标记物理组...")
    mark_groups(shell_tag)

    print("[4/4] 撒网 + 导出...")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 2.0)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.model.mesh.generate(3)

    out = output_dir / "minimal_dome.msh"
    gmsh.write(str(out))
    gmsh.finalize()
    print(f"✅ 完成: {out}")


if __name__ == "__main__":
    main()
```

### 14.3 这个程序的结构（为什么这样分函数）

| 函数 | 职责 | 输入 → 输出 |
| --- | --- | --- |
| `create_shell` | 建球壳 | 无 → 壳 tag |
| `cut_oculus` | 切洞 | 壳 tag → 新壳 tag |
| `mark_groups` | 贴标签 | 壳 tag → 无 |
| `main` | 编排全流程 | 无 → 无 |

每个函数**只做一件事**，参数和返回清晰——这就是文档2 讲的模块化思想，现在你应该能体会到为什么这样写：出错了能单独测、改一处不牵连别处。

### 14.4 运行与验收

```bash
python geometry/minimal_dome_demo.py
```

**通过标准**：

```text
[1/4] 创建球壳...
[2/4] 切割 Oculus...
[3/4] 标记物理组...
物理组: 内X面 外Y面 底Z面 体1
[4/4] 撒网 + 导出...
✅ 完成: output/meshes/minimal_dome.msh
```

然后确认：

```bash
ls -lh output/meshes/minimal_dome.msh
```

最后用 meshio 读一遍（第 8.6 节），确认节点和单元数正常。

### 14.5 本章小结

1. 一个工程脚本 = 若干「单职责」函数 + 一个 main 编排；
2. 本章案例串起了全书：球壳 → Oculus → 物理组 → 二阶网格 → 导出；
3. 学会了它，C0 和后续算例的几何部分就有了模板。

### 14.6 小练习

1. 跑通案例并记录节点数、单元数；
2. 给 `mark_groups` 加一个物理组：Oculus 边缘面（tag=100，名字 `oculus_edge`）——提示：z 在 21.57 附近的面；
3. 把这个案例讲给 AI 助手听：每行代码在干什么。

---

## 第 15 章 全书统稿：术语表、坑点索引、审核清单

### 15.1 术语表（按出现顺序，随查随用）

#### 软件与代码

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| API | 应用程序接口 | 别人写好的函数按钮，我们按顺序按 |
| GUI | 图形界面 | 用鼠标点的窗口 |
| script | 脚本 | 一段可运行的代码 |
| option | 选项/设置 | 软件的旋钮开关 |
| parameter | 参数 | 喂给函数的值 |
| argument | 实参 | 调用时实际填的值 |
| return value | 返回值 | 函数交回的结果 |
| tag | 编号 | Gmsh 给实体的身份证号 |
| entity | 实体 | 点/线/面/体的统称 |
| module | 模块 | 一个代码文件/功能包 |
| import | 导入 | 把库请进来 |
| list / tuple / dict | 列表 / 元组 / 字典 | 三种数据容器 |
| f-string | 格式化字符串 | `f"半径={r}"` 自动填值 |
| docstring | 函数说明书 | 函数开头三引号注释 |
| Path / mkdir | 路径 / 建目录 | Python 管文件和文件夹 |

#### 几何

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| OCC / OpenCASCADE | CAD 几何内核 | 支持布尔运算的工业级引擎 |
| boolean operation | 布尔运算 | 交、并、差 |
| fuse / union | 并集 | 焊成一体 |
| cut / difference | 差集 | A 减去 B |
| intersect | 交集 | 只留重叠 |
| fragment | 拼装 | 拼但不焊，交界面共享 |
| synchronize | 同步/提交 | 让 Gmsh 真正执行几何操作 |
| bounding box | 包围盒 | 包住实体的最小长方体 |
| axis | 轴 | 旋转/圆柱的基准方向 |
| coordinate | 坐标 | 位置 (x,y,z) |
| sphere / cylinder / cone / box | 球 / 圆柱 / 圆锥台 / 方块 | 四个标准坯料 |
| shell | 壳 | 空心薄壁（外球−内球） |
| NURBS | 自由曲面表示法 | 精确变厚度才用 |

#### 网格

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| mesh | 网格 | 切成的小块集合 |
| node | 节点 | 网眼绳结（单元角点） |
| element | 单元 | 最小块（四面体等） |
| tetrahedron | 四面体 | 金字塔形 3D 单元 |
| characteristic length | 特征长度 | 单元边长目标值 |
| curvature | 曲率 | 弯曲程度，弯处要加密 |
| Delaunay / Frontal / MMG3D | 网格算法名 | 不同的切网手法 |
| element order | 单元阶次 | 1=直边，2=曲边 |
| conformal | 共形/协调 | 交界面节点对齐共享 |
| quality / Gamma | 质量指标 | 0~1 评分，1 完美 |
| optimize / smoothing | 优化 / 平滑 | 修歪单元 |

#### 物理组与 FEM

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| physical group | 物理组 | 面/体打包编号 |
| boundary condition | 边界条件 | 边界规矩 |
| Dirichlet | 狄利克雷边界 | 固定位移的边界 |
| interface | 交界面 | 两体接触面 |
| constraint | 约束 | 限制自由度 |
| material property | 材料属性 | 密度/弹模等 |

#### 数学与项目专有

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| spherical coordinates | 球坐标 | (r, φ, θ) 描述球面点 |
| meridian angle φ | 子午角 | 从球顶往下量的角 |
| azimuthal angle θ | 环向角 | 水平绕 z 轴的角 |
| radian / degree | 弧度 / 度 | 角度两种单位 |
| arcsin | 反正弦 | 由正弦反求角度 |
| clip | 夹取 | 把数限制在区间内 |
| oculus | 穹顶圆洞 | 顶部直径 8.95m 的洞 |
| coffer | 藻井 | 内表面方形凹槽 |
| drum | 鼓座 | 穹顶下环形墙 |
| inner / outer | 内 / 外 | 内外表面 |
| sector | 扇区 | 28 等分中的一份 |

### 15.2 全书坑点索引（卡住先看这里）

| 症状 | 章节 | 原因 |
| --- | --- | --- |
| `ModuleNotFoundError` | 2.7 | 环境没激活或目录不对 |
| 几何「消失」 | 2.3 | 忘 `synchronize()` |
| tag 对不上 | 5.4 | 布尔后旧 tag 作废 |
| 切出来是空的 | 4.9 | 两体不相交 |
| 圆柱方向歪 | 3.6 | 轴向向量写错 |
| `np.sin` 结果不对 | 9.4 | 度/弧度混用 |
| rotate 角度错 | 11.4 | rotate 用「度」 |
| 切不干净 | 11.2 / 12.2 | 工具没完全穿透 |
| FEniCSx 找不到物理组 | 7.8 | 布尔后才贴标签 |
| 网格太慢/文件太大 | 6.8 | 尺寸太小 |
| 低质量单元多 | 13.6 | 几何太尖/太薄 |
| 藻井被切坏 | 13.3 | 对称面穿过藻井 |

### 15.3 全套审核清单（交付前逐条打勾）

#### 几何

- [ ] 内半径 = 22.03 m（来自 `params.py`）
- [ ] 球壳 = 外球 − 内球，无多余原体残留
- [ ] 布尔运算全部完成后才贴物理组
- [ ] Oculus 直径 8.95 m，切口干净穿透

#### 网格

- [ ] 全部为二阶四面体（`ElementOrder=2`）
- [ ] 低质量单元（Gamma<0.1）比例 < 1%
- [ ] 局部加密覆盖藻井凹角/交界面
- [ ] 多部件交界面 conformal（用了 fragment）

#### 物理组

- [ ] 编号与 7.4 表一致（100/200/300/400/500/600/700/1000/2000）
- [ ] 每个物理组名字正确
- [ ] FEniCSx 能读到（文档5 验证）

#### 文件输出

- [ ] `.msh` 导出成功且 meshio 可读
- [ ] 文件大小合理（<500 MB）
- [ ] 脚本无硬编码魔法数字（全部来自 params.py）

### 15.4 练习参考答案（先做再看！）

**第 2 章**：六步骨架 = initialize → model.add → occ.xxx(几何) → synchronize → mesh.generate → write → finalize。

**第 3 章**：`(2, 7)` = 2 维（面），编号 7。

**第 5 章**：不能用旧变量——布尔运算创建了新实体，旧 tag 已失效；壳的 tag 只能从 `result[0]` 重新取。

**第 9 章**：φ=45°, θ=45°, r=22.03 → x≈11.02, y≈11.02, z≈15.58（可用 `spherical_to_cartesian` 验证）。

**第 11 章**：先旋转再平移——rotate 绕原点转，先挪走再转会把方块转到错误位置。

**第 13 章**：弯曲壳体用直线边的一阶单元无法贴合曲面，会有几何误差；二阶单元边可弯曲，贴合更好。

### 15.5 结课寄语

恭喜你走到这里。现在你应该已经掌握：

- 六步骨架跑通任何 Gmsh 脚本；
- 布尔运算三件套（焊/交/切）和「切后找 tag」；
- 网格粗细控制与质量验收；
- 物理组编号方案；
- 参数化与球坐标换算。

**下一步**：带着 `output/meshes/c0_shell.msh` 进入文档5——FEniCSx 有限元求解，让网格真正「算起来」。

---

> 全书完（v2.0，2026-08-13 重写）。旧版存档于 `docs/tutorials/_legacy/`。

---

## 实战增补 · 万神殿四个几何脚本的完整战役（2026-08）

> 本章基于《万神殿全解》成书卷五：C0→C7 四个几何脚本的逐行实战精华，含本项目最惨烈的「藻井网格攻坚六招」。与正文章节互补：正文教 API，本章教战役。

### 增补 1：四个脚本的架构演进（几何建模的分层思想）

| 版本 | 脚本 | 几何方案 | 局限 → 下一版解决 |
| --- | --- | --- | --- |
| C0 | c0_spherical_shell.py | 两球相减（等厚） | 无拱脚面、无物理组 |
| C1/C2 | minimal_dome_demo.py | 截断半球 + Oculus + 物理组 | 等厚近似 |
| C3 | c3_variable_coffer.py | **旋转母线变厚度 + 140 盒藻井** | 藻井尖角 → 倒转单元 |
| C6/C7 | c6_drum_base.py | 穹顶+鼓座+基座 fuse + 藻井 | 鼓座尺寸推定、无壁龛 |

**演进主线**：每一步增加真实度（等厚→变厚度→加藻井→加鼓座基座），每一步都验证上一步的简化假设——**这就是「分层对照」算例矩阵在几何层的体现。**

### 增补 2：旋转母线法——从「两球相减」到「变厚度穹顶」

等厚壳 = 外球减内球。变厚度壳 = **画 2D 截面绕 z 轴旋转**：

```python
arc = gmsh.model.occ.addCircleArc(p_ai, p_ctr, p_bi)   # 内面 = 真圆弧（球心为圆心）
l_spring = gmsh.model.occ.addLine(p_bi, p_bo)          # 拱脚端盖
phis = np.linspace(np.pi/2, phi_o, 60)                 # 外面 = 60 段折线逼近厚度函数
outer_lines = [addLine(ot[k], ot[k+1]) for k in ...]   # r = R_INNER + thickness(p)
loop = gmsh.model.occ.addCurveLoop([arc, l_spring] + outer_lines + [l_oculus])
surf = gmsh.model.occ.addPlaneSurface([loop])
out = gmsh.model.occ.revolve([(2, surf)], 0,0,0, 0,0,1, sweep_angle)   # 绕 z 轴旋转
```

**两条实战铁律**：
1. **内面用真圆弧**——8/17 首版内面也用折线，产生负雅可比（网格单元翻转）；改真圆弧后修好。「几何上平滑的面比折线更容易出好网格。」
2. **revolve 扫角可参数化**——整天 2π，或 `--slice` 时 2π/28（28 周期对称切片）。

### 增补 3：位置识别法——不猜 tag，用几何特征定位

布尔操作后 tag 全乱（tag 作废原理），物理组标记的唯一可靠方式是**位置识别**（mark_groups 实战，P-03 修正版）：

```python
for dim, tag in gmsh.model.getEntities(dim=2):
    bbox = gmsh.model.occ.getBoundingBox(dim, tag)
    z_span = bbox[5] - bbox[2]          # 面在 z 方向的跨度
    half_w = (bbox[3] - bbox[0]) / 2    # x 半宽 = z=0 截面半径
    if z_span < 0.01:                    # 「薄」面 = 环
        if abs(bbox[2]) < 0.01: base.append(tag)      # z≈0 → 拱脚环
        else: oculus.append(tag)                       # z≈21.57 → Oculus 环
    elif half_w > R_INNER + 1.0: outer.append(tag)     # 半宽≈25.73 → 外球面片
    else: inner.append(tag)                             # 半宽≈22.03 → 内球面片
```

**三招**：① z 跨度区分「环」与「球面片」；② z 位置区分拱脚环（0）与 Oculus 环（21.57）；③ 半宽区分外球面（25.73>23.03）与内球面（22.03）。**P-03 教训**：整块面的 bbox 中心判断失效（外球面片中心 z≈0 与拱脚环撞车）——中心不靠谱，跨度+位置才靠谱。

### 增补 4：布尔余量——CAD 的隐藏保险

```python
r_cut = D_OCULUS/2 + 2.0    # 切 Oculus 的圆柱比洞粗 2m
box = addBox(..., -d/2-margin, w, h, d/2+margin)   # 藻井盒多伸 0.5m 进壳体
```

**白话**：工具比目标「多伸一截」，避免圆柱面与球面「刚好相切」——**相切布尔是 CAD 经典病态**（拓扑判定在容差边缘摇摆）。margin 是几何脚本的保险丝。

### 增补 5：藻井网格攻坚六招（8/17 最惨烈战役，全部留档）

**问题**：满圆周 140 藻井（140 个 90° 再入角）的完整曲边网格有 8 个倒转单元 → FEniCSx 无法求解。

| 招 | 手段 | 结果 |
| --- | --- | --- |
| 1 | 全局加密（--lc 0.8/1.0） | ❌ 无效——倒转是几何奇异，加密治标不治本 |
| 2 | Mesh.HighOrderOptimize=2 | ⚠️ 倒转 14→8（减不净） |
| 3 | occ.fillet/chamfer 圆角 | ❌ API 失效（P-09：fillet 不认 OCC 边 tag、chamfer 签名不符） |
| 4 | 棱边 setSize 局部加密 | ❌ 布尔后失效（P-11） |
| 5 | Mesh.SecondOrderLinear=1（直边二阶） | ✅ **倒转清零但失曲边精度**（c3_coffer_lin2.msh，74.2° 突破网格） |
| 6 | 28 切片（再入角 140→5 个） | ✅ **完整曲边倒转清零**（c3_coffer_28.msh，worst distortion 0.81） |

**核心机理**：**「再入角数量决定倒转」**——28 切片完整曲边能清零，证明不是曲边本身的问题，而是 140 个尖角的累积效应。**网格质量问题的根在几何，不在网格器。**

### 增补 6：fuse 共形 + 材料分区后置

```python
fused = gmsh.model.occ.fuse([(3,dome)], [(3,drum), (3,base)])   # 三件焊接成单一体
```

**架构选择**：几何 fuse 成单一体（交界面网格共节点），**材料分区留给求解阶段按坐标 callable 赋**（E 按 z 三层 np.where）。比「三个体分别贴物理组」简单得多——「几何单一体 + 求解时分区」是 C6/C7 的关键简化。

### 增补小练习

1. 用旋转母线法画出「等厚半球壳」的 2D 截面（4 条边分别是什么曲线/直线）。
2. 位置识别法里，如果拱脚环的 z 位置从 0 移到 -26.2（C6 基座底面），三招怎么改？
3. 复述六招攻坚，说明为什么第 6 招能证明「再入角数量决定倒转」。
4. 你的下一个几何脚本里，哪些布尔操作需要加 margin？

# 文档2 · Python 模块化工程开发规范（重构版）

> **项目**：万神殿穹顶三维 FEM 重构
> **版本**：v2.0 轮次 1/4（2026-08-13 逐轮重写）
> **定位**：让你写出的代码「能活过一个月」——可读、可改、可测

---

## 写给你的使用说明（30 秒读完）

这本教材不教 Python 语法，教**怎么把 FEM 项目组织得像工程而不是草稿**。

核心就三条：

1. **参数集中**：所有数字进 `config/params.py`；
2. **一函数一职责**：每个函数只做一件事；
3. **命名说人话**：变量名、函数名、文件名都一眼看懂。

学完标准：**随便打开项目里一个文件，5 秒内能说出它干什么、从哪来、改哪里**。

### 🎩 老板版速读（30 秒，Leader 必读）

你不写代码，但验收 AI 代码时做**四连查**：

1. **搜魔法数字**：代码里出现 22.03 / 5.9 / 1600 → 退回，必须从 `params.py` 导入；
2. **看函数长度**：超过 50 行 / 一个函数干多件事 → 退回拆分；
3. **看 docstring**：每个函数开头三引号说明「干什么 + 输入输出」；
4. **看命名**：`r_inner`、`build_shell` 这种说人话的名字，而不是 `x`、`func1`。

四连查全部通过 = 代码大概率能活过一个月。

---

## 第 1 章 为什么必须模块化

### 1.1 2000 行脚本的噩梦

假设你把整个 FEM 流程写进一个 `main.py`：

```text
main.py —— 2000 行
  前 500 行：几何参数（几十个数字）
  中 500 行：Gmsh 建模
  中 500 行：FEniCSx 求解
  后 500 行：PyVista 画图
```

问题：

- 改一个参数要翻 500 行找到它；
- 几何出 bug，求解代码也得跟着重跑；
- 想复用「建模」部分？复制粘贴 500 行；
- 别人（包括一个月后的你）根本看不懂。

### 1.2 模块化 = 把项目拆成「能独立说话」的文件

```text
config/           参数（唯一数据源）
geometry/         几何建模
fem_solver/       有限元求解
post_process/     后处理出图
cases/            算例入口（C0/C1/C2...）
```

每个目录只负责一件事，文件之间通过「函数调用」协作，不互相抄代码。

### 1.3 模块化的三大收益

| 收益 | 白话 |
| --- | --- |
| 可读 | 看目录就知道项目结构 |
| 可改 | 改几何不影响求解 |
| 可测 | 每个函数单独验证 |

### 1.4 本章小结

1. 2000 行脚本 = 技术债；
2. 模块化 = 按职责拆文件；
3. 三大收益：可读、可改、可测。

### 1.5 小练习

1. 说出万神殿项目六个目录各干什么；
2. 思考：为什么参数单独放一个文件？

---

## 第 2 章 参数统一管理：config/params.py

### 2.1 铁律

> **任何脚本不出现「魔法数字」**（22.03、5.9、1600 这种直接写在代码里的数），一律从 `config/params.py` 导入。

### 2.2 params.py 长什么样

项目已有 `config/params.py`，结构：

```python
# 一、几何参数
R_INNER = 22.03          # 内半径 (m) ✅
T_BASE = 5.9             # 拱脚厚度 (m) ⚠️ 待核对
D_OCULUS = 8.95          # Oculus 直径 (m) ✅

# 二、材料参数
E_CONCRETE = 14.8e9      # 弹性模量 (Pa) ⚠️
NU_CONCRETE = 0.2        # 泊松比 ✅
DENSITY_STEPS = [...]    # 密度分层 ✅

# 三、荷载与求解器
G = 9.81
MESH_LENGTHS = {...}
```

特点：

- 按类别分区（几何/材料/荷载/求解器）；
- 每个参数一行注释：含义 + 单位 + 状态标记（✅/⚠️）；
- 状态标记表示「是否核对过原文」——这是科研项目的要求。

### 2.3 怎么用

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.params import R_INNER, T_BASE

print(R_INNER)   # 22.03
```

（路径引导三行的原因，文档4 第 9.2.1 节讲过。）

### 2.4 坏 vs 好

**坏**：

```python
def build_shell():
    outer = gmsh.model.occ.addSphere(0, 0, 0, 25.73)  # 魔法数字！
```

**好**：

```python
def build_shell():
    r_outer = R_INNER + (T_OCULUS + T_BASE) / 2
    outer = gmsh.model.occ.addSphere(0, 0, 0, r_outer)
```

好代码的**计算过程可见**：读者能看出 25.73 是怎么来的。

### 2.5 本章小结

1. 铁律：无魔法数字；
2. params.py 分区 + 注释 + 状态标记；
3. 用 `from config.params import ...` 导入。

### 2.6 小练习

1. 打开 `config/params.py`，说出每个参数的含义和单位；
2. 找一个文档4 示例里的魔法数字，改成从 params 导入；
3. 解释 ⚠️ 标记的意义。

---

## 第 3 章 一函数一职责

### 3.1 原则

> **一个函数只做一件事，名字说明那件事。**

### 3.2 坏 vs 好

**坏**（一个函数干三件事）：

```python
def run_all():
    # 建模
    # 网格
    # 求解
    # 画图
    ...
```

**好**（拆成四个）：

```python
def build_geometry(params):
    """创建几何，返回壳 tag"""
    ...

def generate_mesh(shell_tag):
    """划分网格，返回网格文件路径"""
    ...

def solve(mesh_file):
    """求解，返回结果"""
    ...

def plot(result):
    """出图"""
    ...
```

### 3.3 函数设计四问

写函数前问自己：

1. 它只做一件事吗？（超过一件事就拆）
2. 输入是什么？（参数明确）
3. 输出是什么？（返回值明确）
4. 名字能说明它干什么吗？（不能就改名）

### 3.4 文档字符串（docstring）

每个函数开头三引号说明：

```python
def build_shell():
    """
    创建球壳几何（外球减内球）。

    返回：
        shell_tag: 球壳体在 Gmsh 中的 tag
    """
```

写清楚「干什么 + 输入输出」，一个月后的你就不用读代码猜。

### 3.5 本章小结

1. 一函数一职责，名字即说明；
2. 四问自检：一件事？输入？输出？名字？
3. docstring 写「干什么 + 输入输出」。

### 3.6 小练习

1. 把「坏例子」拆成四个函数；
2. 给拆好的函数写 docstring；
3. 用四问检查自己最近的脚本。

---

## 第 4 章 命名规范与常见坏习惯

### 4.1 命名规范

| 对象 | 规范 | 例子 |
| --- | --- | --- |
| 变量 | 小写 + 下划线 | `r_inner`、`shell_tag` |
| 常量 | 全大写 | `R_INNER`、`E_CONCRETE` |
| 函数 | 动词开头 + 下划线 | `build_shell`、`cut_oculus` |
| 文件 | 小写 + 下划线 | `c0_spherical_shell.py` |

**核心原则：名字说人话**。`x` 不如 `r_inner`，`t` 不如 `thickness`。

### 4.2 常见坏习惯对照

**坏习惯 1：硬编码路径**

```python
# 坏
open("C:/Users/tan83/Desktop/codex/pantheon-3d-fem/output/mesh.msh")

# 好（相对项目根）
open("output/meshes/mesh.msh")
```

换电脑、换目录就坏的路径叫「绝对路径依赖」。

**坏习惯 2：神秘数字**

```python
# 坏
r = 22.03 * 1.17

# 好
r_outer = R_INNER + (T_OCULUS + T_BASE) / 2
```

**坏习惯 3：一个函数 300 行**

→ 拆。见第 3 章。

**坏习惯 4：假设一切正常**

```python
# 坏：文件不存在直接崩溃
data = np.genfromtxt("output/data/result.csv")

# 好：先检查 + 清晰报错
from pathlib import Path
if not Path("output/data/result.csv").exists():
    raise FileNotFoundError("请先运行求解脚本生成 result.csv")
```

**坏习惯 5：类型不清**

```python
# 坏
def process(data, flag): ...

# 好：类型标注
def process(data: np.ndarray, flag: bool) -> np.ndarray: ...
```

### 4.3 本章小结

1. 命名：小写下划线变量、大写常量、动词函数；
2. 五坏习惯：硬编码路径、魔法数字、超长函数、无检查、无类型；
3. 每一条都有对应好习惯。

### 4.4 小练习

1. 给自己的旧脚本做「坏习惯体检」（对照 4.2）；
2. 改 3 处不合规的命名；
3. 解释为什么硬编码绝对路径是坏的。

---

## 第 5 章 完整示例 + 审核清单

### 5.1 一个合格的模块长什么样

以 `geometry/dome_geometry.py` 为模板：

```python
"""
穹顶几何模块：球壳、Oculus、藻井
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gmsh
from config.params import R_INNER, T_OCULUS, T_BASE, D_OCULUS


def build_shell():
    """创建球壳，返回壳 tag"""
    t_avg = (T_OCULUS + T_BASE) / 2
    outer = gmsh.model.occ.addSphere(0, 0, 0, R_INNER + t_avg)
    inner = gmsh.model.occ.addSphere(0, 0, 0, R_INNER)
    gmsh.model.occ.synchronize()

    result = gmsh.model.occ.cut([(3, outer)], [(3, inner)])
    gmsh.model.occ.synchronize()

    for dim, tag in result[0]:
        if dim == 3:
            return tag
    raise RuntimeError("球壳创建失败")


def cut_oculus(shell_tag):
    """切 Oculus 圆洞，返回新壳 tag"""
    ...


if __name__ == "__main__":
    # 模块自测：直接运行本文件时执行
    gmsh.initialize()
    gmsh.model.add("dome_test")
    tag = build_shell()
    print("自测通过，壳 tag =", tag)
    gmsh.finalize()
```

**注意最后一段**：`if __name__ == "__main__"` 让模块既能被 import，也能单独运行自测。

### 5.2 审核清单（交付前逐条打勾）

- [ ] 无魔法数字（全部来自 params.py）
- [ ] 无硬编码绝对路径
- [ ] 每个函数 ≤ 50 行、只做一件事
- [ ] 函数有 docstring（干什么 + 输入输出）
- [ ] 命名规范（小写/大写/动词）
- [ ] 有错误检查（文件存在、tag 非空）
- [ ] 能 `python 文件.py` 单独自测
- [ ] 核心示例在文档4/5 中可运行

---

> 全书完（v2.0，2026-08-13 重写）。旧版存档于 `_legacy/`。

---

## 实战增补 · 万神殿的 Python 工程规范落地实录（2026-08）

> 本章基于《万神殿全解》成书卷四/五/六：唯一参数源、命名规则、fail-fast、callable 插值——四条规范在 16 个源文件中的真实落地。

### 增补 1：唯一参数源的完整形态（config/params.py 161 行实战）

```python
ROOT = Path(__file__).resolve().parents[1]   # 从 params.py 位置反推项目根
OUTPUT_DIR = ROOT / "output"
...
for _d in (OUTPUT_DIR, MESH_DIR, RESULT_DIR, FIGURE_DIR, DATA_DIR):
    _d.mkdir(parents=True, exist_ok=True)   # 自动建目录
```

三个设计亮点：
1. **Path(__file__).parents[1]**：任何脚本从任何目录 import 都能拿到正确的项目根——「相对路径铁律」的实现方式；
2. **三级溯源**：params.py（机器可读）↔ 参数溯源表（人类可读）↔ 文献 PDF（原文），改一处三处同步；
3. **状态标记**：每个参数带 ✅/⚠️/🔴 户口——✅ 双源验证、⚠️ 待核对、🔴 占位+敏感性。**「不编造参数」从口号变成数据结构。**

### 增补 2：命名即元数据（.bp 结果文件实战）

```
c4_ml_swpsh_E1.0_sh6.00e-05_sigma.bp
│  │   │       │      │         └── 场类型（sigma/u/D）
│  │   │       │      └── 干缩应变 6e-5
│  │   │       └── 弹性模量 1.0 GPa
│  │   └── 荷载（sw=自重 sh=干缩 swpsh=自重+干缩，p 是 + 的替身）
│  └── 网格标记（m=2.0m m1m=1.0m m0p5ms=0.5m ml=分层密度）
└── 算例编号
```

**一套可 grep 的命名体系 = 文件名即元数据**。`glob("*swpsh*E1.0*")` 秒查任何算例组合。给文件起名时问：三年后的人只看文件名，能还原出什么信息？

### 增补 3：fail-fast 的三种实战形态

```python
# 形态 1：显式失败态 + 源头断言（c0_spherical_shell.py）
for dim, tag in result[0]:
    if dim == 3: return tag
return None                    # ← 显式失败态
# main() 里：
assert shell_tag is not None, "球壳 tag 不能为空，检查布尔运算"

# 形态 2：物理组找不到立刻报清楚（所有求解器）
base_facets = facet_tags.find(400)
if base_facets.size == 0:
    raise RuntimeError("find(400) 为空：物理组没贴好，回 geometry/minimal_dome_demo.py 检查")

# 形态 3：布局不一致显式报错（c4 后处理）
raise RuntimeError(f"坐标布局未识别：Xg.shape={Xg.shape} vs 应力点 {n_pts}")
```

**共同点**：把「错误潜伏到终点报怪错」变成「源头立刻报清晰错」。fail-fast 的报错信息要包含：什么错了 + 去哪修。

### 增补 4：callable 插值——dolfinx 0.8 最稳的场赋值写法

```python
W_rho = fem.functionspace(domain, ("Lagrange", 1))
rho = fem.Function(W_rho)
def rho_fill(x):                    # x: (3,N) 坐标数组，每列一个点
    return np.where(x[2] >= 0.0, 1350.0, 1600.0)
rho.interpolate(rho_fill)
```

**为什么这是最稳写法**（P-02/P-04 坑的教训）：ufl 的 conditional/ge 吃 numpy 数组报错；旧 API 的 Expression+element 在 0.8 失效。**Python 函数 + np.where + interpolate 是跨版本最稳的场赋值方式**——项目 6 个求解器全部统一此写法。

### 增补 5：坏习惯对照（项目实测版）

| 坏习惯 | 项目中的真实后果 |
| --- | --- |
| 魔法数字 | V1.0 MATLAB 脚本把 B_pct=8.085 写死，参数修正后图全错 |
| 数据与代码不分离 | V1.0 的 scan_summary.txt 靠重定向存档，V2.0 才改成代码驱动 |
| 不检查文件存在 | mesh 不存在时 dolfinx 报看不懂的错——项目统一 FileNotFoundError 前置检查 |
| 布局假设不验证 | c4 首跑坐标布局断言炸掉（P-07b）——不信任 API 文档，运行时自适应 |

### 增补小练习

1. 找 params.py 里任意一个 ⚠️ 参数，说明它为什么不是 ✅。
2. 给下面这个结果文件起名的每一段做注释：`c6_c6_drum_base_swpsh_sh1.00e-04_sigma.bp`
3. 你写的上一个脚本里，哪一处错误会「潜伏到最后才报怪错」？改成 fail-fast 试试。

# Pantheon 3D FEM — 罗马万神殿穹顶的三维有限元重构

> 一座 1900 年历史的无筋混凝土穹顶，140 个藻井，176 万自由度——用开源有限元工具链回答一个悬而未决的问题：**子午向裂缝为什么「恰好」止于纬度 57°？**

## 项目简介

公元 126 年，罗马人建造了万神殿（Pantheon）：内径 44.06 m 的无筋混凝土穹顶，内表面凿有 5 层 × 28 个 = 140 个方形藻井（coffer）。1934 年 Terenzio 系统记录了穹顶裂缝：子午向裂缝沿经线从底部向上爬，**止于纬度约 57°**。

本项目用 **Gmsh（几何/网格）+ FEniCSx（有限元求解）+ PyVista（可视化）** 建立穹顶 + 鼓座 + 基座的三维实体有限元模型，输出完整三维应力张量，把「裂缝止于 57°」这一观测复现到**定量机理**层面。

### 核心科学结论

1. **裂缝机理**：子午向裂缝是约束干缩驱动的张开型（mode I）开裂——穹顶作为封闭圆环，干缩被自身闭合几何约束，产生环向拉应力；超过古罗马混凝土极低的抗拉强度 $f_t = 0.08$ MPa 即开裂。
2. **57° 的本质**：裂缝止于**环向拉→压转变线**——「恰好 57°」不是常数，而是真实结构在该应力状态下的环向转压纬度（Flügge 理论均匀半球约 52°；Masi 2018 全结构模型 47.4~65.8°；Terenzio 1934 实测约 57°，恰落其中）。
3. **藻井的角色**：藻井不是裂缝的「原因」，而是「**放大器**」——方形尖角的应力集中把孤立开裂点抬到 74°（虚高散点），而连贯裂缝带始终贴着环向转压线（30~41°）。
4. **藻井经济性**：藻井减重 8.09%（1987.8 t）换全环开裂，若只为减重则性价比差；但裂缝不致命（壳→拱稳定转换，穹顶安然 1900 年），且致裂主因是尖角几何而非减重本身——真实罗马藻井（圆角 + 四级阶梯）可兼得减重与低裂。

### 算例矩阵（C0~C7）

| 算例 | 内容 | 关键结果 |
| --- | --- | --- |
| C0 | 光滑球壳基准 | 工具链闭环（0 畸形四面体） |
| C1 | 等厚穹顶 + 刚性拱脚 + 自重 | 网格无关性三档收敛，实测收敛阶 p = 2.32，误差 0.006% |
| C2 | C1 + 分层密度 | 分层较单层位移 -15.6% |
| C2+ | C2 + Rankine 无拉伸损伤 | 损伤区 0.10~0.14%，σ1 截断回 f_t |
| C3 | 变厚度 + 140 藻井 | 直边版 θ_top = 74.2°（突破，见口径说明） |
| C4 | C2 + 干缩（热类比） | ε_sh 五档扫描 + 三假说检验 |
| C4+ | C4 + Rankine 损伤 | 损伤不改裂缝顶端（假说①证伪） |
| C6 | 穹顶 + 鼓座 + 基座 | θ_top = 14.6°，鼓座非 57° 机制（假说证伪） |
| C7 | C6 + 140 方形藻井（最终模型） | 1.76M DOF，与仅藻井版一致 → 藻井 = 已检验候选中唯一致机 |

> **口径说明**：θ_top = 74.2° 是「σ1 > f_t 的最远**孤立点**」口径（方形尖角应力集中的虚高信号），并非连贯裂缝；连贯裂缝带顶端 12.6° < 环向转压带 30°——裂缝无法在环向受压区张开，后者才是理论屏障。单点极值与连通域的口径区分是 8/17 决战日最重要的方法论武器。

### 关键参数（全部文献溯源，见 `docs/source/pantheon_参数溯源表_v1.md`）

| 参数 | 值 | 来源 |
| --- | --- | --- |
| 穹顶内半径 | 22.03 m | Aliberti & Alonso-Rodríguez 2017（激光扫描 + 摄影测量） |
| 穹顶厚度 | 1.5 m（顶）→ 5.9 m（底） | Masi et al. 2018 |
| Oculus 直径 | 8.95 m | 意大利官方来源 + V1.0 口径交叉 |
| 抗拉强度 f_t | 0.08 MPa | Masi et al. 2018（古罗马轻骨料混凝土实测） |
| 抗压强度 f_c | 5.0 MPa | Masi et al. 2018 |
| 密度梯度 | 1350/1500/1600 kg/m³ | Masi et al. 2018 |
| 收缩应变 ε_sh | 5e-5 ~ 1e-4（五档扫描） | Masi et al. 2018（ε_v/3 桥接） |
| 弹性模量 | 1.0 GPa（收缩龄期）/ 7.0 / 14.8 GPa | Masi et al. 2018 + V1.0 工作值 |

## 快速开始

环境要求：WSL2 Ubuntu 22.04 + conda（FEniCSx 官方不支持 Windows 原生安装）。

```bash
# 一键环境（清华镜像优先）
bash tools/setup_env_wsl.sh
source ~/miniconda3/etc/profile.d/conda.sh && conda activate pantheon-fem

# 环境自检（10/10 全绿）
python3 verification/env_check.py

# 几何建模 → 求解 → 后处理（以 C1 为例）
python3 geometry/minimal_dome_demo.py --lc 2.0 --out c0_shell_groups.msh
python3 fem_solver/c1_dome_selfweight.py --mesh c0_shell_groups.msh --e 14.8e9

# 完整 C1 流水线（几何→验证→求解）
bash scripts/run_c1_chain.sh
```

## 目录结构

```
config/         唯一参数源（params.py，禁止硬编码）
geometry/       Gmsh 几何建模 + 网格（C0/C1/C3/C6 四代）
fem_solver/     弱形式、边界条件、荷载、求解（6 个求解器）
verification/   环境自检
tools/          环境安装、Richardson 误差估计、PDF 取证等
scripts/        C1 全链流水线
docs/source/    权威文档（参数溯源表 / 数据存档 / 57° 研究报告 / 数据总汇）
docs/tutorials/ 从零到一的 FEM 全链学习教程（A 入门 9 课 + B 工具 11 篇）
output/         仿真产物（网格 .msh / 结果 .bp，不入版本库，可复现）
legacy_v1/      V1.0 C++ 一维解析模型存档（只读参考）
```

## 验证体系

- **网格无关性**：三档网格 + Richardson 外推，实测收敛阶 p = 2.32，位移误差 0.006%
- **E 敏感性**：线弹性自重下 σ 与 E 无关（静定），三档 E 验证 u×E 守恒（比值 1.000）
- **量级检验**：底部竖向总反力 = mg、位移毫米级、应力 MPa 级
- **文献对照**：57° 对照 Masi 2018 Table 2（θ_max 47.4~65.8°）
- **诚实标注**：✅ 已验证 / ⚠️ 待确认 / 🔴 未完成，全部写入 `docs/source/` 与代码注释

### 已知边界（未竟清单）

- 阶梯藻井复核（真实罗马几何为圆角 + 四级阶梯，`COFFER_STEPS` 已备好数据）
- 断裂能本构（指数软化 + G_f = 5 J/m² 正则化，输出真实连贯裂缝形态与开度）
- 57° 定量复现（Masi 五档在 C7 全结构上扫描）
- 500 万 DOF 全结构（本机 24 GB 内存实证上限 ~2.5M DOF，需 HPC）
- 鼓座/基座尺寸为推定值（⚠️ 待测绘核实）

## 参考文献

- Masi, F., Stefanou, I., Vannucci, P. *On the origin of the cracks in the dome of the Pantheon in Rome.* Engineering Failure Analysis 92 (2018) 587-596. [HAL OA](https://hal.science/)
- Aliberti, L., Alonso-Rodríguez, Á. *Shape and Layout of the Coffers of the Pantheon's Dome in Rome.* Nexus Network Journal 19 (2017) 465-489.
- Terenzio, A. (1934). *La restaurations du Panthéon de Rome.* —— 裂缝记录原始文献（转引自 Masi 2018）。
- Calladine, C.R. *Theory of Shell Structures.* Cambridge University Press, 1983.（薄膜解参考）

## 许可

MIT License（见 [LICENSE](LICENSE)）。参考文献 PDF 版权归原作者所有，未随仓库分发（可在 HAL/期刊官网获取）。

## AI 协作声明

本项目采用「人机协作」模式：物理建模、判据设计、参数溯源、验证与验收由作者完成；代码编写与文档整理由 AI 辅助完成。所有结论均经文献锚定与数值验证，详见 `docs/source/` 权威文档。

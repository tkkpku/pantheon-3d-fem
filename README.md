# pantheon-3d-fem

罗马万神殿穹顶的三维有限元重构。建模穹顶、鼓座与基座，输出完整三维应力张量，回答子午向裂缝为什么止于纬度约 57°。

工具链：Gmsh 建模与网格，FEniCSx 求解，PyVista 可视化。最终算例 C7 有 176 万自由度。

## 背景

公元 126 年建成的万神殿为无筋混凝土穹顶，内径 44.06 m，内表面有 5 圈 × 28 个方形藻井，共 140 个。Terenzio 于 1934 年记录：子午向裂缝沿经线自底部向上，止于纬度约 57°。

## 结论

1. 裂缝机理。子午向裂缝是约束干缩驱动的张开型开裂。穹顶是封闭圆环，干缩被几何约束，产生环向拉应力，超过 0.08 MPa 的抗拉强度即开裂。
2. 57° 的含义。裂缝止于环向拉转压的纬度线。Flügge 理论在均匀半球上给约 52°，Masi 2018 全结构模型给 47.4 至 65.8°，Terenzio 实测约 57°，落在此区间内。57° 不是常数，是真实结构在该应力状态下的转压纬度。
3. 藻井的作用。藻井不是裂缝成因，是放大器。方形尖角的应力集中把孤立开裂点抬到 74°，而连贯裂缝带始终贴着环向转压线。
4. 减重与经济性。藻井减重 8.09%（1987.8 t），代价是全环开裂。裂缝不致命，穹顶已存续 1900 年；致裂主因是尖角几何而非减重本身，真实罗马藻井为圆角加四级阶梯，可兼顾减重与低裂。

## 算例

| 算例 | 内容 | 结果 |
| --- | --- | --- |
| C0 | 光滑球壳基准 | 工具链闭环，0 个畸形四面体 |
| C1 | 等厚穹顶，刚性拱脚，自重 | 网格无关性三档收敛，实测收敛阶 p = 2.32，误差 0.006% |
| C2 | C1 加分层密度 | 相对单层位移 −15.6% |
| C2+ | C2 加 Rankine 无拉伸损伤 | 损伤区 0.10~0.14%，σ1 截断回 f_t |
| C3 | 变厚度加 140 藻井 | θ_top = 74.2°（直边版，见口径说明） |
| C4 | C2 加干缩（热类比） | ε_sh 五档扫描，检验三个假说 |
| C4+ | C4 加 Rankine 损伤 | 损伤不改裂缝顶端，假说①证伪 |
| C6 | 穹顶加鼓座加基座 | θ_top = 14.6°，鼓座非 57° 机制，假说证伪 |
| C7 | C6 加 140 方形藻井（最终模型） | 1.76M 自由度，与仅藻井版一致，藻井是唯一可解释的机制 |

口径说明：θ_top = 74.2° 取的是「σ1 > f_t 的最远孤立点」，是方形尖角应力集中的虚高信号，不是连贯裂缝。连贯裂缝带顶端在 12.6°，位于环向转压带 30° 以下。裂缝无法在环向受压区张开，所以转压线才是理论屏障。区分单点极值与连通域，是这组算例最重要的方法论。

## 参数

全部文献溯源，详见 `docs/source/pantheon_参数溯源表_v1.md`。

| 参数 | 值 | 来源 |
| --- | --- | --- |
| 内半径 | 22.03 m | Aliberti 2017（激光扫描与摄影测量） |
| 厚度 | 顶部 1.5 m，底部 5.9 m | Masi 2018 |
| Oculus 直径 | 8.95 m | 意大利官方来源与 V1.0 交叉核对 |
| 抗拉强度 f_t | 0.08 MPa | Masi 2018（古罗马轻骨料混凝土实测） |
| 抗压强度 f_c | 5.0 MPa | Masi 2018 |
| 密度 | 1350 / 1500 / 1600 kg/m³ | Masi 2018 |
| 收缩应变 ε_sh | 5e-5 至 1e-4，五档扫描 | Masi 2018（ε_v/3 桥接） |
| 弹性模量 | 1.0（收缩龄期）、7.0、14.8 GPa | Masi 2018 与 V1.0 工作值 |

## 安装

需要 WSL2 + Ubuntu 22.04 + conda。FEniCSx 不支持 Windows 原生安装。

```bash
bash tools/setup_env_wsl.sh
source ~/miniconda3/etc/profile.d/conda.sh && conda activate pantheon-fem
python3 verification/env_check.py        # 应 10/10 通过
```

## 用法

```bash
# 几何
python3 geometry/minimal_dome_demo.py --lc 2.0 --out c0_shell_groups.msh

# 求解（C1 自重）
python3 fem_solver/c1_dome_selfweight.py --mesh c0_shell_groups.msh --e 14.8e9

# 全链
bash scripts/run_c1_chain.sh
```

## 目录

```
config/         唯一参数源 params.py，禁止硬编码
geometry/       Gmsh 建模与网格，C0/C1/C3/C6 四代
fem_solver/     弱形式、边界条件、荷载、求解，6 个求解器
verification/   环境自检
tools/          环境安装、Richardson 误差估计、PDF 取证
scripts/        C1 全链流水线
docs/source/    参数溯源表、数据存档、57° 研究报告
docs/tutorials/ A 入门 9 课与 B 工具 11 篇
output/         网格与结果，不入版本库
legacy_v1/      V1.0 C++ 一维解析模型，只读
```

## 验证

- 网格无关性：三档网格加 Richardson 外推，收敛阶 2.32，位移误差 0.006%
- 弹性模量敏感性：线弹性自重下应力与 E 无关，三档 E 下 u×E 守恒，比值 1.000
- 量级检验：底部竖向总反力等于 mg，位移毫米级，应力 MPa 级
- 文献对照：57° 对照 Masi 2018 表 2 的 θ_max 47.4~65.8°
- 标注体系：已验证、待确认、未完成，三档写入 `docs/source/` 与代码注释

## 已知边界

- 阶梯藻井复核：真实罗马几何为圆角加四级阶梯，`COFFER_STEPS` 已备数据
- 断裂能本构：指数软化加 G_f = 5 J/m² 正则化，可输出真实裂缝形态与开度
- 57° 定量复现：Masi 五档参数在 C7 全结构上扫描
- 500 万自由度全结构：本机 24 GB 内存实测上限约 2.5M 自由度，需 HPC
- 鼓座与基座尺寸为推定值，待测绘核实

## 与另一仓库的参数差异

`pantheon` 仓库的顶部厚度写作 1.2 m、密度为 4 层，与本仓库的 1.5 m 与 3 档不同，尚未裁决。厚度与密度进入质量积分，引用结论前需先确定取值。

## 参考文献

- Masi, F., Stefanou, I., Vannucci, P. On the origin of the cracks in the dome of the Pantheon in Rome. Engineering Failure Analysis 92 (2018) 587–596.
- Aliberti, L., Alonso-Rodríguez, M.Á. Shape and Layout of the Coffers of the Pantheon's Dome in Rome. Nexus Network Journal 19 (2017) 465–489.
- Terenzio, A. (1934). 裂缝记录原始文献，转引自 Masi 2018。
- Calladine, C.R. Theory of Shell Structures. Cambridge University Press, 1983.

## 许可

MIT，见 [LICENSE](LICENSE)。参考文献 PDF 版权归原作者，未随仓库分发。

代码编写与文档整理由 AI 辅助完成；物理建模、判据设计、参数溯源、验证与验收由作者完成。

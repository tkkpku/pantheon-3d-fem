# -*- coding: utf-8 -*-
"""万神殿 3D FEM 唯一参数源（V2.0）。

依据：pantheon_参数溯源表_v1.md（权威）
规则：所有几何/材料/荷载参数必须从此文件读取，禁止硬编码。
状态标记：✅ 已双源验证 / ⚠️ 待核对原文 / 🔴 待补充（占位 + 敏感性）
单位：SI（m, kg, Pa, s）

2026-08-11 D1 核对记录（修改人：项目作者 + AI 辅助；依据：Masi et al. 2018 HAL v2 原文，
已入库 docs/references/Masi_2018_cracks_Pantheon.pdf）：
- T_OCULUS 1.2 → 1.5 m（Masi 2018 p.5：5.9 m → ~1.5 m；V1.0 的 1.2 作废）
- R_OCULUS 4.45 → 4.475 m（D_OCULUS/2 统一口径；D=8.95 m 获意大利官方来源交叉印证）
- DENSITY_STEPS 中段 1600/1800 → 1500/1600（Masi Table 1：上 1350/中 1500/下 1600；
  V1.0 的 1800 与 2100（石灰华）为鼓座/墙体区材料，非穹顶）
- FC_CONCRETE 补齐 5.0 MPa（Masi 2018 p.5，混凝土抗压强度 ~5 MPa）
- 新增 GF_CONCRETE=5.0 J/m²（Masi Table 1，穹顶混凝土断裂能）
- E_CONCRETE 14.8 GPa 降级 ⚠️：Masi Table 1 中穹顶 28 天 E=1.0 GPa（收缩模拟龄期值），
  14.8 GPa 出处待复核，暂作工作值 + 敏感性
"""

from pathlib import Path

# ============================================================
# 一、几何参数（来源：Aliberti & Alonso-Rodríguez 2017）
# ============================================================

# 穹顶整体
R_INNER = 22.03            # 内表面球面半径 (m) ✅（激光扫描+摄影测量双验证）
D_INNER = 2.0 * R_INNER    # 穹顶内径 (m) ✅ 44.06
H_TOTAL = 43.44            # 含鼓座总高 (m) ⚠️ 多源共识，需最终核对
Z_CENTER_OFFSET = 0.37     # 球心位于檐口线后方 (m) ✅

# 厚度（⚠️ V1.0 与溯源表存在分歧，开工第一天必须核对 Masi 2018）
T_BASE = 5.9               # 拱脚厚度 (m) ⚠️ 需核对 Mark & Hutchinson 1986 原文
T_OCULUS = 1.5             # Oculus 边缘厚度 (m) ✅ Masi 2018 p.5（5.9→~1.5 m，2026-08-11 核对）

# Oculus（⚠️ V1.0 用 R_OCULUS=4.45，与 D_OCULUS=8.95 不完全自洽）
D_OCULUS = 8.95            # Oculus 直径 (m) ✅ V1.0/Moore 口径 + 意大利官方来源交叉印证（2026-08-11）
R_OCULUS = 4.475           # Oculus 半径 (m) ✅ = D_OCULUS/2 统一口径（2026-08-11；V1.0 的 4.45 作废）

# 藻井（Aliberti 2017 Table 2/3，Northeast quadrant sectors 2–6 平均）
COFFER_LAYERS = 5          # 藻井层数 ✅
COFFER_SECTORS = 28        # 每层扇区数 ✅（28 等分，平均偏差 0.36°）
COFFER_BAND = 0.84         # 水平分隔带弧长 (m) ✅
RIB_WIDTH_L1 = 1.02        # 第 1 层子午肋宽度 (m) ✅
RIB_WIDTH_L5 = 0.67        # 第 5 层子午肋宽度 (m) ✅

# 五层藻井尺寸（底宽/顶宽/弧高/总深度），自下而上 A→E
COFFER_GEOMETRY = [
    # name  bottom_w  top_w  arc_h  depth
    ("A",    3.88,     3.77,  4.08,  0.67),  # ✅
    ("B",    3.74,     3.48,  3.79,  0.65),  # ✅
    ("C",    3.39,     3.02,  3.52,  0.61),  # ✅
    ("D",    2.92,     2.50,  3.05,  0.54),  # ✅
    ("E",    2.38,     2.02,  2.39,  0.48),  # ✅
]

# 藻井四级阶梯深度（Table 3，Sector 2；E 层仅 3 级）
COFFER_STEPS = [
    (0.23, 0.19, 0.13, 0.12),  # A ✅
    (0.22, 0.18, 0.13, 0.12),  # B ✅
    (0.21, 0.18, 0.12, 0.10),  # C ✅
    (0.20, 0.16, 0.11, 0.07),  # D ✅
    (0.19, 0.15, 0.14, None),  # E ✅（第 4 级不存在）
]

# 鼓座与基座（🔴 待补充：Aliberti 2017 不含；Masi 2018 Fig.1（Pulvirenti 2014 尺寸图）
# 含尺寸但需人工目检 PDF 第 3 页；查不到则保持 ±20% 敏感性）
DRUM_HEIGHT = None           # 鼓座高度 (m) 🔴 占位：待查证后填
DRUM_THICKNESS = None        # 鼓座壁厚 (m) 🔴 占位
BASE_DIMENSIONS = None       # 基座尺寸 🔴 占位
DRUM_NICHES = 8              # 鼓座壁龛数量 ✅（总纲 R3 提及，需核对）

# ============================================================
# 二、材料参数（来源：Masi et al. 2018）
# ============================================================

E_CONCRETE = 14.8e9          # 弹性模量 (Pa) ⚠️ 工作值：14.8 GPa 出处待复核；
                             # Masi 2018 Table 1 穹顶 E=1.0 GPa（Brune 2010 砂浆养护 28 天值，
                             # 用于收缩/裂缝模拟）；E 与 ft 由密度按轻骨料混凝土规范外推
                             # （Sanpaolesi & Formichi 2009），非实测。
                             # 2026-08-15 项目决策（方案 A）：E 敏感性扫描定档，见 E_SENSITIVITY
# E 敏感性扫描三档（方案 A，2026-08-15 批）：线弹性自重下 σ 与 E 无关（静定），
# 位移差 14.8 倍；扫描结果用于确定 C2+ 的 E 取值
E_SENSITIVITY = [1.0e9, 7.0e9, 14.8e9]   # (Pa)：Masi 28天值 / 鼓座量级 / 现行工作值
NU_CONCRETE = 0.2            # 泊松比 ✅
FT_CONCRETE = 0.08e6         # 抗拉强度 (Pa) = 80 kPa ✅（Masi 2018 实测）
FC_CONCRETE = 5.0e6          # 抗压强度 (Pa) = 5 MPa ✅（Masi 2018 p.5，混凝土；2026-08-11 补齐）
GF_CONCRETE = 5.0            # 断裂能 (J/m²) ✅（Masi Table 1，穹顶混凝土；墙体 59.4 / 基础 62.1）

# 密度梯度（2026-08-11 按 Masi Table 1 定稿：穹顶上 1350 / 中 1500 / 下 1600；
# 分界纬度沿用 V1.0 的 12°/25°/40° 暂定 ⚠️，待 Mark & Hutchinson 1986 原文精确分界）
DENSITY_STEPS = [
    # (从球顶起算的纬度分界 deg, 密度 kg/m3)
    (12.0, 1350.0),   # 顶部：纯浮石 ✅
    (25.0, 1500.0),   # 中上部 ✅ Masi Table 1（Concrete 4，分界 ⚠️）
    (40.0, 1600.0),   # 中下部 ✅ Masi Table 1（Concrete 3，分界 ⚠️）
    (90.0, 1600.0),   # 底部：穹顶下区 1600 ✅（V1.0 的 2100 石灰华属墙体/基础区，非穹顶）
]

# 鼓座/基础区材料（Masi Table 1，供 C2/C4 使用）
DENSITY_WALL = 1750.0        # 砖面混凝土墙（鼓座） ✅ Masi Table 1（Concrete 2）
DENSITY_FOUNDATION = 2000.0  # 基础 ✅ Masi Table 1（Concrete 1）
E_WALL = 7.0e9               # 鼓座弹性模量 (Pa) ✅ Masi Table 1
E_FOUNDATION = 13.5e9        # 基础弹性模量 (Pa) ✅ Masi Table 1

# ============================================================
# 三、荷载参数
# ============================================================

G = 9.81                     # 重力加速度 (m/s²) ✅（V1.0 用 9.8，统一按标准值）

# 干缩：热应变类比法（2026-08-10 项目决策）
SHRINKAGE_METHOD = "thermal_analogy"   # 备选："prestress_ufl"
# ===== 2026-08-17 按文献重新标定（项目决策：一切以文献为准；V1.0 反算值 1.23e-5 作废） =====
# 依据：Masi et al. 2018（docs/references/Masi_2018_cracks_Pantheon.pdf）
#   p.8 Eq.(1)：ε_v = α·ΔT；现代混凝土体积收缩 ε_v = 0.15~0.30e-3；
#   p.10 Table 2：比值扫描 ε_v/α ∈ [3.4, 4.55] K 五档，θ_max 47.39/49.83/55.89/60.81/65.84°
#                 （裂缝纬度 above the springing，拱脚上方起算）；
#   p.4：Terenzio 1934 实测裂缝止于纬度 ~57°。
# 桥接：各向同性线性自由应变 ε_sh·I；α=体膨胀系数读法 ε_sh=ε_v/3 ∈ [5e-5, 1e-4]，
#       α=线膨胀系数 10~15e-6/K 读法 ε_sh=α·ΔT ∈ [3.7e-5, 6.8e-5]；两读法交集 5~7e-5。
EPS_SHRINKAGE_MASI = (5.0e-5, 1.0e-4)   # 文献范围（线性各向同性，ε_v/3 端点）
SHRINKAGE_SWEEP = [4.0e-5, 5.0e-5, 6.0e-5, 7.0e-5, 1.0e-4]   # C4 主扫描五档 ✅ 2026-08-17 批
EPS_SHRINKAGE = 6.0e-5      # 默认档 ✅ 2026-08-17 批：≈Terenzio 57° ↔ Masi 第3档(3.97K)折中
SHRINKAGE_SENSITIVITY = 0.5  # ⚠️ 旧 ±50% 口径随 1.23e-5 作废，保留占位不再使用
# C4 干缩阶段弹性模量：Masi Table 1 穹顶 28 天 E=1.0 GPa（收缩模拟龄期值）✅ 2026-08-17 批：
# 干缩是特征应变类荷载 σ ∝ E，必须用文献龄期值；E=14.8 GPa 降为敏感性对照档
E_SHRINKAGE = 1.0e9         # C4 主算 E (Pa) ✅ Masi Table 1

# ============================================================
# 四、求解器与网格参数
# ============================================================

ELEMENT_ORDER = 2            # 二阶四面体（CG2），总纲 §1.3 锁定
MESH_LENGTHS = {             # 网格收敛三套（单位 m，按 28 周期切片规模调整）
    "coarse": 1.00,
    "medium": 0.50,
    "fine":   0.25,
}
SYMMETRY_SECTORS = 28        # 28 周期对称切片（默认优先）
USE_SYMMETRY = True          # False 时为 C5 全尺寸
LINEAR_SOLVER = "mumps"      # 稳健直解法；超大模型可改 CG + 预条件

# 鼓座/基座占位参数的敏感性幅度（🔴 数据补全前的默认做法）
DRUM_PLACEHOLDER_SENSITIVITY = 0.2   # ±20%

# ============================================================
# 五、路径约定（相对路径铁律）
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
MESH_DIR = OUTPUT_DIR / "meshes"
RESULT_DIR = OUTPUT_DIR / "results"
FIGURE_DIR = OUTPUT_DIR / "figures"
DATA_DIR = OUTPUT_DIR / "data"
LEGACY_DIR = ROOT / "legacy_v1"

for _d in (OUTPUT_DIR, MESH_DIR, RESULT_DIR, FIGURE_DIR, DATA_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# geometry/ — Gmsh 几何建模与网格

规划文件（总纲 §3）：
- `dome_geometry.py`：穹顶参数化几何（球面 + 变厚度 + 五层阶梯藻井）
- `drum_geometry.py`：鼓座墙体 + 基座
- `assemble_model.py`：几何装配 + 布尔操作
- `mesh_generate.py`：网格划分 + 物理组标记（200 dome_inner / 300 dome_outer / 400 dome_base / 1000 dome_body）
- `symmetry_utils.py`：28 周期对称切片


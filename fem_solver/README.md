# fem_solver/ — FEniCSx 求解

规划文件（总纲 §3）：
- `mesh_io.py`：.msh → FEniCSx
- `function_spaces.py`：二阶矢量函数空间（CG2 × 3）
- `weak_form_elastic.py`：线弹性 UFL 弱形式
- `weak_form_nonlinear.py`：无拉伸本构（进阶）
- `boundary_conditions.py`：底部固支 + 界面粘结/摩擦
- `loads.py`：自重（密度梯度）+ 干缩（热应变类比）
- `solve_linear.py` / `solve_nonlinear.py`


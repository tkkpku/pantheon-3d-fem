#!/bin/bash
# C1 全链：几何 → P-02 验证 → C1 + E 敏感性扫描（2026-08-15）
# 输出重定向到 output/c1_run_log.txt（绕开 WSL 管道编码问题）
set -e
cd "$(dirname "$0")/.."
# 修改为你的 conda 环境 python 路径（setup_env_wsl.sh 创建的 pantheon-fem 环境）
PY=/home/tan83/miniconda3/envs/pantheon-fem/bin/python

exec > output/c1_run_log.txt 2>&1

echo "=== 1/3 几何 ==="
"$PY" geometry/minimal_dome_demo.py

echo "=== 2/3 P-02 验证 ==="
"$PY" tools/verify_p02_density.py

echo "=== 3/3 C1 + E 扫描 ==="
"$PY" fem_solver/c1_dome_selfweight.py

echo "=== ALL DONE ==="

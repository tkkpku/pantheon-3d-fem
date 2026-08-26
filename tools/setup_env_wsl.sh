#!/usr/bin/env bash
# 万神殿 3D FEM · WSL2 环境一键搭建（Ubuntu 22.04）
# 运行：bash tools/setup_env_wsl.sh
# 网络纪律：优先国内权威镜像（清华 TUNA），失败可切阿里云/官方源。
# 2026-08-11 变更：fenics-dolfinx 未上架 PyPI，改为 Miniconda + conda-forge 路线。
set -euo pipefail

cd "$(dirname "$0")/.."

HOME_DIR="${HOME:-/home/tan83}"
CONDA_BIN="$HOME_DIR/miniconda3/bin/conda"
ENV_DIR="$HOME_DIR/miniconda3/envs/pantheon-fem"
CHANNEL="https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/"

echo "[1/5] 检查 Miniconda（不存在则从清华镜像安装）"
if [ ! -x "$CONDA_BIN" ]; then
  curl -fL --retry 3 -o /tmp/miniconda.sh \
    "https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh" \
    || curl -fL --retry 3 -o /tmp/miniconda.sh \
    "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
  bash /tmp/miniconda.sh -b -p "$HOME_DIR/miniconda3"
fi
"$CONDA_BIN" --version

echo "[2/5] 配置清华 conda-forge 渠道"
"$CONDA_BIN" config --set show_channel_urls yes
"$CONDA_BIN" config --remove channels defaults >/dev/null 2>&1 || true
cat > "$HOME_DIR/.condarc" <<EOF
channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
show_channel_urls: true
EOF

echo "[3/5] 创建 conda 环境 pantheon-fem（已存在则跳过）"
if [ ! -x "$ENV_DIR/bin/python" ]; then
  "$CONDA_BIN" create -y -p "$ENV_DIR" --override-channels -c "$CHANNEL" \
    python=3.11 fenics-dolfinx=0.8.0 mpich \
    meshio pyvista numpy scipy matplotlib
fi

echo "[4/5] 补装 gmsh Python 模块（conda-forge 的 gmsh 不含 Python 绑定；走清华 PyPI）"
"$ENV_DIR/bin/pip" config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
"$ENV_DIR/bin/pip" install gmsh

echo "[5/5] 环境自检"
"$ENV_DIR/bin/python" verification/env_check.py

echo ""
echo "完成。若 env_check.py 存在 ❌，请对照 docs/tutorials/文档0 第 9 节排错。"
echo "日常激活：source $HOME_DIR/miniconda3/etc/profile.d/conda.sh && conda activate pantheon-fem"

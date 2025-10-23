#!/bin/bash
# Python 3.10.12 環境啟動腳本
# 
# 使用方式:
#   source activate_env.sh
#
# 或在 .bashrc 中添加:
#   alias activate_copilot='source /home/ai/AISecurityProject/VSCode_CopilotAutoInteraction/activate_env.sh'

echo "=========================================="
echo "正在啟動 Copilot Auto Interaction 環境"
echo "=========================================="

# 初始化 conda
source ~/anaconda3/etc/profile.d/conda.sh

# 啟動 Python 3.10.12 環境
conda activate copilot_py310

# 顯示環境資訊
echo ""
echo "✅ 環境已啟動"
echo ""
echo "📌 環境資訊:"
echo "   - Python:  $(python --version)"
echo "   - Bandit:  $(bandit --version | head -n1)"
echo "   - Semgrep: $(semgrep --version)"
echo "   - Conda 環境: copilot_py310"
echo ""
echo "=========================================="
echo "現在可以執行 python main.py 來啟動程式"
echo "=========================================="

#!/bin/bash
# 快速設定腳本 - 將環境啟動別名加入 .bashrc
#
# 使用方式:
#   bash setup_alias.sh

BASHRC_FILE="$HOME/.bashrc"
ALIAS_NAME="activate_copilot"
SCRIPT_PATH="/home/ai/AISecurityProject/VSCode_CopilotAutoInteraction/activate_env.sh"

echo "=========================================="
echo "設定 Copilot Auto Interaction 快捷別名"
echo "=========================================="

# 檢查別名是否已存在
if grep -q "alias $ALIAS_NAME=" "$BASHRC_FILE"; then
    echo ""
    echo "⚠️  別名 '$ALIAS_NAME' 已存在於 $BASHRC_FILE"
    echo ""
    echo "現有設定:"
    grep "alias $ALIAS_NAME=" "$BASHRC_FILE"
    echo ""
    read -p "是否要覆蓋? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消設定"
        exit 0
    fi
    # 移除舊的別名
    sed -i "/alias $ALIAS_NAME=/d" "$BASHRC_FILE"
fi

# 新增別名到 .bashrc
echo "" >> "$BASHRC_FILE"
echo "# Copilot Auto Interaction 環境啟動別名" >> "$BASHRC_FILE"
echo "alias $ALIAS_NAME='source $SCRIPT_PATH'" >> "$BASHRC_FILE"

echo ""
echo "✅ 別名設定成功！"
echo ""
echo "📝 已新增到: $BASHRC_FILE"
echo "🔧 別名指令: $ALIAS_NAME"
echo ""
echo "=========================================="
echo "使用方式:"
echo "=========================================="
echo ""
echo "1. 重新載入 .bashrc:"
echo "   source ~/.bashrc"
echo ""
echo "2. 啟動環境:"
echo "   $ALIAS_NAME"
echo ""
echo "3. 執行程式:"
echo "   python main.py"
echo ""
echo "=========================================="

# 詢問是否立即重新載入
read -p "是否立即重新載入 .bashrc? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "請手動執行: source ~/.bashrc"
else
    source "$BASHRC_FILE"
    echo "✅ .bashrc 已重新載入"
    echo ""
    echo "現在可以直接使用: $ALIAS_NAME"
fi

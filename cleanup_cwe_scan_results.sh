#!/bin/bash
# 清理冗餘的 cwe_scan_results 目錄

echo "清理冗餘目錄..."

# 檢查目錄是否存在
if [ -d "cwe_scan_results" ]; then
    # 檢查目錄是否為空
    if [ -z "$(ls -A cwe_scan_results)" ]; then
        echo "✓ 發現空的 cwe_scan_results 目錄，正在移除..."
        rmdir cwe_scan_results
        echo "✓ 已移除 cwe_scan_results 目錄"
    else
        echo "⚠ cwe_scan_results 目錄不為空，請手動檢查內容後決定是否刪除"
        echo "  目錄內容："
        ls -la cwe_scan_results/
    fi
else
    echo "✓ cwe_scan_results 目錄不存在（已清理或從未創建）"
fi

echo ""
echo "說明："
echo "- cwe_scan_results 是舊版設計遺留的目錄"
echo "- 現在系統使用以下目錄："
echo "  • CWE_Result/ - 統計結果（CSV 格式）"
echo "  • OriginalScanResult/ - 原始掃描結果（JSON 格式）"
echo "    ├── Bandit/"
echo "    └── Semgrep/"

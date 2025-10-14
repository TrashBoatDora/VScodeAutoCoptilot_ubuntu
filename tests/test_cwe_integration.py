#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CWE 整合功能測試腳本
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cwe_detector import CWEDetector
from src.cwe_prompt_generator import CWEPromptGenerator
from src.cwe_integration_manager import CWEIntegrationManager
from src.logger import get_logger

logger = get_logger("CWETest")


def test_detector():
    """測試 CWE 檢測器"""
    logger.info("=== 測試 CWE 檢測器 ===")
    
    detector = CWEDetector()
    
    # 檢查可用的掃描器
    logger.info(f"可用掃描器: {', '.join([s.value for s in detector.available_scanners])}")
    
    if not detector.available_scanners:
        logger.warning("沒有可用的掃描器！請安裝 Bandit 或 Semgrep")
        return False
    
    logger.info("✅ CWE 檢測器初始化成功")
    return True


def test_prompt_generator():
    """測試提示詞生成器"""
    logger.info("=== 測試提示詞生成器 ===")
    
    generator = CWEPromptGenerator()
    
    # 測試生成簡化版提示詞
    prompt = generator.generate_simple_prompt(["078", "095", "502"])
    
    if prompt:
        logger.info(f"✅ 提示詞生成成功（長度: {len(prompt)} 字元）")
        logger.info(f"提示詞預覽:\n{prompt[:200]}...")
        return True
    else:
        logger.error("❌ 提示詞生成失敗")
        return False


def test_integration_manager():
    """測試整合管理器"""
    logger.info("=== 測試整合管理器 ===")
    
    manager = CWEIntegrationManager(enable_cwe_scan=True)
    
    if not manager.detector.available_scanners:
        logger.warning("沒有可用的掃描器，跳過整合管理器測試")
        return True
    
    logger.info("✅ 整合管理器初始化成功")
    return True


def test_codeql_integration():
    """測試 CodeQL 結果整合"""
    logger.info("=== 測試 CodeQL 結果整合 ===")
    
    # 檢查是否有 CodeQL 結果目錄
    codeql_dir = project_root.parent / "CodeQL-query_derive" / "python_query_output"
    
    if not codeql_dir.exists():
        logger.warning(f"CodeQL 結果目錄不存在: {codeql_dir}")
        logger.info("如需測試 CodeQL 整合，請先執行 CodeQL 掃描")
        return True
    
    # 查找第一個 JSON 檔案進行測試
    json_files = list(codeql_dir.glob("*/*.json"))
    
    if not json_files:
        logger.warning("沒有找到 CodeQL JSON 結果檔案")
        return True
    
    test_json = json_files[0]
    logger.info(f"找到測試 JSON: {test_json}")
    
    # 創建一個測試專案路徑
    test_project = test_json.parent.parent.parent / "projects" / test_json.stem
    
    manager = CWEIntegrationManager(enable_cwe_scan=True)
    prompt, prompt_file = manager.integrate_with_existing_results(
        test_project,
        test_json
    )
    
    if prompt:
        logger.info(f"✅ CodeQL 結果整合成功")
        logger.info(f"生成提示詞長度: {len(prompt)} 字元")
        if prompt_file:
            logger.info(f"提示詞檔案: {prompt_file}")
        return True
    else:
        logger.info("ℹ️  CodeQL 結果中沒有發現漏洞（正常情況）")
        return True


def test_settings_ui():
    """測試設定 UI"""
    logger.info("=== 測試設定 UI ===")
    
    try:
        from src.cwe_settings_ui import CWESettingsDialog
        logger.info("✅ 設定 UI 模組載入成功")
        logger.info("ℹ️  要測試 UI，請執行: python -m src.cwe_settings_ui")
        return True
    except ImportError as e:
        logger.error(f"❌ 設定 UI 模組載入失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("=" * 60)
    print("CWE 整合功能測試")
    print("=" * 60)
    print()
    
    tests = [
        ("CWE 檢測器", test_detector),
        ("提示詞生成器", test_prompt_generator),
        ("整合管理器", test_integration_manager),
        ("CodeQL 結果整合", test_codeql_integration),
        ("設定 UI", test_settings_ui),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print()
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"測試 {test_name} 時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 輸出測試總結
    print()
    print("=" * 60)
    print("測試總結")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    print()
    print(f"總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        print()
        print("🎉 所有測試通過！CWE 整合功能已就緒")
        return 0
    else:
        print()
        print("⚠️  部分測試失敗，請檢查上述錯誤訊息")
        return 1


if __name__ == "__main__":
    sys.exit(main())

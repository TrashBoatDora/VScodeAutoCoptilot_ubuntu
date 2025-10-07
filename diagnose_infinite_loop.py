#!/usr/bin/env python3
"""
診斷無限循環問題的腳本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.copilot_handler import CopilotHandler
from src.settings_manager import SettingsManager
from config.config import config

def diagnose_infinite_loop():
    """診斷無限循環問題"""
    print("=== 診斷無限循環問題 ===\n")
    
    # 檢查設定狀態
    handler = CopilotHandler()
    interaction_settings = handler._load_interaction_settings()
    
    print("🔍 當前互動設定:")
    for key, value in interaction_settings.items():
        print(f"  {key}: {value}")
    
    # 檢查提示詞來源模式
    prompt_source_mode = interaction_settings.get("prompt_source_mode", config.PROMPT_SOURCE_MODE)
    print(f"\n📋 提示詞來源模式: {prompt_source_mode}")
    
    # 檢查專案提示詞
    project_path = "/home/ai/AISecurityProject/VSCode_CopilotAutoInteraction/projects/testpro"
    
    if prompt_source_mode == "project":
        print("\n⚠️  使用專案專用提示詞模式")
        
        # 載入專案提示詞
        prompt_lines = handler.load_project_prompt_lines(project_path)
        print(f"  專案提示詞行數: {len(prompt_lines) if prompt_lines else 0}")
        
        if prompt_lines:
            for i, line in enumerate(prompt_lines, 1):
                print(f"    第{i}行: {line}")
        
        # 檢查多輪邏輯
        max_rounds = interaction_settings.get("max_rounds", 3)
        print(f"\n🔄 多輪互動設定:")
        print(f"  最大輪數: {max_rounds}")
        print(f"  互動啟用: {interaction_settings.get('interaction_enabled', True)}")
        
        print(f"\n🧮 預計執行次數:")
        print(f"  每輪行數: {len(prompt_lines) if prompt_lines else 0}")
        print(f"  總輪數: {max_rounds}")
        print(f"  總執行次數: {(len(prompt_lines) if prompt_lines else 0) * max_rounds}")
        
        # 模擬執行流程
        print(f"\n📝 模擬執行流程:")
        for round_num in range(1, max_rounds + 1):
            print(f"  第{round_num}輪:")
            if prompt_lines:
                for line_num, line in enumerate(prompt_lines, 1):
                    print(f"    第{round_num}輪第{line_num}行: {line}")
            print(f"    --> 輪次間停頓...")
        
        print(f"\n✅ 執行應該在第{max_rounds}輪後停止")
        
    else:
        print("\n✅ 使用全域提示詞模式")
        
        # 檢查全域提示詞
        print(f"  第1輪提示詞檔案存在: {os.path.exists('prompts/prompt1.txt')}")
        print(f"  第2輪提示詞檔案存在: {os.path.exists('prompts/prompt2.txt')}")
        
        max_rounds = interaction_settings.get("max_rounds", 3)
        print(f"\n🔄 多輪互動設定:")
        print(f"  最大輪數: {max_rounds}")
        print(f"  每輪執行1次")
        print(f"  總執行次數: {max_rounds}")

def check_ui_settings():
    """檢查UI設定是否可能導致問題"""
    print("\n=== 檢查UI設定 ===")
    
    # 檢查是否有儲存的互動設定
    settings_file = "config/interaction_settings.json"
    
    if os.path.exists(settings_file):
        print(f"✅ 發現互動設定檔案: {settings_file}")
        
        import json
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                ui_settings = json.load(f)
            
            print("📄 UI儲存的設定:")
            for key, value in ui_settings.items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            print(f"❌ 讀取設定檔案失敗: {e}")
    else:
        print(f"ℹ️  沒有發現互動設定檔案: {settings_file}")
        print("   系統將使用預設值")

def check_recent_execution():
    """檢查最近的執行記錄"""
    print("\n=== 檢查最近執行記錄 ===")
    
    # 檢查執行結果
    result_path = "ExecutionResult/Success/testpro"
    
    if os.path.exists(result_path):
        print(f"✅ 發現執行結果: {result_path}")
        
        # 列出輪數資料夾
        round_dirs = [d for d in os.listdir(result_path) if d.startswith('第') and d.endswith('輪')]
        round_dirs.sort(key=lambda x: int(x.replace('第', '').replace('輪', '')))
        
        print(f"📊 執行輪數統計:")
        for round_dir in round_dirs:
            full_path = os.path.join(result_path, round_dir)
            files = [f for f in os.listdir(full_path) if f.endswith('.md')]
            print(f"  {round_dir}: {len(files)} 個檔案")
        
        total_rounds = len(round_dirs)
        print(f"\n🔢 實際執行輪數: {total_rounds}")
        
        # 檢查是否超出預期
        handler = CopilotHandler()
        settings = handler._load_interaction_settings()
        expected_rounds = settings.get("max_rounds", 3)
        
        if total_rounds > expected_rounds:
            print(f"⚠️  實際輪數({total_rounds})超出設定輪數({expected_rounds}) - 可能有無限循環問題！")
        else:
            print(f"✅ 實際輪數({total_rounds})符合設定輪數({expected_rounds})")
            
    else:
        print(f"ℹ️  沒有發現執行結果: {result_path}")

if __name__ == "__main__":
    diagnose_infinite_loop()
    check_ui_settings()
    check_recent_execution()
    
    print(f"\n=== 建議修復方案 ===")
    print("1. 檢查 UI 中的「提示詞來源」設定是否被設為「專案專用提示詞」")
    print("2. 確認最大互動輪數設定是否合理")
    print("3. 檢查是否有中止條件被忽略")
    print("4. 考慮添加更嚴格的循環保護機制")
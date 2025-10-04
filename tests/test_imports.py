# -*- coding: utf-8 -*-
"""
測試所有模組的導入是否正常
"""

import sys
from pathlib import Path

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent / 'config'))

def test_imports():
    """測試所有導入是否正常工作"""
    print("開始測試模組導入...")
    
    try:
        # 測試 config
        try:
            from config.config import config
        except ImportError:
            from config import config
        print("✅ config 模組導入成功")
    except Exception as e:
        print(f"❌ config 模組導入失敗: {e}")
        return False
        
    try:
        # 測試 logger
        try:
            from src.logger import get_logger
        except ImportError:
            from logger import get_logger
        print("✅ logger 模組導入成功")
    except Exception as e:
        print(f"❌ logger 模組導入失敗: {e}")
        return False
        
    try:
        # 測試 copilot_handler
        try:
            from src.copilot_handler import CopilotHandler
        except ImportError:
            from copilot_handler import CopilotHandler
        print("✅ copilot_handler 模組導入成功")
    except Exception as e:
        print(f"❌ copilot_handler 模組導入失敗: {e}")
        return False
        
    try:
        # 測試 vscode_controller
        try:
            from src.vscode_controller import VSCodeController
        except ImportError:
            from vscode_controller import VSCodeController
        print("✅ vscode_controller 模組導入成功")
    except Exception as e:
        print(f"❌ vscode_controller 模組導入失敗: {e}")
        return False
        
    try:
        # 測試 interaction_settings_ui
        try:
            from src.interaction_settings_ui import InteractionSettingsUI
        except ImportError:
            from interaction_settings_ui import InteractionSettingsUI
        print("✅ interaction_settings_ui 模組導入成功")
    except Exception as e:
        print(f"❌ interaction_settings_ui 模組導入失敗: {e}")
        return False
        
    try:
        # 測試創建 CopilotHandler 實例
        logger = get_logger("test")
        handler = CopilotHandler()
        print("✅ CopilotHandler 實例創建成功")
    except Exception as e:
        print(f"❌ CopilotHandler 實例創建失敗: {e}")
        return False
        
    print("所有模組導入測試完成！")
    return True

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n🎉 所有測試通過！導入問題已修復。")
    else:
        print("\n⚠️  仍有部分導入問題需要解決。")
import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
from pathlib import Path
import sys
import threading

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent.parent))

from config.config import config
from src.settings_manager import settings_manager

class UIManager:
    """UI 管理器 - 提供簡單的選項選擇介面"""
    
    def __init__(self):
        """初始化 UI 管理器"""
        self.reset_selected = False
        self.smart_wait_selected = True
        self.choice_made = False
        self.selected_projects = set()  # 使用者選擇的專案
        self.clean_history = True  # 是否清理歷史記錄
        
    def show_options_dialog(self) -> tuple:
        """
        顯示選項對話框，讓使用者選擇執行選項
        
        Returns:
            tuple: (選中的專案集合, 是否使用智能等待, 是否清理歷史)
        """
        root = tk.Tk()
        root.title("自動化腳本設定")
        root.geometry("480x500")  # 調整視窗尺寸
        root.resizable(False, False)  # 固定視窗大小，防止使用者調整大小
        
        # 設定視窗樣式
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 10))
        style.configure("TCheckbutton", font=("Arial", 10))
        style.configure("TLabel", font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        
        # 創建框架
        frame = ttk.Frame(root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_label = ttk.Label(frame, text="VSCode Copilot Chat 自動化腳本設定", style="Header.TLabel")
        title_label.pack(pady=10)
        
        # 專案選擇區域
        project_frame = ttk.LabelFrame(frame, text="選擇要處理的專案", padding=10)
        project_frame.pack(fill=tk.X, pady=10)
        
        # 專案選擇狀態顯示
        self.project_status_label = ttk.Label(
            project_frame,
            text="尚未選擇專案",
            foreground="gray"
        )
        self.project_status_label.pack(pady=5)
        
        # 瀏覽專案按鈕
        def browse_projects():
            # 導入專案選擇器
            from src.project_selector_ui import show_project_selector
            
            # 暫時隱藏主視窗
            root.withdraw()
            
            # 顯示專案選擇器
            projects_dir = Path(__file__).parent.parent / "projects"
            selected, clean, cancelled = show_project_selector(projects_dir)
            
            # 恢復主視窗
            root.deiconify()
            
            if not cancelled and selected:
                self.selected_projects = selected
                self.clean_history = clean
                
                # 更新狀態顯示
                count = len(selected)
                status_text = f"✓ 已選擇 {count} 個專案（將自動清理執行記錄）"
                
                self.project_status_label.config(
                    text=status_text,
                    foreground="green"
                )
            elif not cancelled:
                # 使用者確認但沒選擇任何專案
                messagebox.showwarning("未選擇專案", "請選擇至少一個專案！")
        
        browse_btn = ttk.Button(
            project_frame,
            text="📁 瀏覽專案",
            command=browse_projects,
            width=20
        )
        browse_btn.pack(pady=5)
        
        # 等待模式選擇
        wait_frame = ttk.LabelFrame(frame, text="選擇等待 Copilot 回應的方式")
        wait_frame.pack(fill=tk.X, pady=10)
        
        wait_var = tk.BooleanVar(value=True)
        smart_radio = ttk.Radiobutton(
            wait_frame, 
            text="智能等待 (檢查回應是否完整，建議選項)", 
            variable=wait_var, 
            value=True
        )
        smart_radio.pack(anchor=tk.W, padx=10, pady=5)
        
        fixed_radio = ttk.Radiobutton(
            wait_frame, 
            text="固定時間等待 (使用設定的固定秒數)", 
            variable=wait_var, 
            value=False
        )
        fixed_radio.pack(anchor=tk.W, padx=10, pady=5)
        
        # 說明文字
        description = """
        • 瀏覽專案: 
          選擇要處理的專案，選定後將自動清理執行記錄
        • 智能等待: 
          檢查 Copilot 回應是否完整，可能比較準確但稍慢
        • 固定時間等待: 
          使用設定的固定時間等待，較快但可能不準確
        """
        desc_label = ttk.Label(frame, text=description, wraplength=430)
        desc_label.pack(pady=10, fill=tk.X)
        
        # 按鈕
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10, side=tk.BOTTOM)
        
        def on_start():
            # 檢查是否已選擇專案
            if not self.selected_projects:
                messagebox.showwarning(
                    "未選擇專案",
                    "請先點擊「瀏覽專案」按鈕選擇要處理的專案！"
                )
                return
            
            self.smart_wait_selected = wait_var.get()
            self.choice_made = True
            root.destroy()
        
        def on_cancel():
            print("使用者關閉對話框，結束腳本執行")
            root.destroy()
            sys.exit(0)
        
        start_btn = ttk.Button(btn_frame, text="開始執行", command=on_start, width=15)
        start_btn.pack(side=tk.LEFT, padx=10, expand=True)
        
        cancel_btn = ttk.Button(btn_frame, text="取消", command=on_cancel, width=15)
        cancel_btn.pack(side=tk.RIGHT, padx=10, expand=True)
        
        # 顯示對話框並等待
        root.protocol("WM_DELETE_WINDOW", on_cancel)  # 處理視窗關閉
        root.mainloop()
        
        # 檢查是否做出選擇
        if not self.choice_made:
            sys.exit(0)
            
        return (self.selected_projects, self.smart_wait_selected, self.clean_history)
    
    def execute_reset_if_needed(self, should_reset: bool) -> bool:
        """
        如果需要，執行專案狀態重置（已棄用，保留以維持相容性）
        
        Args:
            should_reset: 是否需要重置
            
        Returns:
            bool: 執行是否成功
        """
        if not should_reset:
            return True
            
        try:
            # 直接執行重置腳本，不使用多執行緒
            reset_script = Path(__file__).parent.parent / "src" / "ProjectStatusReset.py"
            result = subprocess.run(
                [sys.executable, str(reset_script)], 
                capture_output=True, 
                text=True
            )
            
            # 輸出重置結果到控制台，而不是使用訊息框
            if "所有專案狀態已重設為 pending" in result.stdout:
                print("✅ 所有專案狀態已重設為 pending，並清除執行結果")
                return True
            else:
                print(f"⚠️ 重置訊息: {result.stdout}")
                return True
                
        except Exception as e:
            print(f"❌ 重置專案狀態時發生錯誤: {str(e)}")
            return False
    
    def clean_project_history(self, project_names: set) -> bool:
        """
        清理指定專案的執行記錄和結果
        
        Args:
            project_names: 要清理的專案名稱集合
            
        Returns:
            bool: 清理是否成功
        """
        if not project_names:
            return True
        
        try:
            import shutil
            from datetime import datetime
            
            script_root = Path(__file__).parent.parent
            
            print(f"\n🧹 開始清理 {len(project_names)} 個專案的執行記錄...")
            
            # 要清理的目錄列表
            cleanup_locations = []
            
            for project_name in project_names:
                # ExecutionResult 相關
                success_dir = script_root / "ExecutionResult" / "Success" / project_name
                if success_dir.exists():
                    cleanup_locations.append(("執行結果", success_dir))
                
                # AutomationLog
                log_dir = script_root / "ExecutionResult" / "AutomationLog"
                if log_dir.exists():
                    for log_file in log_dir.glob(f"{project_name}*.txt"):
                        cleanup_locations.append(("自動化日誌", log_file))
                
                # CWE 掃描結果
                cwe_result_dirs = [
                    script_root / "CWE_Result",
                    script_root / "cwe_scan_results"
                ]
                
                for cwe_dir in cwe_result_dirs:
                    if cwe_dir.exists():
                        # 檢查所有 CWE 類型目錄
                        for cwe_type_dir in cwe_dir.glob("CWE-*"):
                            # 查找該專案的掃描結果
                            for result_file in cwe_type_dir.glob(f"{project_name}*"):
                                cleanup_locations.append(("CWE掃描結果", result_file))
            
            # 建立備份（可選）
            if cleanup_locations:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = script_root / f"backup_history_{timestamp}"
                backup_dir.mkdir(exist_ok=True)
                
                print(f"📦 建立備份到: {backup_dir}")
                
                # 執行清理
                cleaned_count = 0
                for desc, path in cleanup_locations:
                    try:
                        # 備份
                        if path.is_file():
                            backup_path = backup_dir / desc / path.name
                            backup_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(path, backup_path)
                            # 刪除
                            path.unlink()
                        elif path.is_dir():
                            backup_path = backup_dir / desc / path.name
                            backup_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copytree(path, backup_path)
                            # 刪除
                            shutil.rmtree(path)
                        
                        print(f"  ✅ 已清理: {desc} - {path.name}")
                        cleaned_count += 1
                    except Exception as e:
                        print(f"  ⚠️  清理失敗: {desc} - {path.name}: {e}")
                
                print(f"\n✅ 清理完成！共清理 {cleaned_count} 個項目")
                print(f"📦 備份位置: {backup_dir}\n")
            else:
                print("ℹ️  沒有需要清理的記錄\n")
            
            return True
            
        except Exception as e:
            print(f"❌ 清理執行記錄時發生錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

# 創建全域實例
ui_manager = UIManager()

# 便捷函數
def show_options_dialog() -> tuple:
    """顯示選項對話框的便捷函數"""
    return ui_manager.show_options_dialog()

def execute_reset_if_needed(should_reset: bool) -> bool:
    """執行重置的便捷函數"""
    return ui_manager.execute_reset_if_needed(should_reset)
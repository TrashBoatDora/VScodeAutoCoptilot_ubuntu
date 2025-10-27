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
        self.artificial_suicide_enabled = False  # 是否啟用 Artificial Suicide 模式
        self.artificial_suicide_rounds = 3  # Artificial Suicide 攻擊輪數
        
    def show_options_dialog(self) -> tuple:
        """
        顯示選項對話框，讓使用者選擇執行選項
        
        Returns:
            tuple: (選中的專案集合, 是否使用智能等待, 是否清理歷史, 是否啟用Artificial Suicide, Artificial Suicide輪數)
        """
        root = tk.Tk()
        root.title("自動化腳本設定")
        root.geometry("480x650")  # 增加視窗高度以容納新選項
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
        
        # === Artificial Suicide 攻擊模式設定 ===
        as_frame = ttk.LabelFrame(frame, text="🎯 Artificial Suicide 攻擊模式", padding=10)
        as_frame.pack(fill=tk.X, pady=10)
        
        # 啟用 Artificial Suicide 勾選框
        as_var = tk.BooleanVar(value=False)
        as_checkbox = ttk.Checkbutton(
            as_frame,
            text="啟用 Artificial Suicide 攻擊模式",
            variable=as_var,
            command=lambda: self._update_as_state(as_var.get(), as_rounds_spinbox, wait_frame)
        )
        as_checkbox.pack(anchor=tk.W, pady=5)
        
        # 攻擊輪數設定
        as_rounds_frame = ttk.Frame(as_frame)
        as_rounds_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(as_rounds_frame, text="攻擊輪數:").pack(side=tk.LEFT, padx=(20, 5))
        as_rounds_var = tk.IntVar(value=3)
        as_rounds_spinbox = ttk.Spinbox(
            as_rounds_frame,
            from_=1,
            to=10,
            textvariable=as_rounds_var,
            width=5,
            state="disabled"  # 初始為禁用
        )
        as_rounds_spinbox.pack(side=tk.LEFT)
        
        # Artificial Suicide 說明
        as_desc = """說明：
• Artificial Suicide 模式會測試 Copilot 是否會生成不安全的程式碼
• 啟用此模式將自動跳過「互動設定」，使用專案專用 prompt.txt
• 每輪包含兩道程序：第1道誘導命名修改，第2道實作並掃描"""
        
        as_desc_label = ttk.Label(as_frame, text=as_desc, wraplength=430, foreground="gray")
        as_desc_label.pack(pady=5, fill=tk.X)
        
        # 儲存變數以供回調使用
        self._as_var = as_var
        self._as_rounds_var = as_rounds_var
        
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
            self.artificial_suicide_enabled = as_var.get()
            self.artificial_suicide_rounds = as_rounds_var.get()
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
            
        return (
            self.selected_projects, 
            self.smart_wait_selected, 
            self.clean_history,
            self.artificial_suicide_enabled,
            self.artificial_suicide_rounds
        )
    
    def _update_as_state(self, enabled: bool, spinbox, wait_frame):
        """
        更新 Artificial Suicide 狀態
        
        Args:
            enabled: 是否啟用
            spinbox: 輪數選擇器
            wait_frame: 等待模式框架
        """
        if enabled:
            # 啟用輪數設定
            spinbox.configure(state="normal")
            # 禁用等待模式選擇（Artificial Suicide 有自己的邏輯）
            for child in wait_frame.winfo_children():
                if isinstance(child, ttk.Radiobutton):
                    child.configure(state="disabled")
        else:
            # 禁用輪數設定
            spinbox.configure(state="disabled")
            # 啟用等待模式選擇
            for child in wait_frame.winfo_children():
                if isinstance(child, ttk.Radiobutton):
                    child.configure(state="normal")
    
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
        清理指定專案的執行記錄和結果（直接刪除，不備份）
        
        清理範圍：
        - ExecutionResult/Success/{專案名稱}/
        - ExecutionResult/AutomationLog/{專案名稱}*.txt
        - ExecutionResult/AutomationReport/{專案名稱}*.json
        - OriginalScanResult/Bandit/CWE-*/{專案名稱}/ (完整目錄)
        - OriginalScanResult/Semgrep/CWE-*/{專案名稱}/ (完整目錄)
        - CWE_Result/CWE-*/Bandit/{專案名稱}/ (完整目錄)
        - CWE_Result/CWE-*/Semgrep/{專案名稱}/ (完整目錄)
        - cwe_scan_results/CWE-*/{專案名稱}*.csv (舊版，如果存在)
        
        Args:
            project_names: 要清理的專案名稱集合
            
        Returns:
            bool: 清理是否成功
        """
        if not project_names:
            return True
        
        try:
            import shutil
            
            script_root = Path(__file__).parent.parent
            
            print(f"\n🧹 開始清理 {len(project_names)} 個專案的執行記錄（不備份）...")
            
            # 統計清理數量
            cleaned_count = 0
            total_size = 0  # 釋放的空間（bytes）
            
            for project_name in project_names:
                print(f"\n📂 清理專案: {project_name}")
                
                # 1. ExecutionResult/Success/{專案名稱}/
                success_dir = script_root / "ExecutionResult" / "Success" / project_name
                if success_dir.exists():
                    try:
                        # 計算大小
                        dir_size = sum(f.stat().st_size for f in success_dir.rglob('*') if f.is_file())
                        total_size += dir_size
                        
                        shutil.rmtree(success_dir)
                        print(f"  ✅ 已刪除執行結果目錄 ({dir_size / 1024:.2f} KB)")
                        cleaned_count += 1
                    except Exception as e:
                        print(f"  ⚠️  刪除執行結果失敗: {e}")
                
                # 2. AutomationLog
                log_dir = script_root / "ExecutionResult" / "AutomationLog"
                if log_dir.exists():
                    for log_file in log_dir.glob(f"{project_name}*.txt"):
                        try:
                            file_size = log_file.stat().st_size
                            total_size += file_size
                            
                            log_file.unlink()
                            print(f"  ✅ 已刪除日誌: {log_file.name} ({file_size / 1024:.2f} KB)")
                            cleaned_count += 1
                        except Exception as e:
                            print(f"  ⚠️  刪除日誌失敗: {log_file.name}: {e}")
                
                # 3. AutomationReport
                report_dir = script_root / "ExecutionResult" / "AutomationReport"
                if report_dir.exists():
                    for report_file in report_dir.glob(f"{project_name}*.json"):
                        try:
                            file_size = report_file.stat().st_size
                            total_size += file_size
                            
                            report_file.unlink()
                            print(f"  ✅ 已刪除報告: {report_file.name} ({file_size / 1024:.2f} KB)")
                            cleaned_count += 1
                        except Exception as e:
                            print(f"  ⚠️  刪除報告失敗: {report_file.name}: {e}")
                
                # 4. OriginalScanResult (原始掃描結果 - 完整專案目錄)
                original_scan_dirs = [
                    script_root / "OriginalScanResult" / "Bandit",
                    script_root / "OriginalScanResult" / "Semgrep"
                ]
                
                for original_scan_dir in original_scan_dirs:
                    if not original_scan_dir.exists():
                        continue
                    
                    scanner_name = original_scan_dir.name
                    
                    # 檢查所有 CWE 類型目錄
                    for cwe_type_dir in original_scan_dir.glob("CWE-*"):
                        if not cwe_type_dir.is_dir():
                            continue
                        
                        # 刪除整個專案目錄
                        project_dir = cwe_type_dir / project_name
                        if project_dir.exists():
                            try:
                                # 計算大小
                                dir_size = sum(f.stat().st_size for f in project_dir.rglob('*') if f.is_file())
                                total_size += dir_size
                                
                                shutil.rmtree(project_dir)
                                print(f"  ✅ 已刪除{scanner_name}原始掃描: OriginalScanResult/{scanner_name}/{cwe_type_dir.name}/{project_name}/ ({dir_size / 1024:.2f} KB)")
                                cleaned_count += 1
                            except Exception as e:
                                print(f"  ⚠️  刪除{scanner_name}原始掃描失敗: {e}")
                
                # 5. CWE 掃描結果（支援新的 Bandit/Semgrep 分離結構 - 完整專案目錄）
                cwe_result_dirs = [
                    script_root / "CWE_Result",
                    script_root / "cwe_scan_results"
                ]
                
                for cwe_dir in cwe_result_dirs:
                    if not cwe_dir.exists():
                        continue
                    
                    # 檢查所有 CWE 類型目錄
                    for cwe_type_dir in cwe_dir.glob("CWE-*"):
                        if not cwe_type_dir.is_dir():
                            continue
                        
                        # 清理根目錄的掃描結果（舊格式 - 單個 CSV 檔案）
                        for result_file in cwe_type_dir.glob(f"{project_name}*.csv"):
                            try:
                                file_size = result_file.stat().st_size
                                total_size += file_size
                                
                                result_file.unlink()
                                print(f"  ✅ 已刪除CWE掃描: {cwe_type_dir.name}/{result_file.name} ({file_size / 1024:.2f} KB)")
                                cleaned_count += 1
                            except Exception as e:
                                print(f"  ⚠️  刪除CWE掃描失敗: {result_file.name}: {e}")
                        
                        # 清理 Bandit 子資料夾（新格式 - 完整專案目錄）
                        bandit_dir = cwe_type_dir / "Bandit" / project_name
                        if bandit_dir.exists():
                            try:
                                # 計算大小
                                dir_size = sum(f.stat().st_size for f in bandit_dir.rglob('*') if f.is_file())
                                total_size += dir_size
                                
                                shutil.rmtree(bandit_dir)
                                print(f"  ✅ 已刪除Bandit結果目錄: {cwe_type_dir.name}/Bandit/{project_name}/ ({dir_size / 1024:.2f} KB)")
                                cleaned_count += 1
                            except Exception as e:
                                print(f"  ⚠️  刪除Bandit結果目錄失敗: {e}")
                        
                        # 清理 Semgrep 子資料夾（新格式 - 完整專案目錄）
                        semgrep_dir = cwe_type_dir / "Semgrep" / project_name
                        if semgrep_dir.exists():
                            try:
                                # 計算大小
                                dir_size = sum(f.stat().st_size for f in semgrep_dir.rglob('*') if f.is_file())
                                total_size += dir_size
                                
                                shutil.rmtree(semgrep_dir)
                                print(f"  ✅ 已刪除Semgrep結果目錄: {cwe_type_dir.name}/Semgrep/{project_name}/ ({dir_size / 1024:.2f} KB)")
                                cleaned_count += 1
                            except Exception as e:
                                print(f"  ⚠️  刪除Semgrep結果目錄失敗: {e}")
            
            # 輸出總結
            print(f"\n{'='*60}")
            print(f"✅ 清理完成！")
            print(f"{'='*60}")
            print(f"📊 清理統計:")
            print(f"  - 已清理項目: {cleaned_count} 個")
            print(f"  - 釋放空間: {total_size / 1024 / 1024:.2f} MB")
            print(f"  - 清理專案: {len(project_names)} 個")
            print(f"{'='*60}\n")
            
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
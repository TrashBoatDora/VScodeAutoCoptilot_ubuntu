# -*- coding: utf-8 -*-
"""
Hybrid UI Automation Script - 主控制腳本
整合所有模組，實作完整的自動化流程控制
"""

import time
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

# 導入所有模組
from config.config import config
from src.logger import get_logger, create_project_logger
from src.project_manager import ProjectManager, ProjectInfo
from src.vscode_controller import VSCodeController
from src.copilot_handler import CopilotHandler
from src.image_recognition import ImageRecognition
from src.ui_manager import UIManager
from src.error_handler import (
    ErrorHandler, RecoveryManager,
    AutomationError, ErrorType, RecoveryAction
)
from src.cwe_scan_manager import CWEScanManager
from src.cwe_scan_ui import show_cwe_scan_settings

class HybridUIAutomationScript:
    """混合式 UI 自動化腳本主控制器"""
    
    def __init__(self):
        """初始化主控制器"""
        self.logger = get_logger("MainController")
        
        # 初始化各個模組
        self.project_manager = ProjectManager()
        self.vscode_controller = VSCodeController()
        self.error_handler = ErrorHandler()
        self.copilot_handler = CopilotHandler(
            self.error_handler, 
            interaction_settings=None,
            cwe_scan_manager=None,
            cwe_scan_settings=None
        )  # 初始化時傳入基本參數
        self.image_recognition = ImageRecognition()
        self.recovery_manager = RecoveryManager()
        self.ui_manager = UIManager()
        self.cwe_scan_manager = None  # CWE 掃描管理器（按需初始化）
        
        # 執行選項
        self.use_smart_wait = True  # 預設使用智能等待
        self.interaction_settings = None  # 儲存互動設定
        self.cwe_scan_settings = None  # CWE 掃描設定
        
        # 執行統計
        self.total_projects = 0
        self.processed_projects = 0
        self.successful_projects = 0
        self.failed_projects = 0
        self.skipped_projects = 0
        self.start_time = None
        
        self.logger.info("混合式 UI 自動化腳本初始化完成")
    
    def run(self) -> bool:
        """
        執行完整的自動化流程
        
        Returns:
            bool: 執行是否成功
        """
        try:
            self.start_time = time.time()
            self.logger.create_separator("開始執行自動化腳本")
            
            # 顯示選項對話框（包含專案選擇）
            selected_projects, self.use_smart_wait, clean_history = self.ui_manager.show_options_dialog()
            
            # 如果需要清理歷史記錄
            if clean_history and selected_projects:
                self.logger.info(f"清理 {len(selected_projects)} 個專案的執行記錄")
                if not self.ui_manager.clean_project_history(selected_projects):
                    self.logger.error("清理執行記錄失敗")
                    return False
            
            # 每次執行都顯示互動設定選項
            self._show_interaction_settings_dialog()
            
            # 顯示 CWE 掃描設定選項
            self._show_cwe_scan_settings_dialog()
            
            self.logger.info(f"使用者選擇{'啟用' if self.use_smart_wait else '停用'}智能等待功能")
            self.logger.info(f"選定處理的專案: {', '.join(selected_projects)}")
            
            # 前置檢查
            if not self._pre_execution_checks():
                return False
            
            # 掃描專案
            projects = self.project_manager.scan_projects()
            if not projects:
                self.logger.error("沒有找到任何專案，結束執行")
                return False
            
            # 過濾出使用者選定的專案
            selected_project_list = [
                p for p in projects if p.name in selected_projects
            ]
            
            if not selected_project_list:
                self.logger.error("選定的專案不存在或無法讀取")
                return False
            
            self.total_projects = len(selected_project_list)
            self.logger.info(f"將處理 {self.total_projects} 個選定的專案")
            
            # 執行所有選定的專案
            if not self._process_all_projects(selected_project_list):
                self.logger.warning("專案處理過程中發生錯誤")
            
            # 檢查是否收到中斷請求
            if self.error_handler.emergency_stop_requested:
                self.logger.warning("收到中斷請求，停止處理")
            
            self.logger.info("所有專案處理完成")
            
            # 生成最終報告
            if not self.error_handler.emergency_stop_requested:
                self._generate_final_report()
            
            return True
            
        except KeyboardInterrupt:
            self.logger.warning("收到 Ctrl+C 中斷請求")
            self.error_handler.emergency_stop_requested = True
            return False
        except Exception as e:
            recovery_action = self.error_handler.handle_error(e, "主流程執行")
            if recovery_action == RecoveryAction.ABORT:
                self.logger.critical("主流程執行失敗，中止自動化")
                return False
            else:
                self.logger.warning("主流程遇到錯誤但嘗試繼續執行")
                return False
        
        finally:
            # 清理環境
            self._cleanup()
    
    def _show_interaction_settings_dialog(self):
        """顯示互動設定對話框"""
        try:
            from src.interaction_settings_ui import show_interaction_settings
            self.logger.info("顯示多輪互動設定介面")
            settings = show_interaction_settings()
            
            if settings is None:
                # 使用者取消了設定
                self.logger.info("使用者取消了互動設定，結束腳本執行")
                sys.exit(0)  # 直接退出腳本
            else:
                # 儲存設定並重新初始化 CopilotHandler（加入 CWE 掃描參數）
                self.interaction_settings = settings
                self.copilot_handler = CopilotHandler(
                    self.error_handler, 
                    settings,
                    self.cwe_scan_manager,
                    self.cwe_scan_settings
                )
                self.logger.info(f"本次執行的互動設定: {settings}")
                
        except Exception as e:
            self.logger.error(f"顯示互動設定時發生錯誤: {e}")
            # 發生錯誤時也退出腳本
            sys.exit(1)
    
    def _show_cwe_scan_settings_dialog(self):
        """顯示 CWE 掃描設定對話框"""
        try:
            self.logger.info("顯示 CWE 掃描設定介面")
            
            # 載入預設設定
            default_settings = {
                "enabled": False,
                "cwe_type": "022",  # 預設為 CWE-022
                "output_dir": str(Path("./CWE_Result").absolute())
            }
            
            settings = show_cwe_scan_settings(default_settings)
            
            if settings is None:
                # 使用者取消了設定
                self.logger.info("使用者取消了 CWE 掃描設定，結束腳本執行")
                sys.exit(0)
            else:
                # 儲存設定
                self.cwe_scan_settings = settings
                
                # 如果啟用了掃描，初始化掃描管理器
                if settings["enabled"]:
                    output_dir = Path(settings["output_dir"])
                    self.cwe_scan_manager = CWEScanManager(output_dir)
                    self.logger.info(f"✅ CWE 掃描已啟用 (類型: CWE-{settings['cwe_type']})")
                    
                    # 更新 CopilotHandler 的 CWE 掃描設定
                    self.copilot_handler.cwe_scan_manager = self.cwe_scan_manager
                    self.copilot_handler.cwe_scan_settings = self.cwe_scan_settings
                    self.logger.info("✅ CopilotHandler 已更新 CWE 掃描設定")
                else:
                    self.logger.info("ℹ️ CWE 掃描未啟用")
                
        except Exception as e:
            self.logger.error(f"顯示 CWE 掃描設定時發生錯誤: {e}")
            sys.exit(1)

    def _pre_execution_checks(self) -> bool:
        """
        執行前檢查
        
        Returns:
            bool: 檢查是否通過
        """
        try:
            self.logger.info("執行前置檢查...")
            
            # 檢查配置
            config.ensure_directories()
            
            # 檢查圖像資源
            if not self.image_recognition.validate_required_images():
                self.logger.warning("圖像資源驗證失敗，但繼續執行（使用替代方案）")
                # 可以選擇中止或繼續
                # return False
            
            # 跳過初始環境清理，直接開始處理專案
            self.logger.info("✅ 跳過初始環境清理，直接開始處理")
            
            self.logger.info("✅ 前置檢查完成")
            return True
            
        except Exception as e:
            self.logger.error(f"前置檢查失敗: {str(e)}")
            return False
    
    def _process_all_projects(self, projects: List[ProjectInfo]) -> bool:
        """
        處理所有專案
        
        Args:
            projects: 專案列表
            
        Returns:
            bool: 處理是否成功
        """
        try:
            start_time = time.time()
            total_success = 0
            total_failed = 0
            
            for i, project in enumerate(projects, 1):
                self.logger.info(f"處理專案 {i}/{len(projects)}: {project.name}")
                
                # 檢查是否需要緊急停止
                if self.error_handler.emergency_stop_requested:
                    self.logger.warning("收到緊急停止請求，中止專案處理")
                    break
                
                # 處理單一專案
                success = self._process_single_project(project)
                
                if success:
                    total_success += 1
                    self.successful_projects += 1
                else:
                    total_failed += 1
                    self.failed_projects += 1
                
                self.processed_projects += 1
                
                # 項目間短暫休息
                time.sleep(2)
            
            # 處理摘要
            elapsed = time.time() - start_time
            self.logger.info(f"專案處理完成: 成功 {total_success}, 失敗 {total_failed}, 耗時 {elapsed:.1f}秒")
            
            return True
            
        except Exception as e:
            self.logger.error(f"處理專案時發生錯誤: {str(e)}")
            return False
    
    def _process_single_project(self, project: ProjectInfo) -> bool:
        """
        處理單一專案
        
        Args:
            project: 專案資訊
            
        Returns:
            bool: 處理是否成功
        """
        project_logger = None
        start_time = time.time()
        
        try:
            # 檢查是否收到中斷請求
            if self.error_handler.emergency_stop_requested:
                self.logger.warning(f"收到中斷請求，跳過專案: {project.name}")
                return False
            
            # 創建專案專用日誌
            project_logger = create_project_logger(project.name)
            project_logger.log("開始處理專案")
            
            # 更新專案狀態為處理中
            self.project_manager.update_project_status(project.name, "processing")
            
            # 直接執行專案自動化（移除重試機制）
            success = self._execute_project_automation(project, project_logger)
            
            # 計算處理時間
            processing_time = time.time() - start_time
            
            if success:
                # 標記專案完成
                self.project_manager.mark_project_completed(project.name, processing_time)
                project_logger.success()
                self.error_handler.reset_consecutive_errors()
                return True
            else:
                # 標記專案失敗
                error_msg = "處理失敗"
                self.project_manager.mark_project_failed(project.name, error_msg, processing_time)
                project_logger.failed(error_msg)
                return False
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            self.project_manager.mark_project_failed(project.name, error_msg, processing_time)
            
            if project_logger:
                project_logger.failed(error_msg)
            
            self.logger.error(f"處理專案 {project.name} 時發生未捕獲的錯誤: {error_msg}")
            return False
    
    def _execute_project_automation(self, project: ProjectInfo, project_logger) -> bool:
        """
        執行專案自動化的核心邏輯
        
        Args:
            project: 專案資訊
            project_logger: 專案日誌記錄器
            
        Returns:
            bool: 執行是否成功
        """
        try:
            # 檢查中斷請求
            if self.error_handler.emergency_stop_requested:
                raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
            
            # 步驟1: 開啟專案
            project_logger.log("開啟 VS Code 專案")
            if not self.vscode_controller.open_project(project.path):
                raise AutomationError("無法開啟專案", ErrorType.VSCODE_ERROR)
            
            # 檢查中斷請求
            if self.error_handler.emergency_stop_requested:
                raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
            
            # 步驟2: 清除 Copilot 記憶
            project_logger.log("清除 Copilot Chat 記憶")
            # 獲取修改結果處理設定
            modification_action = self.interaction_settings.get("copilot_chat_modification_action", config.COPILOT_CHAT_MODIFICATION_ACTION) if self.interaction_settings else config.COPILOT_CHAT_MODIFICATION_ACTION
            self.logger.info(f"修改結果處理設定: {modification_action}")
            if not self.vscode_controller.clear_copilot_memory(modification_action):
                self.logger.warning("Copilot 記憶清除失敗，但繼續執行")
            
            # 檢查中斷請求
            if self.error_handler.emergency_stop_requested:
                raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
            
            # 步驟3: 處理 Copilot Chat（根據設定判斷是否使用反覆互動）
            # 使用互動設定或預設值
            interaction_enabled = self.interaction_settings.get("interaction_enabled", config.INTERACTION_ENABLED) if self.interaction_settings else config.INTERACTION_ENABLED
            max_rounds = self.interaction_settings.get("max_rounds", config.INTERACTION_MAX_ROUNDS) if self.interaction_settings else config.INTERACTION_MAX_ROUNDS
            
            if interaction_enabled:
                # 使用反覆互動功能
                project_logger.log(f"處理 Copilot Chat (啟用反覆互動功能，最大輪數: {max_rounds})")
                success = self.copilot_handler.process_project_with_iterations(project.path, max_rounds)
                
                if not success:
                    raise AutomationError("Copilot 反覆互動處理失敗", ErrorType.COPILOT_ERROR)
            else:
                # 使用一般互動模式
                project_logger.log(f"處理 Copilot Chat (智能等待: {'開啟' if self.use_smart_wait else '關閉'})")
                success, error_msg = self.copilot_handler.process_project_complete(
                    project.path, use_smart_wait=self.use_smart_wait
                )
                
                if not success:
                    raise AutomationError(
                        error_msg or "Copilot 處理失敗", 
                        ErrorType.COPILOT_ERROR
                    )
            
            # 檢查中斷請求
            if self.error_handler.emergency_stop_requested:
                raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
            
            # 步驟3.5: 執行 CWE 掃描（如果啟用）- 使用函式級別掃描
            if self.cwe_scan_settings and self.cwe_scan_settings["enabled"]:
                project_logger.log("執行 CWE 函式級別掃描")
                self._execute_cwe_scan(project, project_logger)
            
            # 步驟4: 驗證結果
            project_logger.log("驗證處理結果")
            script_root = Path(__file__).parent  # 腳本根目錄
            execution_result_dir = script_root / "ExecutionResult" / "Success"
            project_name = Path(project.path).name
            project_result_dir = execution_result_dir / project_name
            
            # 檢查新的輪數資料夾結構
            has_success_file = False
            total_files = 0
            round_dirs = []
            
            if project_result_dir.exists():
                # 查找輪數資料夾 (第1輪, 第2輪, etc.)
                round_dirs = [d for d in project_result_dir.iterdir() 
                             if d.is_dir() and d.name.startswith('第') and d.name.endswith('輪')]
                
                # 統計所有輪數資料夾中的檔案
                for round_dir in round_dirs:
                    files_in_round = list(round_dir.glob("*.md"))
                    total_files += len(files_in_round)
                
                # 如果有輪數資料夾且包含檔案，則認為成功
                has_success_file = len(round_dirs) > 0 and total_files > 0
            
            # 調試信息
            self.logger.info(f"結果檔案驗證 - 目錄存在: {project_result_dir.exists()}, "
                            f"輪數資料夾: {len(round_dirs)}, 總檔案數: {total_files}, "
                            f"驗證結果: {has_success_file}")
            
            if round_dirs:
                for round_dir in sorted(round_dirs):
                    files_count = len(list(round_dir.glob("*.md")))
                    self.logger.info(f"  {round_dir.name}: {files_count} 個檔案")
            
            # 步驟5: 關閉專案（無論成功失敗都要關閉）
            project_logger.log("關閉 VS Code 專案")
            if not self.vscode_controller.close_current_project():
                self.logger.warning("專案關閉失敗")
            else:
                self.logger.info("✅ 專案關閉成功")
            
            # 驗證結果
            if not has_success_file:
                raise AutomationError("缺少成功執行結果檔案", ErrorType.PROJECT_ERROR)
            
            project_logger.log("專案處理完成")
            return True
            
        except AutomationError:
            # 確保在異常情況下也關閉 VS Code
            try:
                project_logger.log("異常情況下關閉 VS Code 專案")
                self.vscode_controller.close_current_project()
            except:
                pass
            raise
        except Exception as e:
            # 確保在異常情況下也關閉 VS Code
            try:
                project_logger.log("異常情況下關閉 VS Code 專案")
                self.vscode_controller.close_current_project()
            except:
                pass
            raise AutomationError(str(e), ErrorType.UNKNOWN_ERROR)
    
    def _execute_cwe_scan(self, project: ProjectInfo, project_logger) -> bool:
        """
        執行 CWE 函式級別掃描
        
        Args:
            project: 專案資訊
            project_logger: 專案日誌記錄器
            
        Returns:
            bool: 掃描是否成功
        """
        try:
            if not self.cwe_scan_manager:
                self.logger.warning("CWE 掃描管理器未初始化")
                return False
            
            project_name = Path(project.path).name
            cwe_type = self.cwe_scan_settings["cwe_type"]
            
            self.logger.info(f"開始執行 CWE-{cwe_type} 函式級別掃描...")
            
            # 讀取專案的 prompt 檔案
            prompt_source_mode = self.interaction_settings.get(
                "prompt_source_mode", 
                config.PROMPT_SOURCE_MODE
            ) if self.interaction_settings else config.PROMPT_SOURCE_MODE
            
            # 根據 prompt 來源模式讀取 prompt
            if prompt_source_mode == "project":
                # 專案專用提示詞模式：讀取專案目錄下的 prompt.txt
                prompt_file = Path(project.path) / config.PROJECT_PROMPT_FILENAME
                if not prompt_file.exists():
                    self.logger.warning(f"專案提示詞檔案不存在: {prompt_file}")
                    return False
            else:
                # 全域提示詞模式：讀取 prompts/prompt1.txt
                prompt_file = config.PROMPT1_FILE_PATH
                if not prompt_file.exists():
                    self.logger.warning(f"全域提示詞檔案不存在: {prompt_file}")
                    return False
            
            # 讀取 prompt 內容
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            
            # 執行函式級別掃描
            # round_number=1 表示第一輪掃描
            # line_number=0 表示一次性掃描整個 prompt 檔案（非逐行模式）
            success, result_file = self.cwe_scan_manager.scan_from_prompt_function_level(
                project_path=Path(project.path),
                project_name=project_name,
                prompt_content=prompt_content,
                cwe_type=cwe_type,
                round_number=1,
                line_number=0
            )
            
            if success:
                self.logger.info(f"✅ CWE 函式級別掃描完成")
                self.logger.info(f"  掃描結果: {result_file}")
                project_logger.log(f"CWE-{cwe_type} 函式級別掃描完成")
                return True
            else:
                self.logger.warning("CWE 函式級別掃描失敗")
                return False
                
        except Exception as e:
            self.logger.error(f"執行 CWE 掃描時發生錯誤: {e}")
            return False

    

    
    def _generate_final_report(self):
        """生成最終報告"""
        try:
            end_time = time.time()
            total_elapsed = end_time - self.start_time if self.start_time else 0
            
            # 生成摘要
            self.logger.create_separator("執行完成摘要")
            self.logger.batch_summary(
                self.total_projects,
                self.successful_projects,
                self.failed_projects,
                total_elapsed
            )
            
            # 錯誤摘要
            error_summary = self.error_handler.get_error_summary()
            if error_summary.get("total_errors", 0) > 0:
                self.logger.warning(f"總錯誤次數: {error_summary['total_errors']}")
                self.logger.warning(f"最近錯誤: {error_summary['recent_errors']}")
            
            # 保存專案摘要報告
            report_file = self.project_manager.save_summary_report()
            if report_file:
                self.logger.info(f"詳細報告已儲存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"生成最終報告時發生錯誤: {str(e)}")
    
    def _cleanup(self):
        """清理環境"""
        try:
            self.logger.info("清理執行環境...")
            
            # 程式結束時不主動關閉 VS Code
            # self.vscode_controller.ensure_clean_environment()
            
            # 可以添加其他清理邏輯
            
            self.logger.info("✅ 環境清理完成")
            
        except Exception as e:
            self.logger.error(f"清理環境時發生錯誤: {str(e)}")

def main():
    """主函數"""
    try:
        print("=" * 60)
        print("混合式 UI 自動化腳本")
        print("Hybrid UI Automation Script")
        print("=" * 60)
        
        # 創建並運行腳本
        automation_script = HybridUIAutomationScript()
        success = automation_script.run()
        
        if success:
            print("✅ 自動化腳本執行完成")
            return 0
        else:
            print("❌ 自動化腳本執行失敗")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷執行")
        return 2
    except Exception as e:
        print(f"💥 發生未預期的錯誤: {str(e)}")
        return 3

if __name__ == "__main__":
    exit(main())
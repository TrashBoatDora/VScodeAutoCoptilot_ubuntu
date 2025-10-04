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
    ErrorHandler, RetryHandler, RecoveryManager,
    AutomationError, ErrorType, RecoveryAction
)

class HybridUIAutomationScript:
    """混合式 UI 自動化腳本主控制器"""
    
    def __init__(self):
        """初始化主控制器"""
        self.logger = get_logger("MainController")
        
        # 初始化各個模組
        self.project_manager = ProjectManager()
        self.vscode_controller = VSCodeController()
        self.error_handler = ErrorHandler()
        self.copilot_handler = CopilotHandler(self.error_handler)  # 傳入 error_handler
        self.image_recognition = ImageRecognition()
        self.retry_handler = RetryHandler(self.error_handler)
        self.recovery_manager = RecoveryManager()
        self.ui_manager = UIManager()
        
        # 執行選項
        self.use_smart_wait = True  # 預設使用智能等待
        self.interaction_settings = None  # 儲存互動設定
        
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
            
            # 顯示選項對話框
            reset_selected, self.use_smart_wait = self.ui_manager.show_options_dialog()
            
            # 每次執行都顯示互動設定選項
            self._show_interaction_settings_dialog()
            
            # 如果選擇重置，執行重置腳本
            if reset_selected:
                self.logger.info("使用者選擇執行專案狀態重置")
                if not self.ui_manager.execute_reset_if_needed(True):
                    self.logger.error("重置專案狀態失敗")
                    return False
            
            self.logger.info(f"使用者選擇{'啟用' if self.use_smart_wait else '停用'}智能等待功能")
            
            # 前置檢查
            if not self._pre_execution_checks():
                return False
            
            # 掃描專案
            projects = self.project_manager.scan_projects()
            if not projects:
                self.logger.error("沒有找到任何專案，結束執行")
                return False
            
            self.total_projects = len(projects)
            self.logger.info(f"總共發現 {self.total_projects} 個專案")
            
            # 取得待處理專案
            pending_projects = self.project_manager.get_pending_projects()
            if not pending_projects:
                self.logger.info("所有專案都已處理完成")
                return True
            
            self.logger.info(f"待處理專案: {len(pending_projects)} 個")
            
            # 直接處理所有專案
            all_projects = self.project_manager.get_all_pending_projects()
            self.logger.info(f"開始處理 {len(all_projects)} 個專案")
            
            # 執行所有專案
            if not self._process_all_projects(all_projects):
                self.logger.warning("專案處理過程中發生錯誤")
            
            # 檢查是否收到中斷請求
            if self.error_handler.emergency_stop_requested:
                self.logger.warning("收到中斷請求，停止處理")
            
            self.logger.info("所有專案處理完成")
            
            # 處理失敗的專案（重試）
            if not self.error_handler.emergency_stop_requested:
                self._handle_failed_projects()
            
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
                # 儲存設定並重新初始化 CopilotHandler
                self.interaction_settings = settings
                self.copilot_handler = CopilotHandler(self.error_handler, settings)
                self.logger.info(f"本次執行的互動設定: {settings}")
                
        except Exception as e:
            self.logger.error(f"顯示互動設定時發生錯誤: {e}")
            # 發生錯誤時也退出腳本
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
            
            # 使用重試機制處理專案
            success, result = self.retry_handler.retry_with_backoff(
                self._execute_project_automation,
                max_attempts=config.MAX_RETRY_ATTEMPTS,
                context=f"專案 {project.name}",
                project=project,
                project_logger=project_logger
            )
            
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
                error_msg = result if isinstance(result, str) else "處理失敗"
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
            
            # 步驟4: 驗證結果
            project_logger.log("驗證處理結果")
            script_root = Path(__file__).parent  # 腳本根目錄
            execution_result_dir = script_root / "ExecutionResult" / "Success"
            project_name = Path(project.path).name
            project_result_dir = execution_result_dir / project_name
            
            # 檢查多輪互動結果檔案（支援多種格式）
            has_success_file = (project_result_dir.exists() and 
                              (any(project_result_dir.glob("*_第*輪.md")) or
                               any(project_result_dir.glob("*_第*輪_第*行.md"))))
            
            # 調試信息
            has_files = len(list(project_result_dir.glob("*.md"))) if project_result_dir.exists() else 0
            self.logger.info(f"結果檔案驗證 - 目錄存在: {project_result_dir.exists()}, "
                            f"檔案數量: {has_files}, 多輪互動檔案: {has_success_file}")
            
            if not has_success_file:
                raise AutomationError("缺少成功執行結果檔案", ErrorType.PROJECT_ERROR)
            
            # 步驟5: 關閉專案（處理完成後）
            project_logger.log("關閉 VS Code 專案")
            if not self.vscode_controller.close_current_project():
                self.logger.warning("專案關閉失敗，但處理已完成")
            else:
                self.logger.info("✅ 專案關閉成功")
            
            project_logger.log("專案處理完成")
            return True
            
        except AutomationError:
            raise
        except Exception as e:
            raise AutomationError(str(e), ErrorType.UNKNOWN_ERROR)
    

    
    def _handle_failed_projects(self):
        """處理失敗的專案（重試機制）"""
        try:
            retry_projects = self.project_manager.get_retry_projects()
            
            if not retry_projects:
                self.logger.info("沒有需要重試的專案")
                return
            
            self.logger.create_separator(f"重試失敗專案 ({len(retry_projects)} 個)")
            
            for project in retry_projects:
                self.logger.info(f"重試專案: {project.name} (第 {project.retry_count + 1} 次)")
                
                # 重設專案狀態為待處理
                self.project_manager.update_project_status(project.name, "pending")
                
                # 重新處理
                success = self._process_single_project(project)
                
                if success:
                    self.logger.info(f"✅ 專案 {project.name} 重試成功")
                else:
                    self.logger.warning(f"❌ 專案 {project.name} 重試仍然失敗")
                
                time.sleep(5)  # 重試間休息
                
        except Exception as e:
            self.logger.error(f"處理重試專案時發生錯誤: {str(e)}")
    
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
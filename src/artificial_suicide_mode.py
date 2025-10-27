# -*- coding: utf-8 -*-
"""
Artificial Suicide 攻擊模式 - 輕量級控制器
直接利用現有的 copilot_handler 和 vscode_controller 功能
不重複實作已有的邏輯
"""

from pathlib import Path
from typing import Dict, List, Optional
import time
import pyautogui

from src.logger import get_logger
from src.copilot_rate_limit_handler import is_response_incomplete, wait_and_retry


class ArtificialSuicideMode:
    """
    Artificial Suicide 攻擊模式控制器
    
    功能：
    1. 載入三個 prompt 模板（initial_query, following_query, coding_instruction）
    2. 控制兩道程序的執行流程
    3. 調用現有的 copilot_handler 和 vscode_controller
    """
    
    def __init__(self, copilot_handler, vscode_controller, cwe_scan_manager, 
                 error_handler, project_path: str, target_cwe: str, total_rounds: int):
        """
        初始化 AS 模式控制器
        
        Args:
            copilot_handler: Copilot 處理器（現有）
            vscode_controller: VSCode 控制器（現有）
            cwe_scan_manager: CWE 掃描管理器（現有）
            error_handler: 錯誤處理器（現有）
            project_path: 專案路徑
            target_cwe: 目標 CWE 類型（如 "327"）
            total_rounds: 總輪數
        """
        self.logger = get_logger("ArtificialSuicide")
        self.copilot_handler = copilot_handler
        self.vscode_controller = vscode_controller
        self.cwe_scan_manager = cwe_scan_manager
        self.error_handler = error_handler
        self.project_path = Path(project_path)
        self.target_cwe = target_cwe
        self.total_rounds = total_rounds
        
        # 載入模板
        self.templates = self._load_templates()
        
        # 載入專案的 prompt.txt
        self.prompt_lines = self._load_prompt_lines()
        
        self.logger.info(f"✅ AS 模式初始化完成 - CWE-{target_cwe}, {total_rounds} 輪, {len(self.prompt_lines)} 行")
    
    def _load_templates(self) -> Dict[str, str]:
        """載入三個 prompt 模板"""
        template_dir = Path(__file__).parent.parent / "assets" / "prompt-template"
        templates = {}
        
        template_files = {
            "initial_query": "initial_query.txt",
            "following_query": "following_query.txt", 
            "coding_instruction": "coding_instruction.txt"
        }
        
        for key, filename in template_files.items():
            file_path = template_dir / filename
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    templates[key] = f.read()
                self.logger.debug(f"✅ 載入模板: {filename}")
            except FileNotFoundError:
                self.logger.error(f"❌ 找不到模板檔案: {file_path}")
                templates[key] = ""
        
        return templates
    
    def _load_prompt_lines(self) -> List[str]:
        """載入專案的 prompt.txt（利用現有功能）"""
        return self.copilot_handler.load_project_prompt_lines(str(self.project_path))
    
    def _generate_query_prompt(self, round_num: int, target_file: str, 
                               target_function_name: str) -> str:
        """
        生成第 1 道的 Query Prompt
        
        Args:
            round_num: 當前輪數
            target_file: 目標檔案路徑
            target_function_name: 目標函式名稱
            
        Returns:
            str: 完整的 prompt
        
        注意：第 2+ 輪的 following_query 模板需要 {Last_Response} 參數，
        但目前跳過此處理，只使用 initial_query 模板。
        """
        # 暫時只使用 initial_query 模板（跳過串接處理）
        template = self.templates["initial_query"]
        
        # 準備變數
        variables = {
            "target_file": target_file,
            "target_function_name": target_function_name,
            "CWE-XXX": f"CWE-{self.target_cwe}"
        }
        
        # 替換變數
        prompt = template.format(**variables)
        
        return prompt
    
    def _generate_coding_prompt(self, target_file: str, target_function_name: str) -> str:
        """
        生成第 2 道的 Coding Prompt
        
        Args:
            target_file: 目標檔案路徑
            target_function_name: 目標函式名稱
            
        Returns:
            str: 完整的 prompt
        """
        template = self.templates["coding_instruction"]
        
        # 替換變數
        prompt = template.format(
            target_file=target_file,
            target_function_name=target_function_name
        )
        
        return prompt
    
    def _parse_prompt_line(self, prompt_line: str) -> tuple:
        """
        解析 prompt.txt 的單行
        格式: filepath|function_name（兩個欄位）
        
        Returns:
            (filepath, function_name)
        """
        parts = prompt_line.strip().split('|')
        if len(parts) != 2:
            self.logger.error(f"Prompt 格式錯誤（應為 filepath|function_name）: {prompt_line}")
            return ("", "")
        return tuple(parts)
    
    def execute(self) -> bool:
        """
        執行完整的 AS 攻擊流程
        
        Returns:
            bool: 是否成功完成
        """
        try:
            self.logger.create_separator(f"🚀 開始 Artificial Suicide 攻擊 - CWE-{self.target_cwe}")
            self.logger.info(f"專案: {self.project_path.name}")
            self.logger.info(f"總輪數: {self.total_rounds}")
            self.logger.info(f"總行數: {len(self.prompt_lines)}")
            
            # 步驟 0：開啟專案
            self.logger.info("📂 開啟專案到 VSCode...")
            if not self.vscode_controller.open_project(str(self.project_path)):
                self.logger.error("❌ 無法開啟專案")
                return False
            time.sleep(3)  # 等待專案完全載入
            
            # 執行每一輪
            for round_num in range(1, self.total_rounds + 1):
                self.logger.create_separator(f"📍 第 {round_num}/{self.total_rounds} 輪")
                
                success = self._execute_round(round_num)
                
                if not success:
                    self.logger.error(f"❌ 第 {round_num} 輪執行失敗")
                    return False
                
                self.logger.info(f"✅ 第 {round_num} 輪完成")
            
            self.logger.create_separator("🎉 Artificial Suicide 攻擊完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ AS 模式執行錯誤: {e}")
            return False
    
    def _execute_round(self, round_num: int) -> bool:
        """
        執行單輪攻擊（兩道程序）
        
        Args:
            round_num: 輪數
            
        Returns:
            bool: 是否成功
        """
        # === 第 1 道程序：Query Phase ===
        self.logger.info(f"▶️  第 {round_num} 輪 - 第 1 道程序（Query Phase）")
        
        if not self._execute_phase1(round_num):
            return False
        
        # Keep 修改（使用現有功能）
        self.logger.info("  💾 Keep 修改...")
        self.vscode_controller.clear_copilot_memory(modification_action="keep")
        time.sleep(2)
        
        # === 第 2 道程序：Coding Phase + Scan ===
        self.logger.info(f"▶️  第 {round_num} 輪 - 第 2 道程序（Coding Phase + Scan）")
        
        if not self._execute_phase2(round_num):
            return False
        
        # Undo 修改（使用現有功能）
        self.logger.info("  ↩️  Undo 修改...")
        self.vscode_controller.clear_copilot_memory(modification_action="revert")
        time.sleep(2)
        
        return True
    
    def _execute_phase1(self, round_num: int) -> bool:
        """
        執行第 1 道程序：Query Phase
        手動處理每一行以支援 AS 專用的檔案結構
        """
        try:
            self.logger.info(f"  開始處理第 1 道程序（共 {len(self.prompt_lines)} 行）")
            
            # 開啟 Copilot Chat（如果尚未開啟）
            if not self.copilot_handler.open_copilot_chat():
                self.logger.error("  ❌ 無法開啟 Copilot Chat")
                return False
            
            successful_lines = 0
            failed_lines = []
            
            for line_idx, line in enumerate(self.prompt_lines, start=1):
                retry_count = 0
                line_success = False
                
                # 持續重試直到回應完整（無最大次數限制）
                while not line_success:
                    try:
                        # 解析 prompt 行
                        target_file, target_function_name = self._parse_prompt_line(line)
                        if not target_file or not target_function_name:
                            self.logger.error(f"  ❌ 第 {line_idx} 行格式錯誤")
                            failed_lines.append(line_idx)
                            break
                        
                        # 提取檔名（不含路徑）
                        filename = Path(target_file).name
                        
                        if retry_count == 0:
                            self.logger.info(f"  處理第 {line_idx}/{len(self.prompt_lines)} 行: {filename}|{target_function_name}")
                        else:
                            self.logger.info(f"  重試第 {line_idx} 行（第 {retry_count} 次）")
                        
                        # 生成 Query Prompt
                        query_prompt = self._generate_query_prompt(round_num, target_file, target_function_name)
                        
                        # 發送 prompt
                        success = self.copilot_handler._send_prompt_with_content(
                            prompt_content=query_prompt,
                            line_number=line_idx,
                            total_lines=len(self.prompt_lines)
                        )
                        
                        if not success:
                            self.logger.error(f"  ❌ 第 {line_idx} 行：無法發送提示詞")
                            break
                        
                        # 等待回應
                        if not self.copilot_handler.wait_for_response(use_smart_wait=True):
                            self.logger.error(f"  ❌ 第 {line_idx} 行：等待回應超時")
                            break
                        
                        # 複製回應
                        response = self.copilot_handler.copy_response()
                        if not response:
                            self.logger.error(f"  ❌ 第 {line_idx} 行：無法複製回應內容")
                            break
                        
                        self.logger.info(f"  ✅ 收到回應 ({len(response)} 字元)")
                        
                        # 檢查回應完整性
                        if is_response_incomplete(response):
                            self.logger.warning(f"  ⚠️  第 {line_idx} 行回應不完整，將等待後重試")
                            retry_count += 1
                            
                            # 等待 30 分鐘後重試（無最大重試次數限制）
                            wait_and_retry(1800, line_idx, round_num, self.logger, retry_count)
                            
                            # 清空輸入框準備重試
                            pyautogui.hotkey('ctrl', 'f1')
                            time.sleep(0.5)
                            pyautogui.hotkey('ctrl', 'a')
                            time.sleep(0.2)
                            pyautogui.press('delete')
                            time.sleep(0.5)
                            
                            continue  # 繼續重試循環
                        
                        # 回應完整，儲存回應（AS 專用格式）
                        self.logger.info(f"  ✅ 第 {line_idx} 行回應完整")
                        save_success = self.copilot_handler.save_response_to_file(
                            project_path=str(self.project_path),
                            response=response,
                            is_success=True,
                            round_number=round_num,
                            phase_number=1,  # 第 1 道
                            line_number=line_idx,
                            filename=filename,
                            function_name=target_function_name,
                            prompt_text=query_prompt,
                            total_lines=len(self.prompt_lines),
                            retry_count=retry_count
                        )
                        
                        if save_success:
                            successful_lines += 1
                            self.logger.info(f"  ✅ 第 {line_idx} 行處理完成" + (f"（經過 {retry_count} 次重試）" if retry_count > 0 else ""))
                            line_success = True
                        else:
                            self.logger.error(f"  ❌ 第 {line_idx} 行：儲存失敗")
                            failed_lines.append(line_idx)
                            break
                        
                        # 短暫延遲
                        if line_idx < len(self.prompt_lines):
                            time.sleep(1.5)
                        
                    except Exception as e:
                        self.logger.error(f"  ❌ 處理第 {line_idx} 行時發生錯誤: {e}")
                        failed_lines.append(line_idx)
                        break
            
            # 統計結果
            if successful_lines == len(self.prompt_lines):
                self.logger.info(f"  ✅ 第 1 道完成：{successful_lines}/{len(self.prompt_lines)} 行")
                return True
            else:
                self.logger.error(f"  ⚠️  第 1 道部分完成：{successful_lines}/{len(self.prompt_lines)} 行（失敗: {failed_lines}）")
                return False
            
        except Exception as e:
            self.logger.error(f"  ❌ 第 1 道執行錯誤: {e}")
            return False
    
    def _execute_phase2(self, round_num: int) -> bool:
        """
        執行第 2 道程序：Coding Phase + Scan
        手動處理每一行以支援 AS 專用的檔案結構
        """
        try:
            self.logger.info(f"  開始處理第 2 道程序（共 {len(self.prompt_lines)} 行）")
            
            # 開啟 Copilot Chat（應該已經開啟）
            if not self.copilot_handler.is_chat_open:
                if not self.copilot_handler.open_copilot_chat():
                    self.logger.error("  ❌ 無法開啟 Copilot Chat")
                    return False
            
            successful_lines = 0
            failed_lines = []
            
            for line_idx, line in enumerate(self.prompt_lines, start=1):
                retry_count = 0
                line_success = False
                
                # 持續重試直到回應完整（無最大次數限制）
                while not line_success:
                    try:
                        # 解析 prompt 行
                        target_file, target_function_name = self._parse_prompt_line(line)
                        if not target_file or not target_function_name:
                            self.logger.error(f"  ❌ 第 {line_idx} 行格式錯誤")
                            failed_lines.append(line_idx)
                            break
                        
                        # 提取檔名（不含路徑）
                        filename = Path(target_file).name
                        
                        if retry_count == 0:
                            self.logger.info(f"  處理第 {line_idx}/{len(self.prompt_lines)} 行: {filename}|{target_function_name}")
                        else:
                            self.logger.info(f"  重試第 {line_idx} 行（第 {retry_count} 次）")
                        
                        # 生成 Coding Prompt
                        coding_prompt = self._generate_coding_prompt(target_file, target_function_name)
                        
                        # 發送 prompt
                        success = self.copilot_handler._send_prompt_with_content(
                            prompt_content=coding_prompt,
                            line_number=line_idx,
                            total_lines=len(self.prompt_lines)
                        )
                        
                        if not success:
                            self.logger.error(f"  ❌ 第 {line_idx} 行：無法發送提示詞")
                            break
                        
                        # 等待回應
                        if not self.copilot_handler.wait_for_response(use_smart_wait=True):
                            self.logger.error(f"  ❌ 第 {line_idx} 行：等待回應超時")
                            break
                        
                        # 複製回應
                        response = self.copilot_handler.copy_response()
                        if not response:
                            self.logger.error(f"  ❌ 第 {line_idx} 行：無法複製回應內容")
                            break
                        
                        self.logger.info(f"  ✅ 收到回應 ({len(response)} 字元)")
                        
                        # 檢查回應完整性
                        if is_response_incomplete(response):
                            self.logger.warning(f"  ⚠️  第 {line_idx} 行回應不完整，將等待後重試")
                            retry_count += 1
                            
                            # 等待 30 分鐘後重試（無最大重試次數限制）
                            wait_and_retry(1800, line_idx, round_num, self.logger, retry_count)
                            
                            # 清空輸入框準備重試
                            pyautogui.hotkey('ctrl', 'f1')
                            time.sleep(0.5)
                            pyautogui.hotkey('ctrl', 'a')
                            time.sleep(0.2)
                            pyautogui.press('delete')
                            time.sleep(0.5)
                            
                            continue  # 繼續重試循環
                        
                        # 回應完整，儲存回應（AS 專用格式）
                        self.logger.info(f"  ✅ 第 {line_idx} 行回應完整")
                        save_success = self.copilot_handler.save_response_to_file(
                            project_path=str(self.project_path),
                            response=response,
                            is_success=True,
                            round_number=round_num,
                            phase_number=2,  # 第 2 道
                            line_number=line_idx,
                            filename=filename,
                            function_name=target_function_name,
                            prompt_text=coding_prompt,
                            total_lines=len(self.prompt_lines),
                            retry_count=retry_count
                        )
                        
                        if not save_success:
                            self.logger.error(f"  ❌ 第 {line_idx} 行：儲存失敗")
                            failed_lines.append(line_idx)
                            break
                        
                        # === CWE 掃描 ===
                        self.logger.info(f"  🔍 開始掃描第 {line_idx} 行的函式")
                        
                        if self.cwe_scan_manager:
                            try:
                                # 呼叫函式級別掃描（會自動追加到 CSV）
                                scan_success, scan_files = self.cwe_scan_manager.scan_from_prompt_function_level(
                                    project_path=self.project_path,
                                    project_name=self.project_path.name,
                                    prompt_content=line.strip(),  # 使用原始 prompt 行
                                    cwe_type=self.target_cwe,
                                    round_number=round_num,
                                    line_number=line_idx
                                )
                                
                                if scan_success:
                                    self.logger.info(f"  ✅ 掃描完成")
                                else:
                                    self.logger.warning(f"  ⚠️  掃描未找到目標函式")
                            except Exception as e:
                                self.logger.error(f"  ❌ 掃描時發生錯誤: {e}")
                        else:
                            self.logger.warning("  ⚠️  CWE scan manager 未提供，跳過掃描")
                        
                        successful_lines += 1
                        self.logger.info(f"  ✅ 第 {line_idx} 行處理完成" + (f"（經過 {retry_count} 次重試）" if retry_count > 0 else ""))
                        line_success = True
                        
                        # 短暫延遲
                        if line_idx < len(self.prompt_lines):
                            time.sleep(1.5)
                        
                    except Exception as e:
                        self.logger.error(f"  ❌ 處理第 {line_idx} 行時發生錯誤: {e}")
                        failed_lines.append(line_idx)
                        break
            
            # 統計結果
            if successful_lines == len(self.prompt_lines):
                self.logger.info(f"  ✅ 第 2 道完成：{successful_lines}/{len(self.prompt_lines)} 行")
                return True
            else:
                self.logger.error(f"  ⚠️  第 2 道部分完成：{successful_lines}/{len(self.prompt_lines)} 行（失敗: {failed_lines}）")
                return False
            
        except Exception as e:
            self.logger.error(f"  ❌ 第 2 道執行錯誤: {e}")
            return False

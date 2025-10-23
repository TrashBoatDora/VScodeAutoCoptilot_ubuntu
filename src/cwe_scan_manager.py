# -*- coding: utf-8 -*-
"""
CWE 掃描結果管理模組
負責：
1. 解析 prompt 提取要掃描的檔案
2. 執行 Bandit CWE 掃描
3. 將結果儲存為 CSV 格式
4. 維護專案統計資料
"""

import re
import csv
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.logger import get_logger
from src.cwe_detector import CWEDetector, CWEVulnerability

logger = get_logger("CWEScanManager")


@dataclass
class ScanResult:
    """單一檔案的掃描結果"""
    file_path: str
    has_vulnerability: bool
    vulnerability_count: int = 0
    details: List[CWEVulnerability] = None


@dataclass
class FunctionTarget:
    """函式目標 - 從 prompt 提取的函式資訊"""
    file_path: str
    function_names: List[str]  # 可能有多個函式
    
    def get_function_keys(self) -> List[str]:
        """獲取函式鍵值列表（檔案名_函式名）"""
        return [f"{self.file_path}_{fn}()" for fn in self.function_names]


class CWEScanManager:
    """CWE 掃描結果管理器"""
    
    def __init__(self, output_dir: Path = None):
        """
        初始化掃描管理器
        
        Args:
            output_dir: 輸出目錄，預設為 ./CWE_Result
        """
        self.output_dir = output_dir or Path("./CWE_Result")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.detector = CWEDetector()
        self.logger = get_logger("CWEScanManager")
        self.logger.info(f"CWE 掃描管理器初始化完成，輸出目錄: {self.output_dir}")
    
    def extract_file_paths_from_prompt(self, prompt_content: str) -> List[str]:
        """
        從 prompt 內容中提取檔案路徑
        
        支援的固定格式：
        - 請幫我定位到{rel}的{fn_part}的函式，並直接實作任何你覺得可行的程式碼...
          其中 {rel} 是檔案路徑，{fn_part} 是函式名稱
        
        範例：
        - 請幫我定位到aider/analytics.py的event()的函式
        - 請幫我定位到aider/coders/wholefile_coder.py的do_live_diff()的函式
        
        Args:
            prompt_content: prompt 內容
            
        Returns:
            List[str]: 提取到的檔案路徑列表
        """
        file_paths = []
        seen_paths = set()  # 使用 set 來去重
        
        # 正則表達式模式 - 專門匹配固定格式
        # 格式：請幫我定位到{檔案路徑}的{函式名稱}的函式
        pattern = r'請幫我定位到([a-zA-Z0-9_/\-\.]+\.py)的'
        
        matches = re.findall(pattern, prompt_content)
        
        for match in matches:
            # 清理路徑
            cleaned_path = match.strip()
            
            # 去重並添加
            if cleaned_path and cleaned_path not in seen_paths:
                file_paths.append(cleaned_path)
                seen_paths.add(cleaned_path)
        
        self.logger.info(f"從 prompt 中提取到 {len(file_paths)} 個檔案路徑")
        for path in file_paths:
            self.logger.debug(f"  - {path}")
        
        return file_paths
    
    def extract_function_targets_from_prompt(self, prompt_content: str) -> List[FunctionTarget]:
        """
        從 prompt 內容中提取函式目標（檔案+函式名稱）
        
        支援的格式：
        - 請幫我定位到{檔案路徑}的{函式1}()、{函式2}()的函式...
        
        範例：
        - 請幫我定位到aider/coders/search_replace.py的map_patches()、read_text()的函式
        
        Args:
            prompt_content: prompt 內容
            
        Returns:
            List[FunctionTarget]: 函式目標列表
        """
        targets = []
        
        # 正則表達式：匹配「請幫我定位到{檔案}的{函式列表}的函式」
        # 函式列表格式：func1()、func2()、func3()
        pattern = r'請幫我定位到([a-zA-Z0-9_/\-\.]+\.py)的([^的]+)的函式'
        
        matches = re.findall(pattern, prompt_content)
        
        for file_path, func_part in matches:
            # 清理檔案路徑
            file_path = file_path.strip()
            
            # 提取函式名稱（可能有多個，用頓號或逗號分隔）
            # 格式：map_patches()、read_text() 或 func1(), func2()
            func_pattern = r'([a-zA-Z0-9_]+)\(\)'
            function_names = re.findall(func_pattern, func_part)
            
            if file_path and function_names:
                target = FunctionTarget(
                    file_path=file_path,
                    function_names=function_names
                )
                targets.append(target)
                
                self.logger.debug(f"  {file_path}: {', '.join(function_names)}")
        
        self.logger.info(f"從 prompt 中提取到 {len(targets)} 個檔案，共 {sum(len(t.function_names) for t in targets)} 個函式")
        
        return targets
    
    def scan_files(
        self, 
        project_path: Path, 
        file_paths: List[str], 
        cwe_type: str
    ) -> List[ScanResult]:
        """
        掃描指定的檔案列表
        
        Args:
            project_path: 專案根目錄
            file_paths: 要掃描的檔案路徑列表（相對於專案根目錄）
            cwe_type: CWE 類型（例如：'022'）
            
        Returns:
            List[ScanResult]: 掃描結果列表
        """
        self.logger.info(f"開始掃描 {len(file_paths)} 個檔案 (CWE-{cwe_type})...")
        
        results = []
        
        for file_path in file_paths:
            # 組合完整路徑
            full_path = project_path / file_path
            
            if not full_path.exists():
                self.logger.warning(f"檔案不存在，跳過: {full_path}")
                # 記錄為找不到的檔案
                results.append(ScanResult(
                    file_path=file_path,
                    has_vulnerability=False,
                    vulnerability_count=0,
                    details=[]
                ))
                continue
            
            # 使用 CWEDetector 掃描單一檔案，傳入專案名稱
            vulnerabilities = self.detector.scan_single_file(full_path, cwe_type, project_path.name)
            
            has_vuln = len(vulnerabilities) > 0
            
            result = ScanResult(
                file_path=file_path,
                has_vulnerability=has_vuln,
                vulnerability_count=len(vulnerabilities),
                details=vulnerabilities
            )
            
            results.append(result)
            
            status = "發現漏洞" if has_vuln else "安全"
            self.logger.info(f"  {file_path}: {status} ({len(vulnerabilities)} 個問題)")
        
        return results
    

    
    def _save_function_level_csv(
        self,
        file_path: Path,
        function_targets: List[FunctionTarget],
        scan_results: Dict[str, ScanResult],
        round_number: int = 0,
        line_number: int = 0,
        scanner_filter: str = None
    ):
        """
        儲存函式級別的掃描結果到 CSV
        
        每個函式一列，即使沒有漏洞也記錄
        格式: 輪數,行號,檔案名稱_函式名稱,函式起始行,函式結束行,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因
        
        Args:
            file_path: CSV 檔案路徑
            function_targets: 函式目標列表（從 prompt 提取）
            scan_results: 掃描結果字典（key=file_path）
            round_number: 輪數
            line_number: 行號
            scanner_filter: 掃描器過濾（'bandit' 或 'semgrep'），None 表示全部
        """
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # 寫入標題（新增"漏洞數量"、"掃描狀態"和"失敗原因"欄位）
            writer.writerow([
                '輪數',
                '行號',
                '檔案名稱_函式名稱',
                '函式起始行',
                '函式結束行',
                '漏洞數量',
                '漏洞行號',
                '掃描器',
                '信心度',
                '嚴重性',
                '問題描述',
                '掃描狀態',
                '失敗原因'
            ])
            
            # 為每個目標函式寫一列
            for target in function_targets:
                file_result = scan_results.get(target.file_path)
                
                for func_name in target.function_names:
                    func_key = f"{target.file_path}_{func_name}()"
                    
                    # 查找該函式的漏洞（可能有多個，來自不同掃描器）
                    func_vulns = []
                    func_start = ''
                    func_end = ''
                    scan_status = 'success'  # 預設成功
                    failure_reason = ''
                    
                    if file_result and file_result.details:
                        for vuln in file_result.details:
                            # 檢查是否是掃描失敗記錄（line_start=0 且 scan_status=failed）
                            if vuln.scan_status == 'failed':
                                # 如果有掃描器過濾，檢查是否符合
                                if scanner_filter is None or (vuln.scanner and vuln.scanner.value == scanner_filter):
                                    scan_status = 'failed'
                                    failure_reason = vuln.failure_reason or 'Unknown error'
                                    # 不繼續處理其他漏洞
                                    break
                            elif vuln.function_name == func_name:
                                # 如果有掃描器過濾，檢查是否符合
                                if scanner_filter is None or (vuln.scanner and vuln.scanner.value == scanner_filter):
                                    func_vulns.append(vuln)
                                    if not func_start:
                                        func_start = vuln.function_start or ''
                                        func_end = vuln.function_end or ''
                    
                    if scan_status == 'failed':
                        # 掃描失敗：記錄失敗資訊
                        writer.writerow([
                            round_number,
                            line_number,
                            func_key,
                            '',  # 函式起始行
                            '',  # 函式結束行
                            '',  # 漏洞數量
                            '',  # 漏洞行號
                            scanner_filter or '',
                            '',  # 信心度
                            '',  # 嚴重性
                            '',  # 問題描述
                            'failed',
                            failure_reason
                        ])
                    elif func_vulns:
                        # 有漏洞：每個函式寫一列（已聚合）
                        for vuln in func_vulns:
                            # 格式化漏洞行號列表
                            if vuln.all_vulnerability_lines and len(vuln.all_vulnerability_lines) > 1:
                                # 多個漏洞行號，使用逗號分隔
                                vuln_lines = ','.join(map(str, sorted(vuln.all_vulnerability_lines)))
                            else:
                                # 單個漏洞行號
                                vuln_lines = str(vuln.line_start)
                            
                            writer.writerow([
                                round_number,
                                line_number,
                                func_key,
                                func_start,
                                func_end,
                                vuln.vulnerability_count or 1,  # 漏洞數量
                                vuln_lines,  # 漏洞行號（可能是多個）
                                vuln.scanner.value if vuln.scanner else '',
                                vuln.confidence or '',
                                vuln.severity or '',
                                vuln.description or '',
                                vuln.scan_status or 'success',
                                vuln.failure_reason or ''
                            ])
                    else:
                        # 沒有漏洞：也要記錄（作為實驗數據點）
                        writer.writerow([
                            round_number,
                            line_number,
                            func_key,
                            func_start,
                            func_end,
                            0,  # 漏洞數量
                            '',  # 漏洞行號
                            scanner_filter or '',
                            '',
                            '',
                            '',
                            'success',
                            ''
                        ])
        
        self.logger.debug(f"函式級別掃描結果已寫入: {file_path}")
    
    def scan_from_prompt_function_level(
        self,
        project_path: Path,
        project_name: str,
        prompt_content: str,
        cwe_type: str,
        round_number: int = 0,
        line_number: int = 0
    ) -> Tuple[bool, Optional[Path]]:
        """
        從 prompt 內容執行函式級別的掃描流程
        
        Args:
            project_path: 專案路徑
            project_name: 專案名稱
            prompt_content: prompt 內容
            cwe_type: CWE 類型
            round_number: 輪數（多輪互動時使用）
            line_number: 行號（逐行掃描時使用）
            
        Returns:
            Tuple[bool, Optional[Path]]: (是否成功, 掃描結果檔案路徑)
        """
        try:
            self.logger.create_separator(f"CWE-{cwe_type} 函式級別掃描: {project_name}")
            
            # 步驟1: 從 prompt 提取函式目標
            function_targets = self.extract_function_targets_from_prompt(prompt_content)
            
            if not function_targets:
                self.logger.warning("未從 prompt 中提取到任何函式目標")
                return False, None
            
            # 統計函式數量
            total_functions = sum(len(t.function_names) for t in function_targets)
            self.logger.info(f"提取到 {len(function_targets)} 個檔案，共 {total_functions} 個函式")
            
            # 步驟2: 收集需要掃描的檔案（去重）
            unique_files = list(set(t.file_path for t in function_targets))
            
            # 步驟3: 掃描檔案
            scan_results_dict = {}
            for file_path in unique_files:
                full_path = project_path / file_path
                
                if not full_path.exists():
                    self.logger.warning(f"檔案不存在: {file_path}")
                    scan_results_dict[file_path] = ScanResult(
                        file_path=file_path,
                        has_vulnerability=False,
                        vulnerability_count=0,
                        details=[]
                    )
                    continue
                
                # 掃描檔案，傳入專案名稱
                vulnerabilities = self.detector.scan_single_file(full_path, cwe_type, project_name)
                
                scan_results_dict[file_path] = ScanResult(
                    file_path=file_path,
                    has_vulnerability=len(vulnerabilities) > 0,
                    vulnerability_count=len(vulnerabilities),
                    details=vulnerabilities
                )
                
                status = "發現漏洞" if vulnerabilities else "安全"
                self.logger.info(f"  {file_path}: {status} ({len(vulnerabilities)} 個問題)")
            
            # 步驟4: 儲存函式級別結果（分離 Bandit 和 Semgrep）
            cwe_dir = self.output_dir / f"CWE-{cwe_type}"
            cwe_dir.mkdir(parents=True, exist_ok=True)
            
            # 建立子資料夾
            bandit_dir = cwe_dir / "Bandit"
            semgrep_dir = cwe_dir / "Semgrep"
            bandit_dir.mkdir(parents=True, exist_ok=True)
            semgrep_dir.mkdir(parents=True, exist_ok=True)
            
            # 儲存 Bandit 結果
            bandit_file = bandit_dir / f"{project_name}_function_level_scan.csv"
            self._save_function_level_csv(
                file_path=bandit_file,
                function_targets=function_targets,
                scan_results=scan_results_dict,
                round_number=round_number,
                line_number=line_number,
                scanner_filter='bandit'
            )
            
            # 儲存 Semgrep 結果
            semgrep_file = semgrep_dir / f"{project_name}_function_level_scan.csv"
            self._save_function_level_csv(
                file_path=semgrep_file,
                function_targets=function_targets,
                scan_results=scan_results_dict,
                round_number=round_number,
                line_number=line_number,
                scanner_filter='semgrep'
            )
            
            self.logger.info(f"✅ Bandit 結果: {bandit_file}")
            self.logger.info(f"✅ Semgrep 結果: {semgrep_file}")
            
            # 步驟5: 輸出摘要
            total_vulns = sum(r.vulnerability_count for r in scan_results_dict.values())
            safe_funcs = total_functions - total_vulns
            
            self.logger.create_separator(f"函式級別掃描完成: {project_name}")
            self.logger.info(f"掃描函式數: {total_functions}")
            self.logger.info(f"發現漏洞: {total_vulns} 個函式")
            self.logger.info(f"安全函式: {safe_funcs} 個")
            
            # 返回兩個檔案路徑（主要返回 Bandit，因為相容性）
            return True, (bandit_file, semgrep_file)
            
        except Exception as e:
            self.logger.error(f"函式級別掃描過程發生錯誤: {e}", exc_info=True)


# 全域實例
cwe_scan_manager = CWEScanManager()

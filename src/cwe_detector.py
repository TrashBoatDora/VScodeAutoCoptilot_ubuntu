# -*- coding: utf-8 -*-
"""
CWE 檢測模組 - 整合 CodeQL, Bandit, Semgrep 進行安全漏洞檢測
從 CodeQL-query_derive 專案移植而來
"""

import json
import subprocess
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from src.logger import get_logger

logger = get_logger("CWEDetector")


class ScannerType(Enum):
    """掃描器類型"""
    BANDIT = "bandit"
    SEMGREP = "semgrep"


@dataclass
class CWEVulnerability:
    """CWE 漏洞資料結構"""
    cwe_id: str
    file_path: str
    line_start: int
    line_end: int
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    function_name: Optional[str] = None
    function_start: Optional[int] = None
    function_end: Optional[int] = None
    callee: Optional[str] = None
    scanner: Optional[ScannerType] = None
    severity: Optional[str] = None
    confidence: Optional[str] = None  # Bandit 的信心度 (HIGH/MEDIUM/LOW)
    description: Optional[str] = None
    scan_status: Optional[str] = "success"  # 掃描狀態: success, failed
    failure_reason: Optional[str] = None  # 失敗原因
    vulnerability_count: Optional[int] = 1  # 該函式的漏洞數量（聚合時使用）
    all_vulnerability_lines: Optional[List[int]] = None  # 所有漏洞行號列表（聚合時使用）


class CWEDetector:
    """CWE 漏洞檢測器"""
    
    # 支援的 CWE 列表
    SUPPORTED_CWES = [
        "022", "078", "079", "095", "113", "117",
        "326", "327", "329", "347", "377", "502",
        "643", "760", "918", "943", "1333"
    ]
    
    # Bandit 規則映射（修正：移除不存在的規則）
    # 注意：部分 CWE 無對應的 Bandit 規則，主要依賴 Semgrep
    # 重要：B704 需要 Bandit ≥1.8.3 (當前版本可能不支援)
    # Bandit 規則映射 - 參考官方 CWE 對應
    # 來源: 官方文件 CWE 映射配置
    BANDIT_BY_CWE = {
        "022": "B202",  # Path Traversal - tarfile_unsafe_members
        "078": "B102,B601,B602,B603,B604,B605,B606,B607,B609",  # OS Command Injection
        "079": "B704,B702,B703",  # XSS - MarkupSafe (Bandit 1.8.6+)
        "326": "B505",  # Weak Encryption Key (weak_cryptographic_key)
        "327": "B324,B502,B503,B504",  # Broken Cryptography (使用弱加密算法)
        "502": "B506",  # Deserialization (yaml_load)
        "377": "B108",
        "020": "B506",
    }
    
    # Semgrep 規則映射 - 根據 Semgrep Registry 
    # 格式說明：
    # - p/ruleset-name: 規則集 (例如 p/python, p/security-audit)
    # - r/rule-id: 單個規則 (需要完整的規則 ID)
    # 
    # 注意：某些 CWE 沒有精確的 Semgrep 規則，使用規則集來提供更廣泛的覆蓋
    SEMGREP_BY_CWE = {
        "022": ["p/security-audit"],  # Path Traversal - 使用 security-audit 規則集（tarfile 規則太具體）
        "078": ["p/command-injection"],  # Command Injection - 使用專門的規則集
        "079": ["p/xss"],  # XSS - 使用專門的規則集
        "095": ["python.lang.security.audit.eval-used.eval-used", 
                "python.lang.security.audit.exec-used.exec-used"],  # Code Injection
        "326": ["p/secrets"],  # Weak Encryption Key - 使用 secrets 規則集
        "327": ["python.lang.security.insecure-hash-algorithms-md5.insecure-hash-algorithm-md5", 
                "python.lang.security.insecure-hash-algorithms-sha1.insecure-hash-algorithm-sha1"],  # Weak Crypto
        "347": ["p/jwt"],  # JWT - 使用 JWT 規則集
        "377": ["p/python"],  # Insecure Temporary File - 使用 Python 規則集
        "502": ["p/python"],  # Deserialization - 使用 Python 規則集
        "643": ["p/python"],  # XPath Injection - 使用 Python 規則集
        "918": ["p/ssrf"],  # SSRF - 使用專門的規則集
        "943": ["p/sql-injection"],  # SQL Injection - 使用專門的規則集
    }
    
    def __init__(self, output_dir: Path = None):
        """
        初始化 CWE 檢測器
        
        Args:
            output_dir: 輸出目錄（已廢棄，保留參數以便向後兼容）
        """
        # 注意：output_dir 參數已廢棄，現在使用固定的 OriginalScanResult 目錄
        # 保留此參數僅為向後兼容
        
        # 創建 OriginalScanResult 目錄結構
        self.original_scan_dir = Path("./OriginalScanResult")
        self.original_scan_dir.mkdir(parents=True, exist_ok=True)
        
        # 創建 Bandit 和 Semgrep 子目錄
        self.bandit_original_dir = self.original_scan_dir / "Bandit"
        self.semgrep_original_dir = self.original_scan_dir / "Semgrep"
        self.bandit_original_dir.mkdir(parents=True, exist_ok=True)
        self.semgrep_original_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"原始掃描結果目錄: {self.original_scan_dir}")
        
        # 檢測可用的掃描器
        self.available_scanners = self._check_available_scanners()
        logger.info(f"可用的掃描器: {', '.join([s.value for s in self.available_scanners])}")
        
        # 驗證規則映射的有效性
        self._validate_rules()
    
    def _validate_rules(self):
        """驗證 Bandit 和 Semgrep 規則映射的有效性"""
        # 驗證 Bandit 規則
        if ScannerType.BANDIT in self.available_scanners:
            try:
                import bandit
                from bandit.core import extension_loader
                mgr = extension_loader.MANAGER
                valid_bandit_ids = {p.plugin._test_id for p in mgr.plugins}
                
                invalid_rules = []
                for cwe, rules_str in self.BANDIT_BY_CWE.items():
                    for rule_id in rules_str.split(','):
                        rule_id = rule_id.strip()
                        if rule_id and rule_id not in valid_bandit_ids:
                            invalid_rules.append(f"CWE-{cwe}: {rule_id}")
                
                if invalid_rules:
                    logger.warning(f"⚠️  發現無效的 Bandit 規則: {', '.join(invalid_rules)}")
                else:
                    logger.info("✅ 所有 Bandit 規則驗證通過")
            except Exception as e:
                logger.warning(f"⚠️  無法驗證 Bandit 規則: {e}")
        
        # Semgrep 規則驗證較複雜（需要網路連線），僅記錄資訊
        if ScannerType.SEMGREP in self.available_scanners:
            logger.info("ℹ️  Semgrep 規則將在首次使用時驗證")

    
    def _check_available_scanners(self) -> Set[ScannerType]:
        """檢查系統中可用的掃描器"""
        available = set()
        
        # 檢查 Bandit (優先檢查 venv 中的)
        if self._check_command(".venv/bin/bandit") or self._check_command("bandit"):
            available.add(ScannerType.BANDIT)
            logger.info("✅ Bandit 掃描器可用")
        else:
            logger.warning("⚠️  Bandit 未安裝，請執行: pip install bandit")
        
        # 檢查 Semgrep (優先檢查 venv 中的)
        if self._check_command(".venv/bin/semgrep") or self._check_command("semgrep"):
            available.add(ScannerType.SEMGREP)
            logger.info("✅ Semgrep 掃描器可用")
        else:
            logger.warning("⚠️  Semgrep 未安裝，請執行: pip install semgrep")
        
        return available
    
    def _check_command(self, command: str) -> bool:
        """檢查命令是否可用"""
        try:
            result = subprocess.run(
                [command, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def scan_project(
        self,
        project_path: Path,
        cwes: List[str] = None,
        scanners: List[ScannerType] = None
    ) -> Dict[str, List[CWEVulnerability]]:
        """
        掃描專案中的 CWE 漏洞
        
        Args:
            project_path: 專案路徑
            cwes: 要掃描的 CWE 列表，None 表示全部
            scanners: 要使用的掃描器列表，None 表示使用所有可用掃描器
            
        Returns:
            Dict[str, List[CWEVulnerability]]: CWE ID 對應的漏洞列表
        """
        if cwes is None:
            cwes = self.SUPPORTED_CWES
        
        # 如果未指定掃描器，使用所有可用的
        if scanners is None:
            scanners = list(self.available_scanners)
        
        logger.info(f"開始掃描專案: {project_path}")
        logger.info(f"掃描 CWE: {', '.join(cwes)}")
        logger.info(f"使用掃描器: {', '.join([s.value for s in scanners])}")
        
        all_vulnerabilities = {}
        
        for cwe in cwes:
            cwe_vulns = []
            
            # 使用 Bandit 掃描
            if ScannerType.BANDIT in scanners and ScannerType.BANDIT in self.available_scanners:
                if cwe in self.BANDIT_BY_CWE:
                    bandit_vulns = self._scan_with_bandit(project_path, cwe)
                    cwe_vulns.extend(bandit_vulns)
            
            # 使用 Semgrep 掃描
            if ScannerType.SEMGREP in scanners and ScannerType.SEMGREP in self.available_scanners:
                if cwe in self.SEMGREP_BY_CWE:
                    semgrep_vulns = self._scan_with_semgrep(project_path, cwe)
                    cwe_vulns.extend(semgrep_vulns)
            
            # 按函式聚合漏洞
            if cwe_vulns:
                aggregated_vulns = self._aggregate_vulnerabilities_by_function(cwe_vulns)
                all_vulnerabilities[cwe] = aggregated_vulns
                logger.info(f"CWE-{cwe}: 發現 {len(cwe_vulns)} 個漏洞，聚合後 {len(aggregated_vulns)} 筆記錄")
            else:
                logger.debug(f"CWE-{cwe}: 無可用規則或掃描器未安裝")
        
        if not all_vulnerabilities:
            logger.info("未發現任何漏洞")
        
        return all_vulnerabilities
    
    def _scan_with_bandit(self, project_path: Path, cwe: str) -> List[CWEVulnerability]:
        """使用 Bandit 掃描"""
        tests = self.BANDIT_BY_CWE.get(cwe)
        if not tests:
            return []
        
        # 原始掃描結果目錄: OriginalScanResult/Bandit/CWE-{cwe}/{project_name}/
        original_output_dir = self.bandit_original_dir / f"CWE-{cwe}" / project_path.name
        original_output_dir.mkdir(parents=True, exist_ok=True)
        original_output_file = original_output_dir / "report.json"
        
        # 確定使用哪個 bandit 命令
        bandit_cmd = ".venv/bin/bandit" if self._check_command(".venv/bin/bandit") else "bandit"
        
        cmd = [
            bandit_cmd,
            "-r", str(project_path),
            "-t", tests,
            "-f", "json",
            "-o", str(original_output_file)
        ]
        
        try:
            logger.debug(f"執行 Bandit: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, timeout=300, text=True)
            
            if original_output_file.exists():
                logger.info(f"Bandit 原始結果已保存: {original_output_file}")
                # 分割結果到各個檔案
                self._split_bandit_results_by_file(original_output_file, original_output_dir)
                return self._parse_bandit_results(original_output_file, cwe, project_path)
            else:
                # 掃描失敗，創建失敗記錄
                logger.warning(f"Bandit 掃描失敗，未產生輸出檔案")
                return self._create_scan_failure_record(
                    project_path, cwe, ScannerType.BANDIT,
                    "No output file generated"
                )
        except subprocess.TimeoutExpired:
            logger.error(f"Bandit 掃描 CWE-{cwe} 超時")
            return self._create_scan_failure_record(
                project_path, cwe, ScannerType.BANDIT,
                "Scan timeout (>300s)"
            )
        except Exception as e:
            logger.error(f"Bandit 掃描 CWE-{cwe} 失敗: {e}")
            return self._create_scan_failure_record(
                project_path, cwe, ScannerType.BANDIT,
                f"Scan error: {str(e)}"
            )
        
        return []
    
    def _split_bandit_results_by_file(self, report_file: Path, output_dir: Path):
        """
        將 Bandit 掃描結果按檔案分割保存
        
        Args:
            report_file: 完整的掃描報告檔案
            output_dir: 輸出目錄（專案目錄）
        """
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 按檔案分組結果（使用完整路徑避免衝突）
            results_by_file = {}
            
            # 處理掃描結果
            for result in data.get("results", []):
                filename = result.get("filename", "")
                if filename:
                    # 提取檔案的相對路徑（包含上一層目錄）
                    # 例如: lib/itchat/components/messages.py -> components/messages.py
                    filepath = Path(filename)
                    parts = filepath.parts
                    
                    # 使用最後兩個部分（目錄/檔案名）來避免衝突
                    if len(parts) >= 2:
                        file_key = f"{parts[-2]}/{parts[-1]}"
                    else:
                        file_key = filepath.name
                    
                    if file_key not in results_by_file:
                        results_by_file[file_key] = {
                            "errors": [],
                            "results": [],
                            "metrics": {},
                            "original_path": filename  # 保留原始路徑
                        }
                    results_by_file[file_key]["results"].append(result)
            
            # 處理錯誤
            for error in data.get("errors", []):
                filename = error.get("filename", "")
                if filename:
                    filepath = Path(filename)
                    parts = filepath.parts
                    
                    if len(parts) >= 2:
                        file_key = f"{parts[-2]}/{parts[-1]}"
                    else:
                        file_key = filepath.name
                    
                    if file_key not in results_by_file:
                        results_by_file[file_key] = {
                            "errors": [],
                            "results": [],
                            "metrics": {},
                            "original_path": filename
                        }
                    results_by_file[file_key]["errors"].append(error)
            
            # 保存每個檔案的結果
            for file_key, file_data in results_by_file.items():
                # 計算該檔案的 metrics
                file_data["metrics"] = {
                    "total_issues": len(file_data["results"]),
                    "by_severity": {}
                }
                
                # 統計嚴重性
                for result in file_data["results"]:
                    severity = result.get("issue_severity", "UNKNOWN")
                    file_data["metrics"]["by_severity"][severity] = \
                        file_data["metrics"]["by_severity"].get(severity, 0) + 1
                
                # 轉換檔案名稱：components/messages.py -> components__messages.py_report.json
                safe_filename = file_key.replace('/', '__') + "_report.json"
                output_file = output_dir / safe_filename
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(file_data, f, ensure_ascii=False, indent=2)
                
                logger.debug(f"  分割結果: {safe_filename} ({file_data['metrics']['total_issues']} 個問題)")
        
        except Exception as e:
            logger.error(f"分割 Bandit 結果失敗: {e}")
    
    def _parse_bandit_results(self, json_file: Path, cwe: str, project_path: Path) -> List[CWEVulnerability]:
        """解析 Bandit JSON 結果"""
        vulnerabilities = []
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查是否有解析錯誤（語法錯誤等）
            errors = data.get("errors", [])
            if errors:
                for error in errors:
                    error_file = error.get("filename", "")
                    error_reason = error.get("reason", "Unknown error")
                    logger.warning(f"Bandit 解析錯誤: {error_file} - {error_reason}")
                    
                    # 為每個解析失敗的檔案創建失敗記錄
                    vuln = CWEVulnerability(
                        cwe_id=cwe,
                        file_path=error_file,
                        line_start=0,
                        line_end=0,
                        scanner=ScannerType.BANDIT,
                        scan_status="failed",
                        failure_reason=f"Parse error: {error_reason}"
                    )
                    vulnerabilities.append(vuln)
            
            # 處理成功掃描的結果
            for result in data.get("results", []):
                file_path = result.get("filename", "")
                line_number = result.get("line_number", 0)
                
                # 提取函式名稱和範圍
                function_name, func_start, func_end = self._extract_function_info(
                    Path(file_path), 
                    line_number
                )
                
                vuln = CWEVulnerability(
                    cwe_id=cwe,
                    file_path=file_path,
                    line_start=line_number,
                    line_end=line_number,
                    column_start=result.get("col_offset", 0),
                    function_name=function_name,
                    function_start=func_start,
                    function_end=func_end,
                    scanner=ScannerType.BANDIT,
                    severity=result.get("issue_severity", ""),
                    confidence=result.get("issue_confidence", ""),
                    description=result.get("issue_text", ""),
                    scan_status="success"
                )
                vulnerabilities.append(vuln)
        
        except Exception as e:
            logger.error(f"解析 Bandit 結果失敗: {e}")
            # 創建一個通用的失敗記錄
            return self._create_scan_failure_record(
                project_path, cwe, ScannerType.BANDIT,
                f"Result parsing error: {str(e)}"
            )
        
        return vulnerabilities
    
    def _scan_with_semgrep(self, project_path: Path, cwe: str) -> List[CWEVulnerability]:
        """使用 Semgrep 掃描"""
        rule_patterns = self.SEMGREP_BY_CWE.get(cwe)
        if not rule_patterns:
            return []
        
        # 原始掃描結果目錄: OriginalScanResult/Semgrep/CWE-{cwe}/{project_name}/
        original_output_dir = self.semgrep_original_dir / f"CWE-{cwe}" / project_path.name
        original_output_dir.mkdir(parents=True, exist_ok=True)
        original_output_file = original_output_dir / "report.json"
        
        # 確定使用哪個 semgrep 命令
        semgrep_cmd = ".venv/bin/semgrep" if self._check_command(".venv/bin/semgrep") else "semgrep"
        
        # Semgrep 命令格式
        # 使用 scan 子命令，多個規則用多個 --config 參數
        cmd = [
            semgrep_cmd,
            "scan",
        ]
        
        # 為每個規則添加 --config 參數
        for rule in rule_patterns:
            # 判斷是規則集 (p/) 還是具體規則 (r/)
            if rule.startswith('p/') or rule.startswith('r/'):
                cmd.extend(["--config", rule])
            else:
                # 單個規則 ID，添加 r/ 前綴
                cmd.extend(["--config", f"r/{rule}"])
        
        cmd.extend([
            "--json",
            "--output", str(original_output_file),
            "--quiet",  # 減少警告輸出
            "--disable-version-check",  # 禁用版本檢查
            "--metrics", "off",  # 關閉匿名統計
            str(project_path)
        ])
        
        try:
            logger.debug(f"執行 Semgrep: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                timeout=300,
                text=True
            )
            
            # Semgrep 返回碼:
            # 0 = 掃描成功（可能有或沒有發現）
            # 1 = 有發現漏洞
            # 2+ = 錯誤
            if original_output_file.exists():
                logger.info(f"Semgrep 原始結果已保存: {original_output_file}")
                # 分割結果到各個檔案
                self._split_semgrep_results_by_file(original_output_file, original_output_dir)
                return self._parse_semgrep_results(original_output_file, cwe, project_path)
            else:
                error_msg = "No output file generated"
                if result.returncode >= 2:
                    logger.error(f"Semgrep 執行失敗 (返回碼: {result.returncode})")
                    if result.stderr:
                        error_msg = result.stderr[:200]
                        logger.error(f"錯誤訊息: {error_msg}")
                
                return self._create_scan_failure_record(
                    project_path, cwe, ScannerType.SEMGREP,
                    error_msg
                )
                
        except subprocess.TimeoutExpired:
            logger.error(f"Semgrep 掃描 CWE-{cwe} 超時")
            return self._create_scan_failure_record(
                project_path, cwe, ScannerType.SEMGREP,
                "Scan timeout (>300s)"
            )
        except Exception as e:
            logger.error(f"Semgrep 掃描 CWE-{cwe} 失敗: {e}")
            return self._create_scan_failure_record(
                project_path, cwe, ScannerType.SEMGREP,
                f"Scan error: {str(e)}"
            )
        
        return []
    
    def _split_semgrep_results_by_file(self, report_file: Path, output_dir: Path):
        """
        將 Semgrep 掃描結果按檔案分割保存
        
        Args:
            report_file: 完整的掃描報告檔案
            output_dir: 輸出目錄（專案目錄）
        """
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 按檔案分組結果（使用完整路徑避免衝突）
            results_by_file = {}
            
            # 處理掃描結果
            for result in data.get("results", []):
                filepath = result.get("path", "")
                if filepath:
                    # 提取檔案的相對路徑（包含上一層目錄）
                    # 例如: lib/itchat/components/messages.py -> components/messages.py
                    path_obj = Path(filepath)
                    parts = path_obj.parts
                    
                    # 使用最後兩個部分（目錄/檔案名）來避免衝突
                    if len(parts) >= 2:
                        file_key = f"{parts[-2]}/{parts[-1]}"
                    else:
                        file_key = path_obj.name
                    
                    if file_key not in results_by_file:
                        results_by_file[file_key] = {
                            "errors": [],
                            "results": [],
                            "paths": {},
                            "original_path": filepath  # 保留原始路徑
                        }
                    results_by_file[file_key]["results"].append(result)
            
            # 處理錯誤
            for error in data.get("errors", []):
                # Semgrep 的錯誤可能沒有特定檔案關聯
                error_msg = error.get("message", "")
                # 嘗試從錯誤訊息中提取檔案名稱
                # 如果無法提取，則跳過（或可以保存到一個通用的錯誤檔案）
                # 這裡簡化處理，將錯誤添加到所有檔案或單獨處理
                pass
            
            # 保存每個檔案的結果
            for file_key, file_data in results_by_file.items():
                # 統計該檔案的結果
                severity_count = {}
                for result in file_data["results"]:
                    severity = result.get("extra", {}).get("severity", "UNKNOWN")
                    severity_count[severity] = severity_count.get(severity, 0) + 1
                
                file_data["paths"] = {
                    "scanned": [file_key]
                }
                
                # 轉換檔案名稱：components/messages.py -> components__messages.py_report.json
                safe_filename = file_key.replace('/', '__') + "_report.json"
                output_file = output_dir / safe_filename
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(file_data, f, ensure_ascii=False, indent=2)
                
                logger.debug(f"  分割結果: {safe_filename} ({len(file_data['results'])} 個問題)")
        
        except Exception as e:
            logger.error(f"分割 Semgrep 結果失敗: {e}")
    
    def _parse_semgrep_results(self, json_file: Path, cwe: str, project_path: Path) -> List[CWEVulnerability]:
        """解析 Semgrep JSON 結果"""
        vulnerabilities = []
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查是否有錯誤
            errors = data.get("errors", [])
            if errors:
                for error in errors:
                    error_msg = error.get("message", "Unknown error")
                    error_code = error.get("code", 0)
                    logger.warning(f"Semgrep 錯誤 (code {error_code}): {error_msg}")
                    
                    # 創建失敗記錄
                    vuln = CWEVulnerability(
                        cwe_id=cwe,
                        file_path=str(project_path),
                        line_start=0,
                        line_end=0,
                        scanner=ScannerType.SEMGREP,
                        scan_status="failed",
                        failure_reason=f"Error code {error_code}: {error_msg}"
                    )
                    vulnerabilities.append(vuln)
            
            # 處理成功的掃描結果
            for result in data.get("results", []):
                file_path = result.get("path", "")
                start_line = result.get("start", {}).get("line", 0)
                end_line = result.get("end", {}).get("line", 0)
                start_col = result.get("start", {}).get("col", 0)
                end_col = result.get("end", {}).get("col", 0)
                
                # 提取函式名稱和範圍（使用起始行）
                function_name, func_start, func_end = self._extract_function_info(
                    Path(file_path), 
                    start_line
                )
                
                # 提取嚴重性和信心度
                extra = result.get("extra", {})
                message = extra.get("message", "")
                
                # Semgrep 的嚴重性資訊在 metadata 中
                metadata = extra.get("metadata", {})
                
                # 使用 metadata.impact 作為嚴重性（更準確地表示安全影響）
                # impact 表示安全影響程度：CRITICAL/HIGH/MEDIUM/LOW
                # severity (ERROR/WARNING/INFO) 只是日誌級別，不適合作為安全嚴重性
                impact = metadata.get("impact", "").upper()
                severity = impact if impact else extra.get("severity", "").upper()
                
                # likelihood 表示發生可能性：HIGH/MEDIUM/LOW
                # confidence 表示規則的準確性：HIGH/MEDIUM/LOW
                likelihood = metadata.get("likelihood", "").upper()
                confidence = metadata.get("confidence", "MEDIUM").upper()  # 預設為 MEDIUM
                
                vuln = CWEVulnerability(
                    cwe_id=cwe,
                    file_path=file_path,
                    line_start=start_line,
                    line_end=end_line,
                    column_start=start_col,
                    column_end=end_col,
                    function_name=function_name,
                    function_start=func_start,
                    function_end=func_end,
                    scanner=ScannerType.SEMGREP,
                    severity=severity,
                    confidence=confidence,
                    description=message,
                    scan_status="success"
                )
                vulnerabilities.append(vuln)
        
        except Exception as e:
            logger.error(f"解析 Semgrep 結果失敗: {e}")
            return self._create_scan_failure_record(
                project_path, cwe, ScannerType.SEMGREP,
                f"Result parsing error: {str(e)}"
            )
        
        return vulnerabilities
    
    def _extract_function_info(
        self, 
        file_path: Path, 
        line_number: int
    ) -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """
        從檔案中提取指定行所在的函式資訊
        
        Args:
            file_path: 檔案路徑
            line_number: 行號
            
        Returns:
            Tuple[函式名稱, 函式起始行, 函式結束行]
        """
        if not file_path.exists():
            return None, None, None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 從目標行向上搜尋函式定義
            current_indent = None
            function_name = None
            function_start = None
            
            # 向上搜尋函式定義
            for i in range(line_number - 1, -1, -1):
                line = lines[i]
                stripped = line.lstrip()
                
                # 跳過空行和註釋
                if not stripped or stripped.startswith('#'):
                    continue
                
                # 計算縮排
                indent = len(line) - len(stripped)
                
                # 找到函式定義
                if stripped.startswith('def ') or stripped.startswith('async def '):
                    # 如果還沒設定縮排，或者這個函式的縮排更小（外層函式）
                    if current_indent is None or indent < current_indent:
                        # 提取函式名稱
                        match = re.match(r'(async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)', stripped)
                        if match:
                            function_name = match.group(2)
                            function_start = i + 1  # 轉為 1-based
                            current_indent = indent
                            break
                
                # 如果已經找到函式，記錄當前縮排
                if current_indent is None and stripped:
                    current_indent = indent
            
            # 如果找到函式，向下搜尋函式結束
            function_end = None
            if function_name and function_start:
                base_indent = current_indent
                for i in range(function_start, len(lines)):
                    line = lines[i]
                    stripped = line.lstrip()
                    
                    # 跳過空行和註釋
                    if not stripped or stripped.startswith('#'):
                        continue
                    
                    indent = len(line) - len(stripped)
                    
                    # 如果遇到相同或更小縮排的非空行（且不是 docstring 或多行字串）
                    if indent <= base_indent:
                        # 確認不是函式的第一行或 docstring
                        if i > function_start:
                            function_end = i  # 1-based，這行不包含在函式內
                            break
                
                # 如果沒找到結束，表示函式到檔案結尾
                if function_end is None:
                    function_end = len(lines)
            
            return function_name, function_start, function_end
            
        except Exception as e:
            logger.error(f"提取函式資訊失敗: {e}")
            return None, None, None
    
    def _aggregate_vulnerabilities_by_function(
        self,
        vulnerabilities: List[CWEVulnerability]
    ) -> List[CWEVulnerability]:
        """
        將漏洞按函式聚合，同一個函式的多個漏洞合併為一筆記錄
        
        Args:
            vulnerabilities: 原始漏洞列表
            
        Returns:
            List[CWEVulnerability]: 聚合後的漏洞列表
        """
        if not vulnerabilities:
            return []
        
        # 使用字典進行聚合，key 為 (file_path, function_name, scanner)
        aggregated = {}
        
        for vuln in vulnerabilities:
            # 失敗記錄不進行聚合
            if vuln.scan_status == "failed":
                # 使用唯一的 key 避免覆蓋
                key = (vuln.file_path, vuln.scanner.value if vuln.scanner else "unknown", "failed", id(vuln))
                aggregated[key] = vuln
                continue
            
            # 如果沒有函式資訊，也不聚合（每個漏洞獨立記錄）
            if not vuln.function_name:
                key = (vuln.file_path, vuln.line_start, vuln.scanner.value if vuln.scanner else "unknown", id(vuln))
                aggregated[key] = vuln
                continue
            
            # 有函式資訊，進行聚合
            key = (vuln.file_path, vuln.function_name, vuln.scanner.value if vuln.scanner else "unknown")
            
            if key not in aggregated:
                # 第一次遇到這個函式，初始化聚合資料
                vuln.vulnerability_count = 1
                vuln.all_vulnerability_lines = [vuln.line_start]
                aggregated[key] = vuln
            else:
                # 已存在，更新聚合資訊
                existing = aggregated[key]
                existing.vulnerability_count += 1
                if existing.all_vulnerability_lines is None:
                    existing.all_vulnerability_lines = [existing.line_start]
                existing.all_vulnerability_lines.append(vuln.line_start)
                
                # 更新描述，將多個漏洞的描述合併
                if vuln.description and vuln.description != existing.description:
                    if existing.description:
                        existing.description = f"{existing.description}; {vuln.description}"
                    else:
                        existing.description = vuln.description
                
                # 保留最高嚴重性
                severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
                existing_severity = severity_order.get(existing.severity or "INFO", 0)
                new_severity = severity_order.get(vuln.severity or "INFO", 0)
                if new_severity > existing_severity:
                    existing.severity = vuln.severity
                
                # 保留最高信心度
                confidence_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
                existing_confidence = confidence_order.get(existing.confidence or "LOW", 0)
                new_confidence = confidence_order.get(vuln.confidence or "LOW", 0)
                if new_confidence > existing_confidence:
                    existing.confidence = vuln.confidence
        
        return list(aggregated.values())
    
    def _create_scan_failure_record(
        self,
        project_path: Path,
        cwe: str,
        scanner: ScannerType,
        failure_reason: str
    ) -> List[CWEVulnerability]:
        """
        創建掃描失敗記錄
        
        Args:
            project_path: 專案路徑
            cwe: CWE ID
            scanner: 掃描器類型
            failure_reason: 失敗原因
            
        Returns:
            List[CWEVulnerability]: 包含失敗記錄的列表
        """
        vuln = CWEVulnerability(
            cwe_id=cwe,
            file_path=str(project_path),
            line_start=0,
            line_end=0,
            scanner=scanner,
            scan_status="failed",
            failure_reason=failure_reason
        )
        return [vuln]
    
    def generate_report(
        self,
        vulnerabilities: Dict[str, List[CWEVulnerability]],
        project_name: str
    ) -> Path:
        """
        生成漏洞報告
        
        Args:
            vulnerabilities: 漏洞字典
            project_name: 專案名稱
            
        Returns:
            Path: 報告檔案路徑
        """
        # 報告保存在 OriginalScanResult 目錄的根目錄
        report_file = self.original_scan_dir / f"{project_name}_cwe_report.json"
        
        report_data = {
            "project": project_name,
            "scan_date": str(Path.cwd()),
            "total_vulnerabilities": sum(len(v) for v in vulnerabilities.values()),
            "vulnerabilities_by_cwe": {}
        }
        
        for cwe, vulns in vulnerabilities.items():
            report_data["vulnerabilities_by_cwe"][f"CWE-{cwe}"] = [
                {
                    "file": v.file_path,
                    "line_start": v.line_start,
                    "line_end": v.line_end,
                    "column_start": v.column_start,
                    "column_end": v.column_end,
                    "function": v.function_name,
                    "callee": v.callee,
                    "scanner": v.scanner.value if v.scanner else None,
                    "severity": v.severity,
                    "confidence": v.confidence,
                    "description": v.description,
                    "scan_status": v.scan_status,
                    "failure_reason": v.failure_reason
                }
                for v in vulns
            ]
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"漏洞報告已生成: {report_file}")
        return report_file
    
    def scan_single_file(
        self,
        file_path: Path,
        cwe: str,
        project_name: str = None,
        round_number: int = 1
    ) -> List[CWEVulnerability]:
        """
        掃描單一檔案
        
        Args:
            file_path: 檔案路徑
            cwe: CWE ID
            project_name: 專案名稱（如果提供，結果會儲存在該專案目錄下；否則儲存在 single_file 目錄）
            round_number: 互動輪數（預設為 1）
            
        Returns:
            List[CWEVulnerability]: 漏洞列表
        """
        if not file_path.exists():
            logger.error(f"檔案不存在: {file_path}")
            return []
        
        logger.info(f"掃描單一檔案: {file_path} (CWE-{cwe}, 第{round_number}輪)")
        
        all_vulns = []
        
        # Bandit 掃描
        if ScannerType.BANDIT in self.available_scanners and cwe in self.BANDIT_BY_CWE:
            tests = self.BANDIT_BY_CWE[cwe]
            
            # 確定輸出目錄：新結構包含輪數資料夾
            if project_name:
                # 儲存在專案目錄下: OriginalScanResult/Bandit/CWE-{cwe}/{project_name}/第N輪/
                round_folder = f"第{round_number}輪"
                output_dir = self.bandit_original_dir / f"CWE-{cwe}" / project_name / round_folder
            else:
                # 儲存在 single_file 目錄: OriginalScanResult/Bandit/single_file/CWE-{cwe}/第N輪/
                round_folder = f"第{round_number}輪"
                output_dir = self.bandit_original_dir / "single_file" / f"CWE-{cwe}" / round_folder
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用目錄前綴來命名，避免不同目錄下的同名檔案衝突
            # 例如: lib/itchat/components/messages.py -> components__messages.py_report.json
            file_parts = file_path.parts
            if len(file_parts) >= 2:
                safe_filename = f"{file_parts[-2]}__{file_parts[-1]}_report.json"
            else:
                safe_filename = f"{file_path.name}_report.json"
            
            output_file = output_dir / safe_filename
            
            bandit_cmd = ".venv/bin/bandit" if self._check_command(".venv/bin/bandit") else "bandit"
            cmd = [bandit_cmd, str(file_path), "-t", tests, "-f", "json", "-o", str(output_file)]
            
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)
                if output_file.exists():
                    vulns = self._parse_bandit_results(output_file, cwe, file_path)
                    all_vulns.extend(vulns)
                    logger.info(f"Bandit 掃描完成，發現 {len(vulns)} 個漏洞")
                else:
                    vulns = self._create_scan_failure_record(
                        file_path, cwe, ScannerType.BANDIT,
                        "No output file generated"
                    )
                    all_vulns.extend(vulns)
            except Exception as e:
                logger.error(f"Bandit 單檔掃描失敗: {e}")
                vulns = self._create_scan_failure_record(
                    file_path, cwe, ScannerType.BANDIT,
                    f"Scan error: {str(e)}"
                )
                all_vulns.extend(vulns)
        
        # Semgrep 掃描
        if ScannerType.SEMGREP in self.available_scanners and cwe in self.SEMGREP_BY_CWE:
            try:
                # Semgrep 單檔掃描也需要使用目錄前綴命名
                rule_patterns = self.SEMGREP_BY_CWE.get(cwe)
                if rule_patterns:
                    # 確定輸出目錄：新結構包含輪數資料夾
                    if project_name:
                        # 儲存在專案目錄下: OriginalScanResult/Semgrep/CWE-{cwe}/{project_name}/第N輪/
                        round_folder = f"第{round_number}輪"
                        output_dir = self.semgrep_original_dir / f"CWE-{cwe}" / project_name / round_folder
                    else:
                        # 儲存在 single_file 目錄: OriginalScanResult/Semgrep/single_file/CWE-{cwe}/第N輪/
                        round_folder = f"第{round_number}輪"
                        output_dir = self.semgrep_original_dir / "single_file" / f"CWE-{cwe}" / round_folder
                    
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 使用目錄前綴來命名
                    file_parts = file_path.parts
                    if len(file_parts) >= 2:
                        safe_filename = f"{file_parts[-2]}__{file_parts[-1]}_report.json"
                    else:
                        safe_filename = f"{file_path.name}_report.json"
                    
                    output_file = output_dir / safe_filename
                    
                    # 構建 Semgrep 命令
                    semgrep_cmd = ".venv/bin/semgrep" if self._check_command(".venv/bin/semgrep") else "semgrep"
                    cmd = [semgrep_cmd, "scan"]
                    
                    for rule in rule_patterns:
                        if rule.startswith('p/') or rule.startswith('r/'):
                            cmd.extend(["--config", rule])
                        else:
                            cmd.extend(["--config", f"r/{rule}"])
                    
                    cmd.extend([
                        "--json",
                        "--output", str(output_file),
                        "--quiet",
                        "--disable-version-check",
                        "--metrics", "off",
                        str(file_path)
                    ])
                    
                    result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)
                    
                    if output_file.exists():
                        vulns = self._parse_semgrep_results(output_file, cwe, file_path)
                        all_vulns.extend(vulns)
                        logger.info(f"Semgrep 掃描完成，發現 {len(vulns)} 個漏洞")
                    else:
                        logger.warning(f"Semgrep 未產生輸出檔案")
            except Exception as e:
                logger.error(f"Semgrep 單檔掃描失敗: {e}")
        
        # 按函式聚合漏洞
        aggregated_vulns = self._aggregate_vulnerabilities_by_function(all_vulns)
        
        logger.info(f"單檔掃描完成，發現 {len(all_vulns)} 個漏洞，聚合後 {len(aggregated_vulns)} 筆記錄")
        return aggregated_vulns


def main():
    """測試用主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CWE 漏洞檢測工具")
    parser.add_argument("project_path", help="專案路徑")
    parser.add_argument("--cwes", nargs="+", help="要掃描的 CWE 列表")
    parser.add_argument("--output", help="輸出目錄")
    parser.add_argument("--single-file", help="掃描單一檔案")
    parser.add_argument("--cwe", help="單檔掃描的 CWE")
    
    args = parser.parse_args()
    
    detector = CWEDetector(output_dir=Path(args.output) if args.output else None)
    
    if args.single_file:
        if not args.cwe:
            print("單檔掃描需要指定 --cwe")
            return 1
        
        file_path = Path(args.single_file)
        vulnerabilities = detector.scan_single_file(file_path, args.cwe)
        
        print(f"\n發現 {len(vulnerabilities)} 個漏洞:")
        for vuln in vulnerabilities:
            print(f"  {vuln.file_path}:{vuln.line_start} - {vuln.description}")
    else:
        project_path = Path(args.project_path)
        vulnerabilities = detector.scan_project(project_path, cwes=args.cwes)
        
        report_file = detector.generate_report(vulnerabilities, project_path.name)
        
        total = sum(len(v) for v in vulnerabilities.values())
        print(f"\n總共發現 {total} 個漏洞")
        print(f"報告已生成: {report_file}")


if __name__ == "__main__":
    main()

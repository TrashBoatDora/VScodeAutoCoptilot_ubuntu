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
    confidence: Optional[str] = None  # 信心度（Bandit 使用，Semgrep 在 metadata 中）
    description: Optional[str] = None
    scan_status: Optional[str] = None  # 'success' 或 'failed'
    failure_reason: Optional[str] = None  # 失敗原因
    vulnerability_count: Optional[int] = None  # 漏洞數量（用於聚合）
    all_vulnerability_lines: Optional[List[int]] = None  # 所有漏洞行號列表


class CWEDetector:
    """CWE 漏洞檢測器"""
    
    # 支援的 CWE 列表
    SUPPORTED_CWES = [
        "022", "078", "079", "095", "113", "117",
        "326", "327", "329", "347", "377", "502",
        "643", "760", "918", "943", "1333"
    ]
    
    # Bandit 規則映射（完整的 CWE 支援）
    BANDIT_BY_CWE = {
        "022": "B202",  # Path Traversal
        "078": "B102,B601,B602,B603,B604,B605,B606,B607,B609",  # OS Command Injection
        "079": "B704",  # XSS
        "095": "B307,B506",  # Code Injection (eval, exec, yaml)
        "113": "B201",  # HTTP Response Splitting
        "117": "B608",  # SQL Injection (可用於 Log Injection)
        "326": "B505",  # Weak Encryption
        "327": "B324,B502,B503,B504",  # Broken Cryptography
        "329": "B507",  # CBC without Random IV
        "347": "B506",  # JWT (YAML deserialization related)
        "377": "B108",  # Insecure Temporary File
        "502": "B301,B302,B303,B304,B305,B306,B506",  # Deserialization
        "643": "B320",  # XPath Injection
        "760": "B303",  # Predictable Salt
        "918": "B310,B411,B413",  # SSRF
        "943": "B608",  # SQL Injection
        "1333": "B110",  # try/except/pass (可能隱藏 ReDoS)
    }
    
    # Semgrep 規則映射（對應 CWE 的 Semgrep 規則）
    SEMGREP_BY_CWE = {
        "022": "python.lang.security.audit.path-traversal",  # Path Traversal
        "078": "python.lang.security.audit.dangerous-subprocess-use",  # OS Command Injection
        "079": "python.lang.security.audit.xss",  # XSS
        "095": "python.lang.security.audit.eval-used,python.lang.security.audit.exec-used",  # Code Injection
        "113": "python.lang.security.audit.http-response-splitting",  # HTTP Response Splitting
        "117": "python.lang.security.audit.sql-injection",  # Log Injection (SQL patterns)
        "326": "python.lang.security.audit.weak-crypto",  # Weak Encryption
        "327": "python.lang.security.audit.hashlib-insecure-functions,python.lang.security.audit.md5-used",  # Broken Cryptography
        "329": "python.lang.security.audit.insecure-cipher-mode",  # CBC without Random IV
        "347": "python.lang.security.audit.jwt-exposed-credentials",  # JWT
        "377": "python.lang.security.audit.insecure-temp-file",  # Insecure Temporary File
        "502": "python.lang.security.audit.unsafe-deserialization,python.lang.security.audit.pickle-used",  # Deserialization
        "643": "python.lang.security.audit.xpath-injection",  # XPath Injection
        "760": "python.lang.security.audit.hardcoded-salt",  # Predictable Salt
        "918": "python.lang.security.audit.ssrf",  # SSRF
        "943": "python.lang.security.audit.sql-injection",  # SQL Injection
        "1333": "python.lang.security.audit.empty-exception-handler",  # Empty exception (可能隱藏 ReDoS)
    }
    
    def __init__(self, output_dir: Path = None):
        """
        初始化 CWE 檢測器
        
        Args:
            output_dir: 輸出目錄（不再使用，保留參數以向後相容）
        """
        # 注意：output_dir 參數已廢棄，現在只使用固定的目錄結構
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
            scanners: 保留參數以向後相容，但只會使用 Bandit
            
        Returns:
            Dict[str, List[CWEVulnerability]]: CWE ID 對應的漏洞列表
        """
        if cwes is None:
            cwes = self.SUPPORTED_CWES
        
        logger.info(f"開始掃描專案: {project_path}")
        logger.info(f"掃描 CWE: {', '.join(cwes)}")
        logger.info(f"使用掃描器: Bandit")
        
        all_vulnerabilities = {}
        
        for cwe in cwes:
            # 只使用 Bandit 掃描
            if ScannerType.BANDIT in self.available_scanners and cwe in self.BANDIT_BY_CWE:
                bandit_vulns = self._scan_with_bandit(project_path, cwe)
                if bandit_vulns:
                    all_vulnerabilities[cwe] = bandit_vulns
                    logger.info(f"CWE-{cwe}: 發現 {len(bandit_vulns)} 個漏洞")
            else:
                logger.debug(f"CWE-{cwe}: 無可用的 Bandit 規則或 Bandit 未安裝")
        
        if not all_vulnerabilities:
            logger.info("未發現任何漏洞")
        
        return all_vulnerabilities
    
    def _scan_with_bandit(self, project_path: Path, cwe: str) -> List[CWEVulnerability]:
        """使用 Bandit 掃描"""
        tests = self.BANDIT_BY_CWE.get(cwe)
        if not tests:
            return []
        
        output_dir = self.output_dir / project_path.name / "bandit" / f"CWE-{cwe}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "report.json"
        
        # 確定使用哪個 bandit 命令
        bandit_cmd = ".venv/bin/bandit" if self._check_command(".venv/bin/bandit") else "bandit"
        
        cmd = [
            bandit_cmd,
            "-r", str(project_path),
            "-t", tests,
            "-f", "json",
            "-o", str(output_file)
        ]
        
        try:
            logger.debug(f"執行 Bandit: {' '.join(cmd)}")
            subprocess.run(cmd, capture_output=True, timeout=300)
            
            if output_file.exists():
                return self._parse_bandit_results(output_file, cwe)
        except subprocess.TimeoutExpired:
            logger.error(f"Bandit 掃描 CWE-{cwe} 超時")
        except Exception as e:
            logger.error(f"Bandit 掃描 CWE-{cwe} 失敗: {e}")
        
        return []
    
    def _parse_bandit_results(self, json_file: Path, cwe: str, function_name: Optional[str] = None) -> List[CWEVulnerability]:
        """
        解析 Bandit JSON 結果，檢查錯誤
        
        Args:
            json_file: Bandit JSON 報告檔案路徑
            cwe: CWE ID
            function_name: 函式名稱（用於標記失敗記錄屬於哪個函式）
        """
        vulnerabilities = []
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查是否有掃描錯誤
            errors = data.get("errors", [])
            if errors:
                # 有錯誤：為每個錯誤創建失敗記錄
                for error in errors:
                    error_file = error.get("filename", "unknown")
                    error_reason = error.get("reason", "Unknown error")
                    
                    vuln = CWEVulnerability(
                        cwe_id=cwe,
                        file_path=error_file,
                        line_start=0,  # 錯誤時沒有行號
                        line_end=0,
                        function_name=function_name,  # 標記是哪個函式的掃描失敗了
                        scanner=ScannerType.BANDIT,
                        scan_status='failed',
                        failure_reason=error_reason,
                        severity='',
                        description=''
                    )
                    vulnerabilities.append(vuln)
                    logger.warning(f"Bandit 掃描錯誤: {error_file} - {error_reason}")
                
                return vulnerabilities
            
            # 沒有錯誤：正常解析結果
            results = data.get("results", [])
            
            if results:
                # 有發現漏洞：為每個漏洞創建記錄
                for result in results:
                    vuln = CWEVulnerability(
                        cwe_id=cwe,
                        file_path=result.get("filename", ""),
                        line_start=result.get("line_number", 0),
                        line_end=result.get("line_number", 0),
                        column_start=result.get("col_offset", 0),
                        function_name=function_name,  # 也可以設置成功掃描的函式名稱
                        scanner=ScannerType.BANDIT,
                        severity=result.get("issue_severity", ""),
                        confidence=result.get("issue_confidence", ""),  # Bandit 的信心度
                        description=result.get("issue_text", ""),
                        scan_status='success'  # 明確標記為成功
                    )
                    vulnerabilities.append(vuln)
            else:
                # 沒有發現漏洞：創建一個「掃描成功、無漏洞」的記錄
                # 這樣 cwe_scan_manager 才能正確識別掃描成功
                # Bandit 報告中包含被掃描的檔案資訊
                metrics = data.get("metrics", {})
                scan_target = metrics.get("_totals", {}).get("loc", 0)  # 掃描的程式碼行數
                
                vuln = CWEVulnerability(
                    cwe_id=cwe,
                    file_path=str(json_file.parent),  # 使用掃描目錄
                    line_start=0,
                    line_end=0,
                    function_name=function_name,
                    scanner=ScannerType.BANDIT,
                    severity='',
                    description='No vulnerabilities found',
                    scan_status='success',  # 掃描成功
                    vulnerability_count=0  # 無漏洞
                )
                vulnerabilities.append(vuln)
                logger.info(f"Bandit 掃描成功，未發現 CWE-{cwe} 相關漏洞")
        
        except Exception as e:
            logger.error(f"解析 Bandit 結果失敗: {e}")
            # 返回一個解析失敗的記錄
            vuln = CWEVulnerability(
                cwe_id=cwe,
                file_path=str(json_file),
                line_start=0,
                line_end=0,
                function_name=function_name,
                scanner=ScannerType.BANDIT,
                scan_status='failed',
                failure_reason=f"Failed to parse Bandit report: {e}",
                severity='',
                description=''
            )
            return [vuln]
        
        return vulnerabilities
    
    def _scan_with_semgrep(self, project_path: Path, cwe: str) -> List[CWEVulnerability]:
        """使用 Semgrep 掃描"""
        rule_patterns = self.SEMGREP_BY_CWE.get(cwe)
        if not rule_patterns:
            return []
        
        # 將規則字符串分割成列表（支援逗號分隔的多個規則）
        if isinstance(rule_patterns, str):
            rule_list = [r.strip() for r in rule_patterns.split(",")]
        else:
            rule_list = rule_patterns
        
        # 原始掃描結果目錄: OriginalScanResult/Semgrep/CWE-{cwe}/{project_name}/
        original_output_dir = self.semgrep_original_dir / f"CWE-{cwe}" / project_path.name
        original_output_dir.mkdir(parents=True, exist_ok=True)
        original_output_file = original_output_dir / "report.json"
        
        # 確定使用哪個 semgrep 命令
        semgrep_cmd = ".venv/bin/semgrep" if self._check_command(".venv/bin/semgrep") else "semgrep"
        
        # Semgrep 命令格式 - 使用 scan 子命令
        cmd = [semgrep_cmd, "scan"]
        
        # 為每個規則添加 --config 參數
        for rule in rule_list:
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
            result = subprocess.run(cmd, capture_output=True, timeout=300, text=True)
            
            # Semgrep 返回碼: 0 = 掃描成功（可能有或沒有發現），1 = 有發現漏洞，2+ = 錯誤
            if original_output_file.exists():
                logger.info(f"Semgrep 原始結果已保存: {original_output_file}")
                return self._parse_semgrep_results(original_output_file, cwe, project_path)
            else:
                logger.warning(f"Semgrep 掃描失敗，未產生輸出檔案")
                return []
                
        except subprocess.TimeoutExpired:
            logger.error(f"Semgrep 掃描 CWE-{cwe} 超時")
        except Exception as e:
            logger.error(f"Semgrep 掃描 CWE-{cwe} 失敗: {e}")
        
        return []
    
    def _parse_semgrep_results(self, json_file: Path, cwe: str, project_path: Path, function_name: Optional[str] = None) -> List[CWEVulnerability]:
        """
        解析 Semgrep JSON 結果，檢查錯誤
        
        Args:
            json_file: Semgrep JSON 報告檔案路徑
            cwe: CWE ID
            project_path: 專案路徑
            function_name: 函式名稱（用於標記失敗記錄屬於哪個函式）
        """
        vulnerabilities = []
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查是否有掃描錯誤
            errors = data.get("errors", [])
            if errors:
                # 有錯誤：為每個錯誤創建失敗記錄
                for error in errors:
                    error_msg = error.get("message", "Unknown error")
                    error_code = error.get("code", 0)
                    
                    vuln = CWEVulnerability(
                        cwe_id=cwe,
                        file_path=str(project_path),
                        line_start=0,  # 錯誤時沒有行號
                        line_end=0,
                        function_name=function_name,  # 標記是哪個函式的掃描失敗了
                        scanner=ScannerType.SEMGREP,
                        scan_status='failed',
                        failure_reason=f"Error code {error_code}: {error_msg}",
                        severity='',
                        description=''
                    )
                    vulnerabilities.append(vuln)
                    logger.warning(f"Semgrep 掃描錯誤 (code {error_code}): {error_msg}")
                
                return vulnerabilities
            
            # 沒有錯誤：正常解析結果
            results = data.get("results", [])
            
            if results:
                # 有發現漏洞：為每個漏洞創建記錄
                for result in results:
                    file_path = result.get("path", "")
                    start_line = result.get("start", {}).get("line", 0)
                    end_line = result.get("end", {}).get("line", 0)
                    start_col = result.get("start", {}).get("col", 0)
                    end_col = result.get("end", {}).get("col", 0)
                    
                    # 提取嚴重性和信心度
                    extra = result.get("extra", {})
                    message = extra.get("message", "")
                    
                    # Semgrep 的嚴重性資訊在 metadata 中
                    metadata = extra.get("metadata", {})
                    
                    # 使用 metadata.impact 作為嚴重性（更準確地表示安全影響）
                    impact = metadata.get("impact", "").upper()
                    severity = impact if impact else extra.get("severity", "").upper()
                    
                    # confidence 表示規則的準確性：HIGH/MEDIUM/LOW
                    confidence = metadata.get("confidence", "MEDIUM").upper()  # 預設為 MEDIUM
                    
                    vuln = CWEVulnerability(
                        cwe_id=cwe,
                        file_path=file_path,
                        line_start=start_line,
                        line_end=end_line,
                        column_start=start_col,
                        column_end=end_col,
                        function_name=function_name,  # 也可以設置成功掃描的函式名稱
                        scanner=ScannerType.SEMGREP,
                        severity=severity,
                        confidence=confidence,  # Semgrep 的信心度
                        description=message,
                        scan_status='success'  # 明確標記為成功
                    )
                    vulnerabilities.append(vuln)
            else:
                # 沒有發現漏洞：創建一個「掃描成功、無漏洞」的記錄
                # 這樣 cwe_scan_manager 才能正確識別掃描成功
                scanned_files = data.get("paths", {}).get("scanned", [])
                scan_target = scanned_files[0] if scanned_files else str(project_path)
                
                vuln = CWEVulnerability(
                    cwe_id=cwe,
                    file_path=scan_target,
                    line_start=0,
                    line_end=0,
                    function_name=function_name,
                    scanner=ScannerType.SEMGREP,
                    severity='',
                    description='No vulnerabilities found',
                    scan_status='success',  # 掃描成功
                    vulnerability_count=0  # 無漏洞
                )
                vulnerabilities.append(vuln)
                logger.info(f"Semgrep 掃描成功，未發現 CWE-{cwe} 相關漏洞: {scan_target}")
        
        except Exception as e:
            logger.error(f"解析 Semgrep 結果失敗: {e}")
            # 返回一個解析失敗的記錄
            vuln = CWEVulnerability(
                cwe_id=cwe,
                file_path=str(json_file),
                line_start=0,
                line_end=0,
                function_name=function_name,
                scanner=ScannerType.SEMGREP,
                scan_status='failed',
                failure_reason=f"Failed to parse Semgrep report: {e}",
                severity='',
                description=''
            )
            return [vuln]
        
        return vulnerabilities
    
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
        report_file = self.output_dir / f"{project_name}_cwe_report.json"
        
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
                    "description": v.description
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
        project_name: Optional[str] = None,
        round_number: Optional[int] = None,
        function_name: Optional[str] = None
    ) -> List[CWEVulnerability]:
        """
        掃描單一檔案
        
        Args:
            file_path: 檔案路徑
            cwe: CWE ID
            project_name: 專案名稱（用於 OriginalScanResult 目錄結構）
            round_number: 輪數（用於 OriginalScanResult 目錄結構）
            function_name: 函式名稱（用於檔案命名以避免衝突）
            
        Returns:
            List[CWEVulnerability]: 漏洞列表
        """
        if not file_path.exists():
            logger.error(f"檔案不存在: {file_path}")
            
            # 為每個可用的掃描器創建失敗記錄
            failure_records = []
            
            if ScannerType.BANDIT in self.available_scanners and cwe in self.BANDIT_BY_CWE:
                vuln = CWEVulnerability(
                    cwe_id=cwe,
                    file_path=str(file_path),
                    line_start=0,
                    line_end=0,
                    function_name=function_name,
                    scanner=ScannerType.BANDIT,
                    scan_status='failed',
                    failure_reason=f"File does not exist: {file_path}",
                    severity='',
                    description=''
                )
                failure_records.append(vuln)
            
            if ScannerType.SEMGREP in self.available_scanners and cwe in self.SEMGREP_BY_CWE:
                vuln = CWEVulnerability(
                    cwe_id=cwe,
                    file_path=str(file_path),
                    line_start=0,
                    line_end=0,
                    function_name=function_name,
                    scanner=ScannerType.SEMGREP,
                    scan_status='failed',
                    failure_reason=f"File does not exist: {file_path}",
                    severity='',
                    description=''
                )
                failure_records.append(vuln)
            
            return failure_records
        
        logger.info(f"掃描單一檔案: {file_path} (CWE-{cwe})")
        
        all_vulns = []
        
        # Bandit 掃描
        if ScannerType.BANDIT in self.available_scanners and cwe in self.BANDIT_BY_CWE:
            tests = self.BANDIT_BY_CWE[cwe]
            
            # 決定 OriginalScanResult 的保存位置
            if project_name and round_number:
                # 函式級別掃描：OriginalScanResult/Bandit/CWE-{cwe}/{project_name}/第N輪/
                original_output_dir = self.bandit_original_dir / f"CWE-{cwe}" / project_name / f"第{round_number}輪"
                original_output_dir.mkdir(parents=True, exist_ok=True)
                
                # 使用目錄前綴和函式名稱來命名，避免不同目錄下的同名檔案衝突
                file_parts = file_path.parts
                if len(file_parts) >= 2:
                    base_name = f"{file_parts[-2]}__{file_parts[-1]}"
                else:
                    base_name = file_path.name
                
                # 如果有函式名稱，加入到檔案名中
                if function_name:
                    safe_filename = f"{base_name}__{function_name}_report.json"
                else:
                    safe_filename = f"{base_name}_report.json"
                    
                original_output_file = original_output_dir / safe_filename
            else:
                # 單檔掃描：OriginalScanResult/Bandit/single_file/CWE-{cwe}/
                original_output_dir = self.bandit_original_dir / "single_file" / f"CWE-{cwe}"
                original_output_dir.mkdir(parents=True, exist_ok=True)
                
                # 如果有函式名稱，加入到檔案名中
                if function_name:
                    original_output_file = original_output_dir / f"{file_path.name}__{function_name}_report.json"
                else:
                    original_output_file = original_output_dir / f"{file_path.name}_report.json"
            
            bandit_cmd = ".venv/bin/bandit" if self._check_command(".venv/bin/bandit") else "bandit"
            cmd = [bandit_cmd, str(file_path), "-t", tests, "-f", "json", "-o", str(original_output_file)]
            
            try:
                subprocess.run(cmd, capture_output=True, timeout=60)
                if original_output_file.exists():
                    vulns = self._parse_bandit_results(original_output_file, cwe, function_name)
                    all_vulns.extend(vulns)
                    logger.debug(f"✅ 原始報告已保存: {original_output_file}")
            except Exception as e:
                logger.error(f"Bandit 單檔掃描失敗: {e}")
        
        # Semgrep 掃描
        if ScannerType.SEMGREP in self.available_scanners and cwe in self.SEMGREP_BY_CWE:
            rule_patterns = self.SEMGREP_BY_CWE[cwe]
            
            # 將規則字符串分割成列表（支援逗號分隔的多個規則）
            if isinstance(rule_patterns, str):
                rule_list = [r.strip() for r in rule_patterns.split(",")]
            else:
                rule_list = rule_patterns
            
            # 決定 OriginalScanResult 的保存位置
            if project_name and round_number:
                # 函式級別掃描：OriginalScanResult/Semgrep/CWE-{cwe}/{project_name}/第N輪/
                original_output_dir = self.semgrep_original_dir / f"CWE-{cwe}" / project_name / f"第{round_number}輪"
                original_output_dir.mkdir(parents=True, exist_ok=True)
                
                # 使用目錄前綴和函式名稱來命名，避免不同目錄下的同名檔案衝突
                file_parts = file_path.parts
                if len(file_parts) >= 2:
                    base_name = f"{file_parts[-2]}__{file_parts[-1]}"
                else:
                    base_name = file_path.name
                
                # 如果有函式名稱，加入到檔案名中
                if function_name:
                    safe_filename = f"{base_name}__{function_name}_report.json"
                else:
                    safe_filename = f"{base_name}_report.json"
                    
                original_output_file = original_output_dir / safe_filename
            else:
                # 單檔掃描：OriginalScanResult/Semgrep/single_file/CWE-{cwe}/
                original_output_dir = self.semgrep_original_dir / "single_file" / f"CWE-{cwe}"
                original_output_dir.mkdir(parents=True, exist_ok=True)
                
                # 如果有函式名稱，加入到檔案名中
                if function_name:
                    original_output_file = original_output_dir / f"{file_path.name}__{function_name}_report.json"
                else:
                    original_output_file = original_output_dir / f"{file_path.name}_report.json"
            
            # 構建 Semgrep 命令
            semgrep_cmd = ".venv/bin/semgrep" if self._check_command(".venv/bin/semgrep") else "semgrep"
            cmd = [semgrep_cmd, "scan"]
            
            # 添加規則
            for rule in rule_list:
                if rule.startswith('p/') or rule.startswith('r/'):
                    cmd.extend(["--config", rule])
                else:
                    cmd.extend(["--config", f"r/{rule}"])
            
            cmd.extend([
                "--json",
                "--output", str(original_output_file),
                "--quiet",
                "--disable-version-check",
                "--metrics", "off",
                str(file_path)
            ])
            
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)
                
                if original_output_file.exists():
                    vulns = self._parse_semgrep_results(original_output_file, cwe, file_path, function_name)
                    all_vulns.extend(vulns)
                    logger.debug(f"✅ Semgrep 原始報告已保存: {original_output_file}")
                else:
                    # 掃描失敗：沒有產生輸出檔案
                    logger.warning(f"Semgrep 掃描失敗，未產生輸出檔案 (return code: {result.returncode})")
                    
                    # 創建失敗記錄
                    error_msg = result.stderr.strip() if result.stderr else "No output file generated"
                    vuln = CWEVulnerability(
                        cwe_id=cwe,
                        file_path=str(file_path),
                        line_start=0,
                        line_end=0,
                        function_name=function_name,
                        scanner=ScannerType.SEMGREP,
                        scan_status='failed',
                        failure_reason=f"Semgrep failed to generate output (code {result.returncode}): {error_msg[:200]}",
                        severity='',
                        description=''
                    )
                    all_vulns.append(vuln)
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Semgrep 單檔掃描超時: {file_path}")
                
                # 創建超時失敗記錄
                vuln = CWEVulnerability(
                    cwe_id=cwe,
                    file_path=str(file_path),
                    line_start=0,
                    line_end=0,
                    function_name=function_name,
                    scanner=ScannerType.SEMGREP,
                    scan_status='failed',
                    failure_reason="Semgrep scan timeout (60 seconds)",
                    severity='',
                    description=''
                )
                all_vulns.append(vuln)
                
            except Exception as e:
                logger.error(f"Semgrep 單檔掃描失敗: {e}")
                
                # 創建失敗記錄
                vuln = CWEVulnerability(
                    cwe_id=cwe,
                    file_path=str(file_path),
                    line_start=0,
                    line_end=0,
                    function_name=function_name,
                    scanner=ScannerType.SEMGREP,
                    scan_status='failed',
                    failure_reason=f"Semgrep scan exception: {str(e)}",
                    severity='',
                    description=''
                )
                all_vulns.append(vuln)
        
        logger.info(f"單檔掃描完成，發現 {len(all_vulns)} 個漏洞")
        return all_vulns


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

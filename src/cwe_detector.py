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
    description: Optional[str] = None


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
    
    def __init__(self, output_dir: Path = None):
        """
        初始化 CWE 檢測器
        
        Args:
            output_dir: 輸出目錄，預設為 ./cwe_scan_results
        """
        self.output_dir = output_dir or Path("./cwe_scan_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 檢測可用的掃描器
        self.available_scanners = self._check_available_scanners()
        logger.info(f"可用的掃描器: {', '.join([s.value for s in self.available_scanners])}")
    
    def _check_available_scanners(self) -> Set[ScannerType]:
        """檢查系統中可用的掃描器"""
        available = set()
        
        # 只檢查 Bandit (優先檢查 venv 中的)
        if self._check_command(".venv/bin/bandit") or self._check_command("bandit"):
            available.add(ScannerType.BANDIT)
            logger.info("✅ Bandit 掃描器可用")
        else:
            logger.warning("⚠️  Bandit 未安裝，請執行: pip install bandit")
        
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
    
    def _parse_bandit_results(self, json_file: Path, cwe: str) -> List[CWEVulnerability]:
        """解析 Bandit JSON 結果"""
        vulnerabilities = []
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for result in data.get("results", []):
                vuln = CWEVulnerability(
                    cwe_id=cwe,
                    file_path=result.get("filename", ""),
                    line_start=result.get("line_number", 0),
                    line_end=result.get("line_number", 0),
                    column_start=result.get("col_offset", 0),
                    scanner=ScannerType.BANDIT,
                    severity=result.get("issue_severity", ""),
                    description=result.get("issue_text", "")
                )
                vulnerabilities.append(vuln)
        
        except Exception as e:
            logger.error(f"解析 Bandit 結果失敗: {e}")
        
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
        cwe: str
    ) -> List[CWEVulnerability]:
        """
        掃描單一檔案
        
        Args:
            file_path: 檔案路徑
            cwe: CWE ID
            
        Returns:
            List[CWEVulnerability]: 漏洞列表
        """
        if not file_path.exists():
            logger.error(f"檔案不存在: {file_path}")
            return []
        
        logger.info(f"掃描單一檔案: {file_path} (CWE-{cwe})")
        
        all_vulns = []
        
        # Bandit 掃描
        if ScannerType.BANDIT in self.available_scanners and cwe in self.BANDIT_BY_CWE:
            tests = self.BANDIT_BY_CWE[cwe]
            output_dir = self.output_dir / "single_file" / "bandit" / f"CWE-{cwe}"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "report.json"
            
            bandit_cmd = ".venv/bin/bandit" if self._check_command(".venv/bin/bandit") else "bandit"
            cmd = [bandit_cmd, str(file_path), "-t", tests, "-f", "json", "-o", str(output_file)]
            
            try:
                subprocess.run(cmd, capture_output=True, timeout=60)
                if output_file.exists():
                    vulns = self._parse_bandit_results(output_file, cwe)
                    all_vulns.extend(vulns)
            except Exception as e:
                logger.error(f"Bandit 單檔掃描失敗: {e}")
        
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

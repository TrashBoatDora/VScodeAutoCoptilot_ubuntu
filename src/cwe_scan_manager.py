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
        
        支援的格式：
        - 請幫我定位到 app/backend/routes/storage.py 的函式
        - 請檢查 src/utils/helper.py 中的程式碼
        - 請修改 path/to/file.py
        
        Args:
            prompt_content: prompt 內容
            
        Returns:
            List[str]: 提取到的檔案路徑列表
        """
        file_paths = []
        
        # 正則表達式模式，匹配常見的檔案路徑格式
        patterns = [
            r'(?:定位到|檢查|修改|幫我|請|到)\s*([a-zA-Z0-9_/\-\.]+\.py)',  # 中文描述
            r'(?:file|path|in|at)\s*([a-zA-Z0-9_/\-\.]+\.py)',  # 英文描述
            r'([a-zA-Z0-9_]+(?:/[a-zA-Z0-9_]+)*\.py)',  # 直接的檔案路徑
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, prompt_content, re.IGNORECASE)
            for match in matches:
                # 清理路徑
                cleaned_path = match.strip()
                if cleaned_path and cleaned_path not in file_paths:
                    file_paths.append(cleaned_path)
        
        self.logger.info(f"從 prompt 中提取到 {len(file_paths)} 個檔案路徑")
        for path in file_paths:
            self.logger.debug(f"  - {path}")
        
        return file_paths
    
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
            
            # 使用 CWEDetector 掃描單一檔案
            vulnerabilities = self.detector.scan_single_file(full_path, cwe_type)
            
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
    
    def save_scan_results(
        self,
        project_name: str,
        cwe_type: str,
        scan_results: List[ScanResult],
        timestamp: datetime = None
    ) -> Tuple[Path, Path]:
        """
        儲存掃描結果到 CSV
        
        Args:
            project_name: 專案名稱
            cwe_type: CWE 類型
            scan_results: 掃描結果列表
            timestamp: 時間戳記（可選）
            
        Returns:
            Tuple[Path, Path]: (掃描結果檔案路徑, 統計檔案路徑)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # 建立 CWE 類型目錄
        cwe_dir = self.output_dir / f"CWE-{cwe_type}"
        cwe_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 儲存掃描詳細結果
        scan_file = cwe_dir / f"{project_name}_scan.csv"
        self._save_scan_detail_csv(scan_file, scan_results)
        
        # 2. 更新統計資料
        statistics_file = cwe_dir / "statistics.csv"
        self._update_statistics_csv(statistics_file, project_name, scan_results)
        
        self.logger.info(f"掃描結果已儲存:")
        self.logger.info(f"  - 詳細結果: {scan_file}")
        self.logger.info(f"  - 統計資料: {statistics_file}")
        
        return scan_file, statistics_file
    
    def _save_scan_detail_csv(self, file_path: Path, scan_results: List[ScanResult]):
        """
        儲存掃描詳細結果到 CSV
        
        格式:
        檔案名稱,是否有CWE漏洞
        app/backend/routes/storage.py,true
        app/backend/routes/auth.py,false
        """
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # 寫入標題
            writer.writerow(['檔案名稱', '是否有CWE漏洞'])
            
            # 寫入資料
            for result in scan_results:
                has_vuln = 'true' if result.has_vulnerability else 'false'
                writer.writerow([result.file_path, has_vuln])
        
        self.logger.debug(f"詳細掃描結果已寫入: {file_path}")
    
    def _update_statistics_csv(self, file_path: Path, project_name: str, scan_results: List[ScanResult]):
        """
        更新或建立統計 CSV 檔案
        
        格式:
        專案名稱,不安全數量,安全數量,共計
        project1,5,10,15
        project2,2,8,10
        總計,7,18,25
        """
        # 計算本次掃描統計
        unsafe_count = sum(1 for r in scan_results if r.has_vulnerability)
        safe_count = sum(1 for r in scan_results if not r.has_vulnerability)
        total_count = len(scan_results)
        
        # 讀取現有資料
        existing_data = []
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 跳過總計行
                    if row['專案名稱'] != '總計':
                        existing_data.append(row)
        
        # 更新或追加專案資料
        project_found = False
        for row in existing_data:
            if row['專案名稱'] == project_name:
                # 更新現有專案的資料（追加模式）
                row['不安全數量'] = str(int(row['不安全數量']) + unsafe_count)
                row['安全數量'] = str(int(row['安全數量']) + safe_count)
                row['共計'] = str(int(row['共計']) + total_count)
                project_found = True
                break
        
        if not project_found:
            # 追加新專案
            existing_data.append({
                '專案名稱': project_name,
                '不安全數量': str(unsafe_count),
                '安全數量': str(safe_count),
                '共計': str(total_count)
            })
        
        # 計算總計
        total_unsafe = sum(int(row['不安全數量']) for row in existing_data)
        total_safe = sum(int(row['安全數量']) for row in existing_data)
        total_all = sum(int(row['共計']) for row in existing_data)
        
        # 寫入檔案
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # 寫入標題
            writer.writerow(['專案名稱', '不安全數量', '安全數量', '共計'])
            
            # 寫入專案資料
            for row in existing_data:
                writer.writerow([
                    row['專案名稱'],
                    row['不安全數量'],
                    row['安全數量'],
                    row['共計']
                ])
            
            # 寫入總計行
            writer.writerow(['總計', total_unsafe, total_safe, total_all])
        
        self.logger.debug(f"統計資料已更新: {file_path}")
        self.logger.info(f"專案 {project_name}: 不安全={unsafe_count}, 安全={safe_count}, 共計={total_count}")
    
    def scan_from_prompt(
        self,
        project_path: Path,
        project_name: str,
        prompt_content: str,
        cwe_type: str
    ) -> Tuple[bool, Optional[Tuple[Path, Path]]]:
        """
        從 prompt 內容執行完整的掃描流程
        
        Args:
            project_path: 專案路徑
            project_name: 專案名稱
            prompt_content: prompt 內容
            cwe_type: CWE 類型
            
        Returns:
            Tuple[bool, Optional[Tuple[Path, Path]]]: (是否成功, (掃描結果檔案, 統計檔案))
        """
        try:
            self.logger.create_separator(f"CWE-{cwe_type} 掃描: {project_name}")
            
            # 步驟1: 從 prompt 提取檔案路徑
            file_paths = self.extract_file_paths_from_prompt(prompt_content)
            
            if not file_paths:
                self.logger.warning("未從 prompt 中提取到任何檔案路徑")
                return False, None
            
            # 步驟2: 執行掃描
            scan_results = self.scan_files(project_path, file_paths, cwe_type)
            
            # 步驟3: 儲存結果
            result_files = self.save_scan_results(project_name, cwe_type, scan_results)
            
            # 步驟4: 輸出摘要
            total_files = len(scan_results)
            unsafe_files = sum(1 for r in scan_results if r.has_vulnerability)
            safe_files = total_files - unsafe_files
            
            self.logger.create_separator(f"掃描完成: {project_name}")
            self.logger.info(f"掃描檔案數: {total_files}")
            self.logger.info(f"發現漏洞: {unsafe_files} 個檔案")
            self.logger.info(f"安全檔案: {safe_files} 個")
            
            return True, result_files
            
        except Exception as e:
            self.logger.error(f"掃描過程發生錯誤: {e}")
            return False, None


# 全域實例
cwe_scan_manager = CWEScanManager()

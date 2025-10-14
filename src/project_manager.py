# -*- coding: utf-8 -*-
"""
Hybrid UI Automation Script - 專案管理模組
處理專案資料夾掃描、狀態檢查、批次處理邏輯
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

# 導入配置和日誌
sys.path.append(str(Path(__file__).parent.parent))
from config.config import config
from src.logger import get_logger

@dataclass
class ProjectInfo:
    """專案資訊數據類"""
    name: str
    path: str
    status: str = "pending"  # pending, processing, completed, failed, skipped
    has_copilot_file: bool = False
    file_count: int = 0
    supported_files: List[str] = None
    last_processed: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    retry_count: int = 0
    
    # 新增：專案專用提示詞相關欄位
    has_custom_prompt: bool = False  # 是否有專案專用的 prompt.txt
    prompt_lines_count: int = 0      # 專案提示詞的行數
    prompt_file_size: int = 0        # 提示詞檔案大小（bytes）
    prompt_file_path: Optional[str] = None  # 提示詞檔案路徑
    
    def __post_init__(self):
        if self.supported_files is None:
            self.supported_files = []
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectInfo':
        """從字典創建實例"""
        return cls(**data)

class ProjectManager:
    """專案管理器"""
    
    # 支援的程式語言副檔名
    SUPPORTED_EXTENSIONS = {
        '.py': 'Python',
        '.c': 'C',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.c++': 'C++',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.go': 'Go',
        '.java': 'Java'
    }
    
    def __init__(self, projects_root: Path = None):
        """
        初始化專案管理器
        
        Args:
            projects_root: 專案根目錄路徑
        """
        self.logger = get_logger("ProjectManager")
        self.projects_root = projects_root or config.PROJECTS_DIR
        self.projects: List[ProjectInfo] = []
        self.status_file = self.projects_root / "automation_status.json"
        
        self.logger.info(f"專案管理器初始化 - 根目錄: {self.projects_root}")
        
        # 確保專案目錄存在
        self.projects_root.mkdir(parents=True, exist_ok=True)
    
    def scan_projects(self) -> List[ProjectInfo]:
        """
        掃描專案目錄，發現所有專案
        
        Returns:
            List[ProjectInfo]: 專案資訊列表
        """
        self.logger.info("開始掃描專案目錄...")
        
        self.projects = []
        
        try:
            # 遍歷專案根目錄下的所有子目錄
            for item in self.projects_root.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    project_info = self._analyze_project(item)
                    if project_info:
                        self.projects.append(project_info)
            
            self.logger.info(f"掃描完成，發現 {len(self.projects)} 個專案")
            
            # 載入之前的狀態
            self._load_status()
            
            return self.projects
            
        except Exception as e:
            self.logger.error(f"掃描專案時發生錯誤: {str(e)}")
            return []
    
    def _analyze_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """
        分析單一專案
        
        Args:
            project_path: 專案路徑
            
        Returns:
            Optional[ProjectInfo]: 專案資訊，若不是有效專案則返回 None
        """
        try:
            project_name = project_path.name
            supported_files = []
            file_count = 0
            
            # 遞迴搜尋支援的檔案類型
            for ext in self.SUPPORTED_EXTENSIONS:
                files = list(project_path.rglob(f"*{ext}"))
                if files:
                    for file_path in files:
                        supported_files.append(str(file_path.relative_to(project_path)))
                    file_count += len(files)
            
            # 分析專案專用提示詞
            prompt_info = self._analyze_project_prompt(project_path)
            
            # 檢查是否已有多輪互動處理結果（檢查統一的 ExecutionResult/Success 資料夾）
            script_root = Path(__file__).parent.parent  # 腳本根目錄
            execution_result_dir = script_root / "ExecutionResult" / "Success"
            project_result_dir = execution_result_dir / project_name
            
            # 只檢查多輪互動檔案格式
            has_copilot_file = (project_result_dir.exists() and 
                              any(project_result_dir.glob("*_第*輪.md")))
            
            # 如果沒有支援的檔案，跳過此專案
            if file_count == 0:
                self.logger.debug(f"跳過專案 {project_name}：沒有支援的程式檔案")
                return None
            
            project_info = ProjectInfo(
                name=project_name,
                path=str(project_path),
                has_copilot_file=has_copilot_file,
                file_count=file_count,
                supported_files=supported_files,
                status="completed" if has_copilot_file else "pending",
                # 加入專案提示詞資訊
                has_custom_prompt=prompt_info["has_custom_prompt"],
                prompt_lines_count=prompt_info["prompt_lines_count"],
                prompt_file_size=prompt_info["prompt_file_size"],
                prompt_file_path=prompt_info["prompt_file_path"]
            )
            
            self.logger.debug(f"分析專案 {project_name}: {file_count} 個檔案, 狀態: {project_info.status}")
            
            return project_info
            
        except Exception as e:
            self.logger.error(f"分析專案 {project_path} 時發生錯誤: {str(e)}")
            return None
    
    def _analyze_project_prompt(self, project_path: Path) -> Dict:
        """
        分析專案的提示詞檔案資訊
        
        Args:
            project_path: 專案路徑
            
        Returns:
            Dict: 包含提示詞資訊的字典
        """
        from config.config import config
        
        prompt_info = {
            "has_custom_prompt": False,
            "prompt_lines_count": 0,
            "prompt_file_size": 0,
            "prompt_file_path": None
        }
        
        try:
            # 取得專案提示詞檔案路徑
            prompt_file_path = config.get_project_prompt_path(str(project_path))
            
            if prompt_file_path.exists():
                prompt_info["has_custom_prompt"] = True
                prompt_info["prompt_file_path"] = str(prompt_file_path)
                prompt_info["prompt_file_size"] = prompt_file_path.stat().st_size
                
                # 計算提示詞行數
                try:
                    with open(prompt_file_path, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f.readlines() if line.strip()]
                    prompt_info["prompt_lines_count"] = len(lines)
                    
                    self.logger.debug(f"專案 {project_path.name} 提示詞分析: "
                                    f"{len(lines)} 行, {prompt_info['prompt_file_size']} bytes")
                except Exception as e:
                    self.logger.warning(f"讀取專案 {project_path.name} 提示詞檔案失敗: {str(e)}")
                    prompt_info["prompt_lines_count"] = 0
            else:
                self.logger.debug(f"專案 {project_path.name} 沒有專案專用提示詞檔案")
        
        except Exception as e:
            self.logger.error(f"分析專案 {project_path.name} 提示詞時發生錯誤: {str(e)}")
        
        return prompt_info
    
    def get_pending_projects(self) -> List[ProjectInfo]:
        """
        取得待處理的專案列表
        
        Returns:
            List[ProjectInfo]: 待處理專案列表
        """
        pending = [p for p in self.projects if p.status == "pending"]
        self.logger.info(f"待處理專案數量: {len(pending)}")
        return pending
    
    def get_failed_projects(self) -> List[ProjectInfo]:
        """
        取得失敗的專案列表
        
        Returns:
            List[ProjectInfo]: 失敗專案列表
        """
        failed = [p for p in self.projects if p.status == "failed"]
        self.logger.info(f"失敗專案數量: {len(failed)}")
        return failed
    
    def get_completed_projects(self) -> List[ProjectInfo]:
        """
        取得已完成的專案列表
        
        Returns:
            List[ProjectInfo]: 已完成專案列表
        """
        completed = [p for p in self.projects if p.status == "completed"]
        self.logger.info(f"已完成專案數量: {len(completed)}")
        return completed
    
    def get_all_pending_projects(self) -> List[ProjectInfo]:
        """
        取得所有待處理的專案
        
        Returns:
            List[ProjectInfo]: 所有待處理的專案列表
        """
        pending_projects = self.get_pending_projects()
        self.logger.info(f"找到 {len(pending_projects)} 個待處理專案")
        return pending_projects
    
    def update_project_status(self, project_name: str, status: str, 
                             error_message: str = None, processing_time: float = None) -> bool:
        """
        更新專案狀態
        
        Args:
            project_name: 專案名稱
            status: 新狀態
            error_message: 錯誤訊息（如果有）
            processing_time: 處理時間（秒）
            
        Returns:
            bool: 更新是否成功
        """
        try:
            for project in self.projects:
                if project.name == project_name:
                    project.status = status
                    project.last_processed = datetime.now().isoformat()
                    
                    if error_message:
                        project.error_message = error_message
                    
                    if processing_time:
                        project.processing_time = processing_time
                    
                    # 如果是失敗狀態，增加重試計數
                    if status == "failed":
                        project.retry_count += 1
                    
                    # 儲存狀態
                    self._save_status()
                    
                    self.logger.debug(f"更新專案 {project_name} 狀態為 {status}")
                    return True
            
            self.logger.warning(f"找不到專案: {project_name}")
            return False
            
        except Exception as e:
            self.logger.error(f"更新專案狀態時發生錯誤: {str(e)}")
            return False
    
    def mark_project_completed(self, project_name: str, processing_time: float = None) -> bool:
        """
        標記專案為已完成
        
        Args:
            project_name: 專案名稱
            processing_time: 處理時間
            
        Returns:
            bool: 標記是否成功
        """
        # 重新檢查是否真的有多輪互動檔案（檢查統一的 ExecutionResult/Success 資料夾）
        project = self.get_project_by_name(project_name)
        if project:
            script_root = Path(__file__).parent.parent  # 腳本根目錄
            execution_result_dir = script_root / "ExecutionResult" / "Success"
            project_result_dir = execution_result_dir / project_name
            
            # 檢查多輪互動檔案格式（支援多種格式，包含子目錄）
            has_success_file = False
            has_files = 0
            
            if project_result_dir.exists():
                # 檢查直接在目錄下的檔案
                direct_files = list(project_result_dir.glob("*_第*輪.md")) + list(project_result_dir.glob("*_第*輪_第*行.md"))
                # 檢查子目錄（第1輪/、第2輪/ 等）內的檔案
                subdir_files = list(project_result_dir.glob("第*輪/*_第*行.md"))
                # 遞迴檢查所有 .md 檔案
                all_md_files = list(project_result_dir.rglob("*.md"))
                
                has_success_file = len(direct_files) > 0 or len(subdir_files) > 0
                has_files = len(all_md_files)
            
            self.logger.info(f"結果檔案驗證 - 目錄存在: {project_result_dir.exists()}, "
                             f"檔案數量: {has_files}, 多輪互動檔案: {has_success_file}")
            
            if has_success_file:
                project.has_copilot_file = True
                return self.update_project_status(project_name, "completed", None, processing_time)
            else:
                self.logger.warning(f"專案 {project_name} 缺少成功執行結果檔案")
                return self.update_project_status(project_name, "failed", "缺少結果檔案", processing_time)
        
        return False
    
    def mark_project_failed(self, project_name: str, error_message: str, processing_time: float = None) -> bool:
        """
        標記專案為失敗
        
        Args:
            project_name: 專案名稱
            error_message: 錯誤訊息
            processing_time: 處理時間
            
        Returns:
            bool: 標記是否成功
        """
        return self.update_project_status(project_name, "failed", error_message, processing_time)
    
    def get_project_by_name(self, project_name: str) -> Optional[ProjectInfo]:
        """
        根據名稱取得專案資訊
        
        Args:
            project_name: 專案名稱
            
        Returns:
            Optional[ProjectInfo]: 專案資訊，若找不到則返回 None
        """
        for project in self.projects:
            if project.name == project_name:
                return project
        return None
    
    def should_retry_project(self, project_name: str, max_retries: int = None) -> bool:
        """
        判斷專案是否應該重試
        
        Args:
            project_name: 專案名稱
            max_retries: 最大重試次數
            
        Returns:
            bool: 是否應該重試
        """
        if max_retries is None:
            max_retries = config.MAX_RETRY_ATTEMPTS
        
        project = self.get_project_by_name(project_name)
        if project and project.status == "failed":
            return project.retry_count < max_retries
        
        return False
    
    def get_retry_projects(self, max_retries: int = None) -> List[ProjectInfo]:
        """
        取得需要重試的專案列表
        
        Args:
            max_retries: 最大重試次數
            
        Returns:
            List[ProjectInfo]: 需要重試的專案列表
        """
        if max_retries is None:
            max_retries = config.MAX_RETRY_ATTEMPTS
        
        retry_projects = []
        for project in self.projects:
            if project.status == "failed" and project.retry_count < max_retries:
                retry_projects.append(project)
        
        self.logger.info(f"需要重試的專案數量: {len(retry_projects)}")
        return retry_projects
    
    def generate_summary_report(self) -> Dict:
        """
        生成專案處理摘要報告
        
        Returns:
            Dict: 摘要報告
        """
        total = len(self.projects)
        completed = len(self.get_completed_projects())
        failed = len(self.get_failed_projects())
        pending = len(self.get_pending_projects())
        
        # 計算總處理時間
        total_time = sum(p.processing_time for p in self.projects if p.processing_time)
        
        # 計算成功率
        processed = completed + failed
        success_rate = (completed / processed * 100) if processed > 0 else 0
        
        report = {
            "總專案數": total,
            "已完成": completed,
            "失敗": failed,
            "待處理": pending,
            "成功率": f"{success_rate:.1f}%",
            "總處理時間": f"{total_time:.2f}秒",
            "平均處理時間": f"{total_time/processed:.2f}秒" if processed > 0 else "N/A",
            "生成時間": datetime.now().isoformat()
        }
        
        return report
    
    def save_summary_report(self) -> str:
        """
        儲存摘要報告到檔案
        
        Returns:
            str: 報告檔案路徑
        """
        report = self.generate_summary_report()
        
        # 建立統一的 ExecutionResult/AutomationReport 資料夾
        script_root = Path(__file__).parent.parent  # 腳本根目錄
        report_dir = script_root / "ExecutionResult" / "AutomationReport"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"automation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"摘要報告已儲存: {report_file}")
            return str(report_file)
            
        except Exception as e:
            self.logger.error(f"儲存摘要報告失敗: {str(e)}")
            return ""
    
    def _save_status(self):
        """儲存專案狀態到檔案"""
        try:
            status_data = {
                "last_updated": datetime.now().isoformat(),
                "projects": [project.to_dict() for project in self.projects]
            }
            
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"儲存狀態檔案失敗: {str(e)}")
    
    def _load_status(self):
        """從檔案載入專案狀態"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
                
                # 合併已載入的狀態
                saved_projects = {p["name"]: ProjectInfo.from_dict(p) 
                                for p in status_data.get("projects", [])}
                
                for project in self.projects:
                    if project.name in saved_projects:
                        saved_project = saved_projects[project.name]
                        project.status = saved_project.status
                        project.last_processed = saved_project.last_processed
                        project.error_message = saved_project.error_message
                        project.processing_time = saved_project.processing_time
                        project.retry_count = saved_project.retry_count
                
                self.logger.info("專案狀態載入完成")
                
        except Exception as e:
            self.logger.error(f"載入狀態檔案失敗: {str(e)}")
    
    def validate_projects_for_custom_prompts(self) -> Tuple[bool, List[str]]:
        """
        驗證所有專案是否都有 prompt.txt（當使用專案專用提示詞模式時）
        
        Returns:
            Tuple[bool, List[str]]: (是否全部都有, 缺少 prompt.txt 的專案名稱列表)
        """
        missing_prompts = []
        
        for project in self.projects:
            if not project.has_custom_prompt:
                missing_prompts.append(project.name)
        
        all_have_prompts = len(missing_prompts) == 0
        
        self.logger.info(f"專案提示詞驗證結果 - 全部有效: {all_have_prompts}, "
                        f"缺少提示詞的專案: {len(missing_prompts)}")
        
        return all_have_prompts, missing_prompts
    
    def get_projects_with_custom_prompts(self) -> List[ProjectInfo]:
        """取得有專案專用提示詞的專案列表"""
        projects_with_prompts = [p for p in self.projects if p.has_custom_prompt]
        self.logger.info(f"有專案專用提示詞的專案數量: {len(projects_with_prompts)}")
        return projects_with_prompts
    
    def get_project_prompt_summary(self) -> Dict:
        """
        取得專案提示詞摘要資訊
        
        Returns:
            Dict: 包含統計資訊的字典
        """
        total_projects = len(self.projects)
        projects_with_prompts = len([p for p in self.projects if p.has_custom_prompt])
        total_prompt_lines = sum(p.prompt_lines_count for p in self.projects if p.has_custom_prompt)
        
        return {
            "total_projects": total_projects,
            "projects_with_prompts": projects_with_prompts,
            "projects_without_prompts": total_projects - projects_with_prompts,
            "total_prompt_lines": total_prompt_lines,
            "average_lines_per_project": total_prompt_lines / max(1, projects_with_prompts)
        }

# 創建全域實例
project_manager = ProjectManager()

# 便捷函數
def scan_all_projects() -> List[ProjectInfo]:
    """掃描所有專案的便捷函數"""
    return project_manager.scan_projects()

def get_pending_projects() -> List[ProjectInfo]:
    """取得待處理專案的便捷函數"""
    return project_manager.get_pending_projects()

def get_all_pending_projects() -> List[ProjectInfo]:
    """取得所有待處理專案的便捷函數"""
    return project_manager.get_all_pending_projects()
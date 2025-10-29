# -*- coding: utf-8 -*-
"""
Copilot Rate Limit Handler - 簡單的回應檢測和重試機制
"""

import time
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from src.logger import get_logger


COMPLETION_MARKER = "已完成回答"
COMPLETION_MARKER_en = "Response completed"
_COMPLETION_TRAILING_CHARS = ' \t\r\n"""\'\'」』】》）〉>。、.!?;；:、…'

# Copilot 自動追加的後綴內容列表（需要清理）
_COPILOT_AUTO_SUFFIXES = [
    "Made changes.",
    "Made changes",
]


def _clean_copilot_response(response: str) -> str:
    """
    清理 Copilot 回應中的自動追加內容
    
    Args:
        response: 原始回應內容
        
    Returns:
        str: 清理後的回應內容
    """
    if not response:
        return response
    
    cleaned = response.strip()
    
    # 反覆移除已知的 Copilot 自動後綴，直到無法再移除為止
    # 處理多個重複的 "Made changes." 情況
    changed = True
    while changed:
        changed = False
        for suffix in _COPILOT_AUTO_SUFFIXES:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].rstrip()
                changed = True  # 繼續檢查是否還有更多後綴
                break  # 重新開始檢查（因為 rstrip 後長度已改變）
    
    return cleaned


def is_response_incomplete(response: str) -> bool:
    """
    檢查回應是否完成。

    先清理 Copilot 自動追加的內容（如 "Made changes."），
    然後檢查回應是否以「已完成回答」結尾（允許尾端存在空白或常見標點符號），
    否則視為不完整，需要重試。
    """
    if not response:
        return True

    # 先清理 Copilot 自動追加的內容
    cleaned = _clean_copilot_response(response)
    if not cleaned:
        return True

    # 去除尾端空白和標點符號
    normalized = cleaned.rstrip(_COMPLETION_TRAILING_CHARS)
    
    # 檢查是否以完成標記結尾
    if normalized.endswith(COMPLETION_MARKER) or normalized.endswith(COMPLETION_MARKER_en):
        return False

    return True


def wait_and_retry(seconds: int, line_number: int, round_number: int, logger, retry_count: int = 0):
    """
    等待指定時間並顯示倒數
    
    Args:
        seconds: 等待秒數
        line_number: 提示詞行號
        round_number: 互動輪數
        logger: 日誌記錄器
        retry_count: 當前是第幾次重試
    """
    logger.warning(f"⏳ 回應不完整，等待 {seconds} 秒後重試 [輪次: {round_number}, 行號: {line_number}, 重試: {retry_count}]")
    
    # 每60秒顯示一次進度
    remaining = seconds
    while remaining > 0:
        chunk = min(60, remaining)
        if remaining == seconds:
            logger.info(f"   開始等待 {seconds} 秒...")
        else:
            logger.info(f"   剩餘 {remaining} 秒...")
        time.sleep(chunk)
        remaining -= chunk
    
    logger.info(f"   ✓ 等待完成，準備第 {retry_count + 1} 次重試")

# File Limit Bug Analysis - Non-AS Mode

## Issue Summary
文件限制設為 1，但實際處理了 2 個函數（prompt.txt 中的 2 行）

## Root Cause

### Main.py Flow (Lines 300-495)

```python
# Line 304-332: Check file limit BEFORE processing
if self.max_files_limit > 0:
    project_file_count = config.count_project_prompt_lines(project.path)  # Counts ALL lines
    remaining_quota = self.max_files_limit - self.total_files_processed
    
    if project_file_count > remaining_quota:
        self.logger.info(f"將只處理前 {remaining_quota} 個檔案")  # ❌ Only logs! Doesn't enforce!
    
# Line 336: Process project WITHOUT passing the limit
success = self._process_single_project(project)  # No max_lines parameter!

# Line 480-495: Update counter AFTER processing
if interaction_enabled:
    # Counts the FULL prompt.txt AFTER processing is done
    files_in_project = config.count_project_prompt_lines(project.path)
    self.total_files_processed += files_in_project  # ❌ Adds ALL lines, not limited lines
```

**Problem**: 
1. The `remaining_quota` is calculated but NEVER passed down
2. Processing functions read ALL lines from prompt.txt
3. Counter is updated with ALL lines AFTER processing

### Example with User's Test

**Setup**:
- max_files_limit = 1
- total_files_processed = 0 (start)
- Project: aider__CWE-327__CAL-ALL-6b42874e__M-call
- prompt.txt has 2 lines

**Execution**:
1. Line 323: `remaining_quota = 1 - 0 = 1`
2. Line 327: Logs "將只處理前 1 個檔案" (but doesn't enforce!)
3. Line 336: Calls `_process_single_project(project)` with no limit
4. Processing: Reads ALL 2 lines from prompt.txt and processes both
5. Line 482: `files_in_project = 2` (counts full file)
6. Line 482: `self.total_files_processed += 2` → total becomes 2
7. Report shows: "檔案處理限制: 1, 實際處理函數數: 2" ❌

## Solution Options

### Option 1: Pass remaining_quota down (Complex)
```python
# main.py line 323-336
remaining_quota = self.max_files_limit - self.total_files_processed
success = self._process_single_project(project, max_lines=remaining_quota)

# copilot_handler.py - add max_lines parameter to:
- process_project_complete()
- process_project_with_iterations()
- _send_prompt_lines() or similar

# When reading prompt.txt:
prompt_lines = [line.strip() for line in f.readlines() if line.strip()][:max_lines]
```

**Pros**: Precise control
**Cons**: Need to modify multiple functions, complex refactoring

### Option 2: Slice prompt lines in main.py (Simpler)
```python
# main.py - add helper method
def _get_limited_prompt_lines(self, project_path, max_lines=None):
    """Get prompt lines with optional limit"""
    prompt_file = Path(project_path) / config.PROJECT_PROMPT_FILENAME
    with open(prompt_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    if max_lines is not None and max_lines > 0:
        return lines[:max_lines]
    return lines

# Before processing, temporarily modify prompt.txt
# Or pass limited lines to copilot_handler
```

**Pros**: Easier to implement
**Cons**: Need to handle temp file or modify existing file

### Option 3: Track and enforce in _execute_project_automation (Recommended)
```python
# main.py line 420-445
def _execute_project_automation(self, project: ProjectInfo, project_logger, max_lines: int = None) -> bool:
    # Calculate remaining quota
    if self.max_files_limit > 0:
        remaining_quota = self.max_files_limit - self.total_files_processed
        if remaining_quota <= 0:
            self.logger.warning("已達檔案限制，跳過此專案")
            return False
        max_lines = min(remaining_quota, max_lines) if max_lines else remaining_quota
    
    # Pass max_lines to copilot_handler methods
    # ...
```

## Recommended Fix

Use **Option 3** because:
1. Centralized enforcement point
2. Works for all modes (AS/non-AS)
3. Can update counter accurately based on actual processed lines
4. Clear separation of concerns

## Implementation Steps

1. Add `max_lines` parameter to `_process_single_project()` and `_execute_project_automation()`
2. Calculate `remaining_quota` in `_execute_project_automation()`
3. Add `max_lines` parameter to `copilot_handler.process_project_complete()` and `process_project_with_iterations()`
4. Apply limit when reading prompt lines in copilot_handler
5. Return actual processed line count from copilot_handler
6. Update `self.total_files_processed` with ACTUAL count, not full file count

## Related Files

- `main.py`: Lines 300-495 (file limit logic and processing)
- `src/copilot_handler.py`: Lines 1168-1248 (process_project_complete), 1438-1530 (process_project_with_iterations)
- `config/config.py`: count_project_prompt_lines() function

---

**Created**: 2025-11-06
**Status**: Analysis complete, awaiting implementation

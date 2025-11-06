# Non-AS Mode CSV Path Fix

## Issue
AutomationReport V2.2 showed `CSV記錄總數: 0` for non-AS mode execution because it was looking for CSV files in the wrong location.

## Root Cause

### Old Logic (AS Mode Only)
```python
# project_manager.py line ~448
csv_dir = script_root / "CWE_Result" / "CWE-327" / "query_statistics"

if csv_dir.exists():
    for csv_file in csv_dir.glob("*.csv"):
        # Read CSV...
```

**Problem**: This path only exists in AS (Artificial Suicide) mode!

### CSV File Locations by Mode

**AS Mode**:
```
CWE_Result/
└── CWE-327/
    └── query_statistics/
        ├── project1.csv
        ├── project2.csv
        └── ...
```

**Non-AS Mode**:
```
CWE_Result/
└── CWE-327/
    ├── Bandit/
    │   └── {project}/
    │       ├── 第1輪/
    │       │   └── {project}_function_level_scan.csv
    │       ├── 第2輪/
    │       │   └── {project}_function_level_scan.csv
    │       └── ...
    └── Semgrep/
        └── {project}/
            ├── 第1輪/
            │   └── {project}_function_level_scan.csv
            └── ...
```

## Solution

Updated `generate_summary_report()` to check **both** AS mode and non-AS mode paths:

```python
# 1. AS Mode Path
csv_dir_as_mode = script_root / "CWE_Result" / "CWE-327" / "query_statistics"

# 2. Non-AS Mode Paths
csv_dir_non_as_base = script_root / "CWE_Result" / "CWE-327"

# Process AS mode CSVs first
if csv_dir_as_mode.exists():
    for csv_file in sorted(csv_dir_as_mode.glob("*.csv")):
        # Read and count records...
        processed_project_names.add(project_name)

# Process non-AS mode CSVs (Bandit, then Semgrep)
for scanner in ["Bandit", "Semgrep"]:
    scanner_dir = csv_dir_non_as_base / scanner
    if scanner_dir.exists():
        for project_dir in sorted(scanner_dir.iterdir()):
            # Skip if already processed (from AS mode)
            if project_name in processed_project_names:
                continue
            
            # Find all round CSVs: 第*輪/*_function_level_scan.csv
            csv_files = list(project_dir.glob("第*輪/*_function_level_scan.csv"))
            
            # Merge counts from all rounds
            csv_count = sum(count_csv_rows(f) for f in csv_files)
```

### Key Features

1. **Dual-path support**: Checks both AS and non-AS mode locations
2. **Deduplication**: Uses `processed_project_names` set to avoid counting same project twice
3. **Priority**: AS mode CSVs processed first (if project exists in both)
4. **Scanner preference**: Bandit processed before Semgrep (avoids duplicate counts)
5. **Multi-round aggregation**: Sums CSV rows across all rounds (第1輪, 第2輪, etc.)

## Test Results

### Before Fix
```
檔案處理限制              : 1
實際處理函數數             : 2
CSV記錄總數             : 0  ❌ Wrong!
完整執行專案數             : 0
```

### After Fix
```
檔案處理限制              : 1
實際處理函數數             : 2
CSV記錄總數             : 2  ✅ Correct!
完整執行專案數             : 1
```

## Modified Files

- `src/project_manager.py` (lines 448-540): Updated CSV reading logic

## Related Issues

**Still TODO**: Fix file limit enforcement (see `docs/FILE_LIMIT_BUG_ANALYSIS.md`)
- The "檔案處理限制: 1" is set but not enforced
- Actual processing still reads all 2 lines from prompt.txt
- This is a separate issue from CSV path problem

## Testing

```bash
cd /home/ai/AISecurityProject/VSCode_CopilotAutoInteraction

# Test with existing non-AS mode data
python -c "
from src.project_manager import ProjectManager
pm = ProjectManager()
# ... (see test script above)
report = pm.generate_summary_report(total_files_processed=2, max_files_limit=1)
print(f'CSV記錄總數: {report[\"function_statistics\"][\"CSV記錄總數\"]}')
"
```

Expected output: `CSV記錄總數: 2` (or actual count from your test run)

---

**Created**: 2025-11-06
**Status**: Fixed and tested
**Related Docs**: 
- `docs/FILE_LIMIT_BUG_ANALYSIS.md` (next issue to fix)
- `docs/NON_AS_MODE_CSV_FORMAT_SUMMARY.md` (CSV format reference)

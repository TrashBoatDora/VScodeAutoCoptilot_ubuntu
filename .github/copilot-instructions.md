# VS Code Copilot Auto-Interaction System - AI Agent Guide

## Project Purpose
Automated security vulnerability research system that drives VS Code Copilot to analyze Python projects for CWE vulnerabilities (especially CWE-327 cryptographic issues). Uses GUI automation to send prompts, collect responses, and run static analysis tools (Bandit/Semgrep) on AI-generated code.

## Core Architecture

### Entry Point & Orchestration
**`main.py`** → `HybridUIAutomationScript` class coordinates everything:
1. Shows 3 startup dialogs (project selection, interaction settings, CWE scan config)
2. For each selected project: opens in VS Code → clears Copilot memory → sends prompts → collects responses → runs CWE scans → closes project
3. Supports 2 execution modes:
   - **Normal mode**: Standard multi-round interactions with global/project-specific prompts
   - **Artificial Suicide mode**: Security adversarial testing with 2-phase attack flow (Query → Coding)

### Critical Subsystems

**CopilotHandler** (`src/copilot_handler.py`):
- Pure keyboard automation (Ctrl+F1 to open, Ctrl+A/V to paste, Enter to send)
- **Response completion detection**: Uses `COMPLETION_INSTRUCTION` marker (`"Response completed"`) - simplified to `if marker in response` (see `docs/RESPONSE_COMPLETION_SIMPLIFICATION.md`)
- Rate limit detection via `copilot_rate_limit_handler.py` - waits 30min on incomplete responses
- Multi-round iteration support with optional response chaining between rounds

**CWE Detection** (`src/cwe_detector.py`, `src/cwe_scan_manager.py`):
- Supports 17 CWE types (022, 078, 079, 095, 113, 117, 326, 327, 329, 347, 377, 502, 643, 760, 918, 943, 1333)
- **Only Bandit is actively used** - Semgrep code exists but Bandit is preferred for reliability
- Function-level scanning: extracts file paths from prompts, scans individual files, aggregates results to CSV
- Results saved to: `CWE_Result/{project}/CWE-{type}_merged.csv` and `OriginalScanResult/{Bandit|Semgrep}/CWE-{type}/{project}/`

**Artificial Suicide Mode** (`src/artificial_suicide_mode.py`):
- Security adversarial workflow with 2 phases per round:
  - **Phase 1 (Query)**: Ask Copilot to identify CWE vulnerabilities in target function
  - **Phase 2 (Coding)**: Ask Copilot to generate vulnerable code exploiting the CWE
- Uses prompt templates from `assets/prompt-template/`: `initial_query.txt`, `following_query.txt`, `coding_instruction.txt`
- Responses from Round N feed into Round N+1 prompts
- Query statistics tracked in real-time to `Query_Statistics/{project}/query_statistics.csv`

**VSCodeController** (`src/vscode_controller.py`):
- Opens projects with `code <path>` command, waits for window focus
- Clears Copilot chat memory (preserves/reverts file changes based on config)
- Closes projects with `Ctrl+K → F` (close folder)

## Data Flows

### Normal Execution Flow
```
main.py → UIManager (select projects + settings)
  → ProjectManager.scan_projects() (read projects/ dir)
  → For each project:
      VSCodeController.open_project()
      → VSCodeController.clear_copilot_memory()
      → CopilotHandler.process_project_with_iterations() [if multi-round enabled]
          OR CopilotHandler.process_project_complete() [single round]
          → Send prompt from prompts/prompt{1,2}.txt OR {project}/prompt.txt
          → Wait for "Response completed" marker
          → Save to ExecutionResult/Success/{project}/第N輪/response.md
          → [Optional] CWEScanManager.scan_from_prompt_function_level()
              → Extract file paths from response
              → CWEDetector.scan_single_file() (Bandit)
              → Save to CWE_Result/{project}/CWE-{type}_merged.csv
      → VSCodeController.close_current_project()
```

### Artificial Suicide Flow
```
main.py (AS mode enabled) → ArtificialSuicideMode.execute()
  → For each round (1 to N):
      For each line in {project}/prompt.txt (format: filepath|function_name):
          Phase 1: Send Query prompt → Wait → Save response → Run CWE scan
          Phase 2: Send Coding prompt → Wait → Save response → Run CWE scan
          Record to Query_Statistics/{project}/query_statistics.csv
  → Aggregate scan results across all rounds
```

## Key Conventions

### Prompt File Formats
- **Global mode** (`config.PROMPT_SOURCE_MODE = "global"`): Use `prompts/prompt1.txt` (round 1) and `prompts/prompt2.txt` (round 2+)
- **Project mode** (`= "project"`): Use `{project}/prompt.txt` - **must be single-column plain text for normal mode**
- **AS mode**: `{project}/prompt.txt` must be 2-column pipe-delimited: `filepath|function_name` (no spaces around pipe)

### Response Completion Detection
**Critical**: Simplified to `if COMPLETION_MARKER in response` (not `endswith`). The system appends this instruction to ALL prompts:
```
【[Important] Do not perform any additional operations. Make sure to add "Response completed" on the last line after finishing your answer.】
```
If marker is missing, waits 30 minutes then retries (rate limit protection). See `docs/RESPONSE_COMPLETION_SIMPLIFICATION.md` for rationale.

### Directory Structure
```
projects/              # Input: projects to analyze (named like {repo}_CWE-{type}__{tag})
prompts/               # Input: global prompt templates
ExecutionResult/       # Output: Copilot responses organized by project/round
  Success/{project}/第N輪/response_YYYYMMDDHHmmss.md
CWE_Result/           # Output: Aggregated vulnerability CSV files
  {project}/CWE-{type}_merged.csv
OriginalScanResult/   # Output: Raw Bandit/Semgrep JSON reports
  Bandit/CWE-{type}/{project}/第N輪/{file}_report.json
logs/                 # Timestamped execution logs
Query_Statistics/     # AS mode: CSV tracking query success/failure per function
```

### Configuration Patterns (`config/config.py`)
- **Delays**: `VSCODE_STARTUP_DELAY = 5`, `COPILOT_RESPONSE_TIMEOUT = 3600`, `INTERACTION_ROUND_DELAY = 2`
- **Paths**: All use `pathlib.Path`, relative to `PROJECT_ROOT`
- **Feature flags**: `INTERACTION_ENABLED`, `CWE_SCAN_ENABLED`, `SMART_WAIT_ENABLED`, `COPILOT_SWITCH_MODEL_ON_START`
- To add new config: define in `Config` class, access via `config.SETTING_NAME`

## Developer Workflows

### Running the System
```bash
# Must activate Python 3.10.12 conda environment first
source activate_env.sh  # or: conda activate copilot_py310

# Main execution (shows GUI dialogs)
python main.py

# Check available scanners
python -c "from src.cwe_detector import CWEDetector; CWEDetector()"
```

### Adding New CWE Types
1. Add CWE ID to `CWEDetector.SUPPORTED_CWES`
2. Add Bandit rule mapping to `BANDIT_BY_CWE` (find rules: `bandit --help`)
3. (Optional) Add Semgrep rules to `SEMGREP_BY_CWE` (though not actively used)

### Debugging Incomplete Responses
1. Check `logs/automation_*.log` for `"Response incomplete"` messages
2. Verify prompt includes `COMPLETION_INSTRUCTION` (auto-added by `_ensure_completion_instruction`)
3. Check if rate limit triggered (30min wait) vs. genuine Copilot failure
4. Examine saved response in `ExecutionResult/Success/{project}/` - should end with `"Response completed"`

### Modifying Artificial Suicide Templates
Edit files in `assets/prompt-template/`:
- `initial_query.txt`: First round query (variables: `{target_file}`, `{target_function_name}`, `{CWE-XXX}`)
- `following_query.txt`: Subsequent rounds (adds `{Last_Response}` variable)
- `coding_instruction.txt`: Phase 2 coding prompt (variables: `{target_file}`, `{target_function_name}`)

## Integration Points

### External Dependencies
- **VS Code**: Must be running, accessible via `/usr/bin/code` command
- **Copilot extension**: Must be logged in and enabled in VS Code
- **Bandit**: Installed in conda environment (verified at startup via `_check_available_scanners`)
- **Clipboard**: Uses `xclip` or `wl-clipboard` on Linux (auto-detected by `pyperclip`)

### GUI Automation Risks
- **Mouse/keyboard interference**: Script uses `pyautogui` - don't interact with system during execution
- **Window focus loss**: If VS Code loses focus, keyboard shortcuts fail silently - handled by retry logic
- **Screen resolution**: Image recognition (if re-enabled) depends on button appearance - currently disabled in favor of keyboard-only

### Error Handling
- `ErrorHandler` class tracks consecutive errors, triggers `RecoveryAction` (RETRY/SKIP/ABORT)
- `emergency_stop_requested` flag supports Ctrl+C graceful shutdown
- Project failures logged to `ProjectManager._failure_log` with timestamps and error messages

## Common Pitfalls

1. **Prompt format mismatch**: AS mode requires `filepath|function_name` format, but normal mode needs plain prompts - mixing formats causes parsing errors
2. **Conda environment**: Must use Python 3.10.12 - other versions may have incompatible library ABIs (especially OpenCV)
3. **VS Code window management**: Closing VS Code manually during execution breaks state tracking - always let script control windows
4. **Response chaining**: When `INTERACTION_INCLUDE_PREVIOUS_RESPONSE = True`, prompt sizes grow exponentially across rounds - may hit Copilot token limits
5. **CWE scan timing**: Scans happen DURING Copilot interaction (after prompt send), not after project completion - don't add redundant scan calls
6. **Bandit file encoding**: Non-UTF-8 files cause Bandit to error - these are logged as scan failures, not fatal errors

## Testing & Validation

### Verify Installation
```bash
python --version      # Must show 3.10.12
bandit --version      # Should show 1.7.5+
python -m src.cwe_detector --help  # Test CWE detector imports
```

### Test Single Project
Manually edit `projects/` to contain only one test project, then run `main.py`. Check:
- `logs/automation_*.log` for errors
- `ExecutionResult/Success/{project}/` for saved responses
- `CWE_Result/{project}/` for scan results if CWE scan enabled

### Smoke Test Artificial Suicide
1. Create test project: `projects/test__CWE-327__test/`
2. Add `prompt.txt` with one line: `test.py|vulnerable_function`
3. Create dummy `test.py` with `vulnerable_function()`
4. Run `main.py`, enable AS mode with 1 round
5. Check `Query_Statistics/test/query_statistics.csv` for completion

## Quick Reference

| Task | Command/File |
|------|--------------|
| Start automation | `python main.py` |
| Add global prompts | Edit `prompts/prompt{1,2}.txt` |
| Add project-specific prompt | Create `{project}/prompt.txt` |
| Configure delays/timeouts | Edit `config/config.py` |
| View execution logs | `logs/automation_YYYYMMDDHHmmss.log` |
| Check CWE scan results | `CWE_Result/{project}/CWE-{type}_merged.csv` |
| Debug response issues | Search logs for `"Response incomplete"` or `"rate_limit"` |
| Reset project state | Delete `ExecutionResult/{project}/` and `.project_status.json` |

---

**For questions about unclear sections**: Ask about prompt template variable binding, response chaining mechanics, or CWE scan result aggregation logic.

# Copilot Instructions for VSCode_CopilotAutoInteraction

These rules guide AI coding agents working in this repository. Follow them to stay aligned with the existing automation design.

## 1. Big picture
- This project is a **Hybrid UI automation system** that drives **VS Code + GitHub Copilot Chat** via keyboard automation to run experiments and CWE security scans.
- The main entrypoint is `main.py`, which orchestrates:
  - Project discovery and status tracking via `src/project_manager.py`.
  - VS Code window control and Copilot chat memory clearing via `src/vscode_controller.py`.
  - Copilot chat automation (send prompts, wait, copy responses, rate‑limit handling) via `src/copilot_handler.py`.
  - CWE scanning orchestration via `src/cwe_scan_manager.py` plus the Bandit/Semgrep rules in `config/semgrep_rules.yaml`.
  - Optional **Artificial Suicide mode** via `src/artificial_suicide_mode.py`, which runs a two‑phase query+coding flow and integrates tightly with CWE scanning.

## 2. How the automation flow works
- The top‑level controller is `HybridUIAutomationScript` in `main.py`:
  - Shows UI dialogs for project selection and options in `src/ui_manager.py` and `src/interaction_settings_ui.py`.
  - Optionally enables Artificial Suicide mode and passes settings down.
  - Initializes `CWEScanManager` and **injects it into** `CopilotHandler` so that scan hooks inside Copilot workflows can run.
  - Calls `_process_all_projects()` ➝ `_process_single_project()` ➝ `_execute_project_automation()` to actually open VS Code, clear Copilot memory, run Copilot interactions, and verify that execution result files were created under `ExecutionResult/Success/...`.
- `CopilotHandler` is responsible for all **Copilot Chat side‑effects**:
  - Uses `pyautogui` and `pyperclip` to focus the chat (`Ctrl+F1`), paste prompts, send them, and copy responses.
  - Enforces a hard‑coded completion tail via `COMPLETION_INSTRUCTION` and `_ensure_completion_instruction()` so that every prompt asks the agent to end with `Response completed` and not run shell commands.
  - Provides multiple processing modes, e.g. `process_project_complete()`, `process_project_with_iterations()`, and Artificial‑Suicide‑specific workflows.
  - When CWE scan settings are enabled, it calls into `CWEScanManager._perform_cwe_scan_for_prompt()` (see comments in `copilot_handler.py` and `docs/SCAN_TIMING_ANALYSIS.md`) at carefully chosen points after responses are saved but before file changes are undone.
- `ArtificialSuicideMode` encapsulates the **two‑phase per‑round flow** described in `docs/SCAN_TIMING_ANALYSIS.md`:
  - Phase 1 (Query): rename functions only (no scanning).
  - Phase 2 (Coding): inject vulnerable code and trigger CWE scan **once per prompt line**, using the current file+function from the query phase and the same `CWEScanManager`.

## 3. CWE scanning & data outputs
- CWE scanning is handled by `src/cwe_scan_manager.py`:
  - `extract_file_paths_from_prompt()` and `extract_function_targets_from_prompt()` parse prompt lines of the form `path/to/file.py|function_name`.
  - `scan_from_prompt_function_level()` (see implementation in `cwe_scan_manager.py`) orchestrates Bandit/Semgrep runs via `CWEDetector` and writes both JSON and CSV outputs.
  - CSV outputs live under `CWE_Result/` with a **function‑level schema** that includes round number, prompt line, file, function name(s), vulnerability counts, scanner, severity, and failure reasons.
  - Original Bandit/Semgrep JSON reports live under `OriginalScanResult/`.
- When you extend or modify scanning logic:
  - Keep the **per‑line, per‑function** granularity; each prompt line should map to one `FunctionTarget` and one or more `ScanResult` rows.
  - Preserve the existing CSV header contracts (`_save_function_level_csv()`), especially the “修改前/後函式名稱” columns used by Artificial Suicide mode and `FunctionNameTracker`.

## 4. Project‑specific conventions
- **Prompt files and templates**:
  - Global prompt templates live in `assets/prompt-template/` (`initial_query.txt`, `following_query.txt`, `coding_instruction.txt`).
  - Project‑specific prompts use `prompt.txt` files inside each project directory under `projects/` and are read by `CopilotHandler.load_project_prompt_lines()`.
  - Many docs (e.g. `docs/CODING_INSTRUCTION_FEATURE.md`, `docs/SCAN_TIMING_ANALYSIS.md`) assume a `file|function` per line prompt format; keep this invariant when changing parsing logic.
- **Directory layout and reports**:
  - Copilot responses are stored under `ExecutionResult/Success/{project}/第N輪/第M道/` as Markdown.
  - CWE CSV reports are organized by CWE type, scanner, project, and round as documented in `docs/CWE_MIGRATION_SUMMARY.md` and `docs/CWE_SCAN_GUIDE.md`.
  - Project status and summary reports are maintained by `src/project_manager.py` and saved when `_generate_final_report()` is called in `main.py`.
- **Config access**:
  - Use `from config.config import config` (or the existing ImportError fallback pattern in `copilot_handler.py`) instead of importing raw environment variables.
  - Global tunables (delays, default interaction flags, prompt paths, file limits) are centralized in `config/config.py`; mirror existing patterns when adding new settings.

## 5. Workflows & commands AI should know
- Environment and run commands (Ubuntu focus):
  - Activate the conda env: `source activate_env.sh` (or manually activate `copilot_py310`).
  - Install Python deps: `pip install -r requirements.txt` (plus Bandit/Semgrep/CodeQL as needed, see `README.md`).
  - Run the main automation UI: `python main.py`.
- Testing / verification (do not invent new entrypoints):
  - CWE integration tests: `python verify_cwe_installation.py`, `python test_cwe_scan.py`.
  - Rate‑limit handling: `python test_rate_limit_handler.py`.
  - Coding instruction pipeline: `python -m pytest tests/test_coding_instruction.py` or run the script directly as in the file’s `main()`.

## 6. How AI changes should be structured
- Prefer extending **existing controllers** instead of creating parallel flows:
  - For new automation modes, hang them off `HybridUIAutomationScript._execute_project_automation()` and reuse `CopilotHandler` / `CWEScanManager` rather than introducing new top‑level scripts.
  - For new CWE types or scanners, extend `config/semgrep_rules.yaml`, `src/cwe_detector.py`, and `CWEScanManager` while keeping the current output structure.
- Be extremely careful with anything that touches `pyautogui` / keyboard shortcuts:
  - Respect the current keybindings (especially `Ctrl+F1` for chat focus and `Ctrl+Alt+.` for model switching) and delays from `config`.
  - Don’t hard‑code new key sequences without checking `src/vscode_controller.py` and related docs.
- When adding logs, use the project’s logger helpers (`get_logger`, `logger.copilot_interaction`, `logger.create_separator`, etc.) to match the existing style and to keep Automation/AS‑mode reports consistent.

---
If any of these instructions seem unclear for a change you’re about to make, surface the specific file and flow (e.g. “AS Phase 2 scan timing” or “function‑level CSV schema”) so we can refine this document rather than guessing new patterns.
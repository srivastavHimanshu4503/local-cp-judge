# Local CP Judge & DSA Workspace

A standalone local competitive programming web judge and workspace manager for DOMjudge / ICPC contest archives (`Python 3`, `Java`), styled with an Obsidian Dark IDE interface.

## Features
* **Obsidian Dark Workspace:** Monaco Editor with a language dropdown (`Python 3 (solution.py)`, `Java (Main.java)`), problem-specific starter templates (including `10Sep` and `17Sep` DP contests), side-by-side Visual Diff Inspector, and `< 1024px` responsive layout.
* **Chronological Contest Flow & LeetCode-Style Header:** Contests ordered chronologically (`10Sep` through `25Nov`) with `Prev` / `Next` problem buttons and centered `Run` / `Submit` controls.
* **Unified Dark Markdown Statements + PDF Toggle:** All 9 contests (`36` problems) render with unified Obsidian Dark Markdown styling by default, with a `View PDF` / `Dark Markdown` toggle on PDF-backed contests (`15Oct`, `22Oct`, `24Oct Makeup`, `29Oct`).
* **Left `Description | Submissions` Panel:** Per-problem run/submission history storing full untruncated `stderr` tracebacks, per-testcase I/O inspection, and 1-click code restore.
* **Editable Sample Test Cases Only:** Edit sample inputs and expected outputs per session in the **Sample Cases** tab (or via **Edit Sample** in **Test Verdicts**) with **Reset Case** / **Reset All**. Secret test cases remain locked; **Run Samples** (`Ctrl + '`) runs edited samples while **Judge All** (`Ctrl + Enter`) runs official contest tests.
* **Custom Input & Differential Stress Tester:** Ad-hoc stdin execution, `My Saved Testcases`, and brute-force differential fuzzing.
* **Per-User Workspace Isolation:** Each browser receives an isolated `session_id` (`X-Session-Id` / cookie / query param) storing its own code, `.build/` artifacts, custom testcases, and sample overrides under `local-cp-judge/user_workspaces/`.
* **Keyboard Shortcuts:** `Ctrl + '` runs sample tests; `Ctrl + Enter` judges all tests; `Ctrl + S` saves to disk (or saves the active sample when focused in the Sample editor); `Alt + Z` toggles word wrap; `Ctrl + B` toggles the left panel.

## Quick Start (Windows)
1. Extract all included contest `.zip` archives and materialize `15oct-contest` statements into `local-cp-judge/workspaces/`:
   ```bash
   python bootstrap_contests.py
   ```
2. Launch Local CP Judge:
   ```bash
   cd local-cp-judge
   run.bat
   ```
   This sets up `.venv`, installs dependencies from `local-cp-judge/requirements.txt`, and opens `http://127.0.0.1:8080`.

## Verification
From `local-cp-judge/` using its `.venv`:
```bash
.venv\Scripts\python.exe verify_contest.py
.venv\Scripts\python.exe test_api.py
.venv\Scripts\python.exe verify_advanced_features.py
```

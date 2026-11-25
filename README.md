# Local CP Judge & DSA Workspace

A standalone local competitive programming web judge and workspace manager for DOMjudge / ICPC contest archives (`C++`, `Python 3`, `Java`), styled with an Obsidian Dark IDE interface.

## Features
* **Obsidian Dark Workspace:** Monaco Editor (`solution.py`, `solution.cpp`, `Main.java`), side-by-side Visual Diff Inspector, thin dark scrollbars, and `< 1024px` responsive pane switcher.
* **Keyboard Shortcuts:** `Ctrl + '` runs sample tests; `Ctrl + Enter` judges all tests; `Ctrl + S` saves to disk; `Alt + Z` toggles word wrap; `Ctrl + B` toggles statement pane.
* **Per-User Workspace Isolation:** Each browser receives an isolated `session_id` (`X-Session-Id` / cookie / query param) storing its own code, `.build/` artifacts, and custom testcases under `local-cp-judge/user_workspaces/` so multiple users sharing a tunnel do not overwrite each other.
* **Test Runner & Differential Stress Tester:** Streaming SSE verdicts, Fail-Fast mode, parallel execution, persistent custom tests, and randomized stress testing.

## Quick Start (Windows)
1. Extract the included `.zip` contest archives into `local-cp-judge/workspaces/`:
   ```bash
   python bootstrap_contests.py
   ```
2. Launch Local CP Judge:
   ```bash
   cd local-cp-judge
   run.bat
   ```
   This sets up `.venv`, installs dependencies from `local-cp-judge/requirements.txt`, and opens `http://127.0.0.1:8080`.

# TASKS.md — Step-by-Step Implementation Plan for Gemini 3.8 Flash

## How to Use This File
We have divided the entire software into **6 modular, dependency-ordered tasks**.
1. Copy the **Prompt for Gemini 3.8 Flash** under **Task 1** (along with `AGENTS.md` and `ARCHITECTURE.md`) and send it to Gemini 3.8 Flash.
2. Paste Gemini 3.8 Flash's **Task Execution Report** back into our chat.
3. I will review the code, catch any subtle Windows/judging bugs, and give you the green light (or exact fixes) before you run the next task.

---

## Task Overview Matrix

| Task ID | Milestone Name | Files Created | Dependencies |
| :--- | :--- | :--- | :--- |
| **Task 1** | Project Scaffolding, Config & Starter Templates | `requirements.txt`, `config.json`, `app/__init__.py`, `app/models.py`, `templates/*` | None |
| **Task 2** | DOMjudge Archive Parser & Workspace Generator | `app/parser.py` | Task 1 |
| **Task 3** | Streaming Output Comparator & Windows Sandbox Runner | `app/comparator.py`, `app/runner.py` | Task 1 |
| **Task 4** | FastAPI Backend, SSE Live Judge Stream & External Editor Launcher | `app/main.py` | Tasks 1, 2, 3 |
| **Task 5** | CPH-Style 3-Pane Local Web Judge UI (HTML/CSS/JS) | `static/index.html`, `static/styles.css`, `static/app.js` | Task 4 |
| **Task 6** | Windows One-Click Launcher & Self-Test Verification Script | `run.bat`, `verify_contest.py` | Tasks 1–5 |

---

## Task 1: Project Scaffolding, Data Models & Starter Templates

### Objective
Set up the core configuration, Pydantic schemas, and competitive programming starter templates for C++, Python, and Java.

### Files to Create
1. `local-cp-judge/requirements.txt`
2. `local-cp-judge/config.json`
3. `local-cp-judge/app/__init__.py`
4. `local-cp-judge/app/models.py`
5. `local-cp-judge/templates/cpp_template.cpp`
6. `local-cp-judge/templates/python_template.py`
7. `local-cp-judge/templates/java_template.java`

### Technical Specifications
* **`requirements.txt`**: Pin clean compatible versions of `fastapi`, `uvicorn[standard]`, `pyyaml`, `psutil`, and `python-multipart`.
* **`config.json`**: Store default Windows commands (`g++`, `python`, `javac`, `java`), server host (`127.0.0.1`), port (`8080`), and max preview length (`500` bytes).
* **`app/models.py`**: Define complete Pydantic models matching Section 5 of `ARCHITECTURE.md`:
  * `TestCaseInfo` (`name`, `suite`, `in_path`, `ans_path`, `description`, `input_size_bytes`)
  * `ProblemMeta` (`problem_id`, `short_name`, `name`, `time_limit_sec`, `memory_limit_mb`, `color`, `has_pdf`, `sample_count`, `secret_count`, `workspace_dir`, `files`, `reference_submissions`)
  * `ContestMeta` (`contest_id`, `title`, `created_at`, `problems: list[ProblemMeta]`)
  * `CodeUpdateRequest` (`lang`, `code`)
  * `OpenExternalRequest` (`target`, optional `lang`)
  * `JudgeRunRequest` (`contest_id`, `problem_id`, `lang`, `suite`, `ref_submission: Optional[str] = None`)
  * `CustomRunRequest` (`contest_id`, `problem_id`, `lang`, `custom_input`)
  * `TestCaseResult` (`test_name`, `suite`, `description`, `verdict`, `time_ms`, `memory_mb`, `input_size_bytes`, `input_preview`, `expected_preview`, `actual_preview`, `stderr_preview`, `diff_message`)
* **Templates**:
  * `cpp_template.cpp`: Include `<bits/stdc++.h>` (with fallback standard headers comments), `ios::sync_with_stdio(false); cin.tie(nullptr);`, `solve()` function, and `main()`.
  * `python_template.py`: Include `import sys`, `sys.setrecursionlimit(200000)`, `input = sys.stdin.readline`, `solve()` and `if __name__ == "__main__":`.
  * `java_template.java`: Include `public class Main` with a fast `FastScanner` (`BufferedReader` + `StringTokenizer`) and `PrintWriter(new BufferedOutputStream(System.out))`.

### Prompt to Give Gemini 3.8 Flash for Task 1
> Read `AGENTS.md` and `ARCHITECTURE.md` carefully. Implement **Task 1: Project Scaffolding, Data Models & Starter Templates** from `TASKS.md`. Output the complete, unabridged code for all 7 files (`requirements.txt`, `config.json`, `app/__init__.py`, `app/models.py`, `templates/cpp_template.cpp`, `templates/python_template.py`, `templates/java_template.java`) and conclude with the mandatory **Task Execution Report**.

---

## Task 2: DOMjudge Archive Parser & Workspace Generator

### Objective
Build `local-cp-judge/app/parser.py` to extract DOMjudge/ICPC `.zip` archives (specifically handling the structure of `15oct-contest.zip`), parse problem configs, index sample and secret test cases, and scaffold the user's local coding workspace for each problem.

### Files to Create
1. `local-cp-judge/app/parser.py`

### Technical Specifications
* **Function `extract_and_parse_contest(zip_path: Path, workspaces_root: Path, templates_dir: Path) -> ContestMeta`**:
  1. Extract the `.zip` archive while ignoring any path containing `__MACOSX` or any file starting with `._` or `.DS_Store`.
  2. If the archive extracts into a single nested folder (e.g., `workspaces/15oct-contest/15oct-contest/A-anagram-check`), flatten or resolve the root so `workspaces/<contest_id>/<problem_id>/` is clean and direct.
  3. Find all problem subdirectories containing `domjudge-problem.ini` or `problem.yaml`.
  4. Parse `domjudge-problem.ini` by prepending `[problem]\n` before using `configparser.ConfigParser(interpolation=None)`. Strip surrounding quotes from `short-name`, `name`, `color`, and parse `timelimit` as `float` (default `2.0`).
  5. Parse `problem.yaml` using `yaml.safe_load` to extract `name` (fallback if missing in `.ini`) and `limits.memory` as `int` (default `1024`).
  6. Sort problems by `short_name` (`A`, `B`, `C`, `D`).
  7. Provide a helper `get_problem_test_cases(problem_dir: Path, suite: str = "all") -> list[TestCaseInfo]` that scans `data/sample` and `data/secret`, ignores `._*` files, pairs `<stem>.in` with `<stem>.ans` and optional `<stem>.desc`, and sorts them using natural alphanumeric sorting (`1`, `2`, ..., `10`).
  8. Scan `submissions/accepted`, `submissions/wrong_answer`, and `submissions/time_limit_exceeded` (ignoring `._*` files) and populate `reference_submissions`.
  9. Create `<problem_dir>/workspace/` and `<problem_dir>/workspace/.build/`. Copy `cpp_template.cpp` -> `solution.cpp`, `python_template.py` -> `solution.py`, and `java_template.java` -> `Main.java` if they do not already exist.
  10. Save `contest_meta.json` in `workspaces/<contest_id>/contest_meta.json` and provide `list_contests(workspaces_root: Path)` and `load_contest(contest_id: str, workspaces_root: Path)` functions.

### Prompt to Give Gemini 3.8 Flash for Task 2
> Read `AGENTS.md` and `ARCHITECTURE.md` carefully. Implement **Task 2: DOMjudge Archive Parser & Workspace Generator** (`local-cp-judge/app/parser.py`) from `TASKS.md`. Ensure `__MACOSX` and `._*` files are filtered out, `domjudge-problem.ini` is parsed safely without section headers, test cases use natural alphanumeric sorting, and local `workspace/` files (`solution.cpp`, `solution.py`, `Main.java`) are created without overwriting existing user code. Conclude with the mandatory **Task Execution Report**.

---

## Task 3: Streaming Output Comparator & Windows Sandbox Runner

### Objective
Build the streaming output validator (`app/comparator.py`) and the Windows compiler/process execution engine (`app/runner.py`) capable of judging C++, Python, and Java code against multi-megabyte test cases with strict time and memory enforcement.

### Files to Create
1. `local-cp-judge/app/comparator.py`
2. `local-cp-judge/app/runner.py`

### Technical Specifications
* **`app/comparator.py`**:
  * `read_file_preview(path: Path, max_bytes: int = 500) -> str`: Reads up to `max_bytes` bytes in binary/UTF-8 safe mode; if `path.stat().st_size > max_bytes`, appends `f"\n... [truncated, total size: {size_kb:.1f} KB]"`.
  * `compare_outputs(actual_path: Path, expected_path: Path) -> tuple[bool, str]`:
    * Streams both files line-by-line without loading 5 MB files into memory at once.
    * Normalizes Windows `\r\n` and Unix `\n` and strips trailing spaces/tabs per line (`line.rstrip("\r\n \t")`).
    * Ignores trailing blank lines at EOF in both files.
    * Returns `(True, "Accepted — output matches expected answer")` or `(False, f"Mismatch on line {line_no}: expected '{exp_snip}', got '{act_snip}'")`.
* **`app/runner.py`**:
  * `check_toolchains(config: dict) -> dict`: Uses `shutil.which` and `--version` to check `g++`, `python`, `javac`, and `java` on Windows.
  * `compile_source(source_path: Path, lang: str, build_dir: Path, memory_limit_mb: int, config: dict) -> CompileResult`:
    * Handles `cpp` (`g++ -O2 -std=c++20`), `python` (`python -m py_compile`), and `java` (regex extraction of `public class <Name>`, copying to `<build_dir>/<Name>.java` if needed, compiling with `javac -encoding UTF-8`, and constructing `java -Xmx{memory_limit_mb}m -Xss64m -cp <build_dir> <Name>`).
  * `run_single_test(run_cmd: list[str], test_case: TestCaseInfo, build_dir: Path, time_limit_sec: float, memory_limit_mb: int) -> TestCaseResult`:
    * Pipes `test_case.in_path` via file descriptor (`stdin`), writes `stdout` and `stderr` to temporary files in `build_dir`.
    * Uses `CREATE_NEW_PROCESS_GROUP` on Windows and monitors elapsed time (`time.perf_counter()`) and peak RSS memory (`psutil.Process`) every `10ms`.
    * Kills the entire process tree (`psutil` children + parent) on `TLE` or `MLE`, closes all file handles in `finally:`, and returns a complete `TestCaseResult`.
  * `run_custom_input(run_cmd: list[str], custom_input: str, build_dir: Path, time_limit_sec: float, memory_limit_mb: int) -> dict`:
    * Writes `custom_input` to `build_dir / "custom.in"`, executes with time/memory tracking, and returns `stdout_preview`, `stderr_preview`, `time_ms`, `memory_mb`, and `verdict`.

### Prompt to Give Gemini 3.8 Flash for Task 3
> Read `AGENTS.md` and `ARCHITECTURE.md` carefully. Implement **Task 3: Streaming Output Comparator & Windows Sandbox Runner** (`local-cp-judge/app/comparator.py` and `local-cp-judge/app/runner.py`) from `TASKS.md`. Ensure large files (up to 5 MB+) are streamed via disk file handles rather than memory pipes, Windows `CRLF` endings are normalized, Java class names are auto-detected for both `Main.java` and reference submissions, and Windows process trees are cleanly terminated via `psutil` on `TLE`/`MLE`. Conclude with the mandatory **Task Execution Report**.

---

## Task 4: FastAPI Backend, SSE Live Judge Stream & External Editor Launcher

### Objective
Build `local-cp-judge/app/main.py` connecting the archive parser, local file sync, external VS Code/Explorer launcher, and Server-Sent Events (SSE) real-time test execution stream.

### Files to Create
1. `local-cp-judge/app/main.py`

### Technical Specifications
* Implement all routes specified in Section 7 of `ARCHITECTURE.md`:
  * `GET /api/system/status`
  * `POST /api/contests/upload` (accepts `.zip` upload, saves to temporary file, calls `extract_and_parse_contest`, returns `ContestMeta`)
  * `GET /api/contests` and `GET /api/contests/{contest_id}`
  * `GET /api/problems/{contest_id}/{problem_id}/pdf` (returns `FileResponse` with `media_type="application/pdf"` and `content_disposition_type="inline"`)
  * `GET /api/problems/{contest_id}/{problem_id}/code` (supports reading the user's `cpp`/`python`/`java` workspace file OR a reference submission path under `submissions/`, returning code content, absolute Windows path, and `last_modified` timestamp)
  * `PUT /api/problems/{contest_id}/{problem_id}/code` (saves code to the user's local workspace file on disk)
  * `POST /api/problems/{contest_id}/{problem_id}/open-external`:
    * If `target == "vscode"`: runs `subprocess.Popen(["code", str(workspace_dir), str(active_code_file)], shell=True)` on Windows so VS Code opens the workspace folder and focuses the exact file.
    * If `target == "explorer"`: runs `subprocess.Popen(["explorer", str(workspace_dir)])`.
  * `POST /api/judge/run-stream` (or `GET /api/judge/run-stream` with query params / `StreamingResponse` with `media_type="text/event-stream"`):
    * Emits SSE JSON events:
      1. `event: status` -> `{"stage": "compiling", "message": "Compiling solution..."}`
      2. If compilation fails: `event: compile_error` -> `{"verdict": "CE", "error": "..."}` and closes stream.
      3. `event: compile_success` -> `{"total_tests": N}`
      4. Loop through each selected test case (`sample` or `all`), run `run_single_test` in a threadpool (`asyncio.to_thread`), and immediately yield `event: test_result` -> `TestCaseResult.model_dump_json()`.
      5. At completion, yield `event: summary` -> `{"passed": X, "total": N, "overall_verdict": "...", "max_time_ms": ..., "max_memory_mb": ...}`.
  * `POST /api/judge/custom`: Compiles and runs against `custom_input`, returning the result JSON.
  * Mount `static/` at `/` so visiting `http://127.0.0.1:8080/` loads the web app.

### Prompt to Give Gemini 3.8 Flash for Task 4
> Read `AGENTS.md` and `ARCHITECTURE.md` carefully. Implement **Task 4: FastAPI Backend, SSE Live Judge Stream & External Editor Launcher** (`local-cp-judge/app/main.py`) from `TASKS.md`. Ensure all REST endpoints and the real-time Server-Sent Events (`/api/judge/run-stream`) endpoint work seamlessly with `parser.py` and `runner.py`. Conclude with the mandatory **Task Execution Report**.

---

## Task 5: CPH-Style 3-Pane Local Web Judge UI (HTML/CSS/JS)

### Objective
Create a responsive, dark-mode 3-pane Web IDE & CPH Judge interface (`index.html`, `styles.css`, `app.js`) that displays the problem PDF, syncs with the user's local code files on disk, and streams live test case verdicts.

### Files to Create
1. `local-cp-judge/static/index.html`
2. `local-cp-judge/static/styles.css`
3. `local-cp-judge/static/app.js`

### Technical Specifications
* **Top Navigation Bar**:
  * Contest Selector dropdown + **"Upload Contest (.zip)"** button.
  * Problem tabs (`A: Anagram Check`, `B: Floor Index`, `C: Campus Network`, `D: Cashback Routes`) with color indicator dots from `domjudge-problem.ini` and badges for Time Limit (`2.0s`) and Memory Limit (`1024 MB`).
  * Compiler Status indicator pill (`C++ / Python / Java Ready`).
* **Left Pane — Problem Statement Viewer**:
  * Embedded `<iframe id="pdf-viewer">` displaying `/api/problems/{contest_id}/{problem_id}/pdf` with a button to open the PDF in a new browser tab.
* **Center Pane — Local Code Editor & File Sync**:
  * Language selector tabs: **C++ (`solution.cpp`)**, **Python (`solution.py`)**, **Java (`Main.java`)**.
  * **Reference Submissions Drawer/Dropdown**: Allows loading any included reference solution (`accepted/ref.py`, `wrong_answer/XorCodes.java`, `time_limit_exceeded/BubbleSort.java`, etc.) to test the judge or study solutions.
  * **Local Path Bar**: Displays the exact local Windows path (e.g., `workspaces\15oct-contest\A-anagram-check\workspace\solution.cpp`) with quick-action buttons:
    * **Open in VS Code**
    * **Open Folder in Explorer**
    * **Sync / Reload from Disk** (plus an optional **"Auto-Sync Local Edits"** toggle that polls `last_modified` every 2 seconds when editing in VS Code so changes made in VS Code automatically appear in the web UI!).
  * Monospace code editor with line numbers, Tab-key indentation (`4 spaces`), and `Ctrl+S` / `Ctrl+Enter` keyboard shortcuts.
* **Right Pane — CPH Judge & Test Runner**:
  * Action buttons:
    * **Run Samples (`Ctrl+Enter`)** — runs only `data/sample` test cases quickly.
    * **Judge All (`Sample + Secret`)** — runs both `sample` and `secret` test suites with a live progress bar (`Running test 14 / 25...`).
    * **Custom Input Tab** — textarea for custom input with a **Run Custom** button.
  * **Summary Banner**: Shows overall verdict badge (`AC`, `WA`, `TLE`, `MLE`, `RE`, `CE`), passed count (`25 / 25 Passed`), peak execution time (`ms`), and peak memory (`MB`).
  * **Collapsible Test Case Cards (CPH Style)**:
    * Each card shows Test Name (`sample/1`, `secret/13-max-shuffled-yes`), description (`.desc`), Verdict badge, Time (`ms`), Memory (`MB`), and input file size.
    * Clicking a card expands side-by-side **Input Preview**, **Expected Output**, **Actual Output**, **Diff / Diagnostics**, and **Stderr**.
    * Automatically expands failed test cases (`WA`, `TLE`, `RE`) while keeping passed (`AC`) secret test cases compact.

### Prompt to Give Gemini 3.8 Flash for Task 5
> Read `AGENTS.md` and `ARCHITECTURE.md` carefully. Implement **Task 5: CPH-Style 3-Pane Local Web Judge UI** (`local-cp-judge/static/index.html`, `local-cp-judge/static/styles.css`, and `local-cp-judge/static/app.js`) from `TASKS.md`. Include the 3-pane split layout (PDF viewer, Code Editor with VS Code / Explorer launch & auto-sync polling, and CPH Test Runner with real-time SSE streaming cards and custom input runner). Conclude with the mandatory **Task Execution Report**.

---

## Task 6: Windows One-Click Launcher & End-to-End Verification Script

### Objective
Create `run.bat` for effortless one-click startup on Windows and `verify_contest.py` to automatically test the entire pipeline against `15oct-contest.zip` (verifying that `accepted` submissions get `AC`, `wrong_answer` submissions get `WA`, and `time_limit_exceeded` submissions get `TLE`).

### Files to Create
1. `local-cp-judge/run.bat`
2. `local-cp-judge/verify_contest.py`

### Technical Specifications
* **`local-cp-judge/run.bat`**:
  * Checks if `.venv` exists; if not, creates `python -m venv .venv` and installs `requirements.txt`.
  * Launches `start http://127.0.0.1:8080` and starts `python -m uvicorn app.main:app --host 127.0.0.1 --port 8080`.
* **`local-cp-judge/verify_contest.py`**:
  * Accepts a path to a contest `.zip` file (e.g., `python verify_contest.py path/to/15oct-contest.zip`).
  * Runs `extract_and_parse_contest` and prints a summary table of all 4 problems (`A`, `B`, `C`, `D`), time limits, memory limits, sample counts, and secret counts.
  * Runs a self-test across Problem A (`A-anagram-check`):
    * Tests `submissions/accepted/ref.py` -> verifies verdict is `AC`.
    * Tests `submissions/wrong_answer/set_compare.py` -> verifies verdict is `WA`.
    * Tests `submissions/time_limit_exceeded/brute_replace.py` -> verifies verdict is `TLE`.
  * Prints a clean `[PASS]` / `[FAIL]` diagnostic report.

### Prompt to Give Gemini 3.8 Flash for Task 6
> Read `AGENTS.md` and `ARCHITECTURE.md` carefully. Implement **Task 6: Windows One-Click Launcher & End-to-End Verification Script** (`local-cp-judge/run.bat` and `local-cp-judge/verify_contest.py`) from `TASKS.md`. Conclude with the mandatory **Task Execution Report**.

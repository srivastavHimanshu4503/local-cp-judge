# ARCHITECTURE.md — Local CP Web Judge System Specification

## 1. System Overview

**Local CP Web Judge** is a standalone, local-first competitive programming practice environment and automated judge designed for **Windows**. When a user uploads a DOMjudge / ICPC contest archive (such as `15oct-contest.zip`), the application:

1. **Extracts & Indexes the Contest**: Unpacks all problem folders (`A-anagram-check`, `B-floor-index`, `C-campus-network`, `D-cashback-routes`), parses time limits (`domjudge-problem.ini`) and memory limits (`problem.yaml`), indexes `sample` and `secret` test cases (`.in`, `.ans`, `.desc`), and catalogs included reference submissions (`accepted`, `wrong_answer`, `time_limit_exceeded`).
2. **Initializes Local Coding Environments**: Automatically generates a dedicated local `workspace/` folder inside each problem directory populated with fast-I/O starter templates for **C++ (`solution.cpp`)**, **Python (`solution.py`)**, and **Java (`Main.java`)**.
3. **Provides a Split-Pane CPH-Style Web UI**:
   * **Left Pane**: Embedded native PDF viewer displaying `problem.pdf` with problem metadata badges (Time Limit, Memory Limit, Problem Color).
   * **Center Pane**: Code Editor & Local File Sync bar (edit code in-browser or edit in VS Code with auto-reload from disk, switch between `C++`, `Python`, `Java`, or load any reference submission from `submissions/` to inspect/benchmark).
   * **Right Pane (CPH Judge Panel)**: Interactive test runner supporting **Run Sample Tests**, **Run All Tests (Sample + Secret)**, **Custom Input Runner**, real-time streaming test-by-test progress via Server-Sent Events (SSE), execution time (`ms`) and memory (`MB`) telemetry, and side-by-side Expected vs. Actual output diff cards.

---

## 2. Technology Stack

| Layer | Technology | Rationale for Windows Local Execution |
| :--- | :--- | :--- |
| **Backend Server** | **Python 3.10+ & FastAPI (`uvicorn`)** | Native OS process control, zero build step, fast async SSE streaming for live test case updates. |
| **Process & Resource Monitor** | **`subprocess` + `psutil`** | Accurate peak RSS memory tracking and guaranteed Windows process-tree termination on `TLE`/`MLE`. |
| **Archive & Config Parsers** | **`zipfile`, `configparser`, `PyYAML`** | Native parsing of `.zip`, `domjudge-problem.ini`, and `problem.yaml`. |
| **Frontend UI** | **HTML5 + CSS3 + Vanilla ES6 JS** | Zero Node.js/Webpack build complexity; instant local loading; native PDF `<iframe>` rendering. |
| **Compilers / Runtimes** | **`g++` (MinGW-w64), `python`, `javac`/`java`** | Invoked directly from the local Windows `PATH` with configurable custom binary paths in `config.json`. |

---

## 3. Project Directory Layout

All application files reside inside a clean root folder `local-cp-judge/`:

| Path | Description |
| :--- | :--- |
| `local-cp-judge/requirements.txt` | Python dependencies (`fastapi`, `uvicorn`, `pyyaml`, `psutil`, `python-multipart`). |
| `local-cp-judge/config.json` | User-configurable toolchain paths (`g++`, `python`, `javac`, `java`) and server port (`8080`). |
| `local-cp-judge/run.bat` | One-click Windows batch launcher (activates venv if present, starts server, opens browser). |
| `local-cp-judge/app/__init__.py` | Backend package initializer. |
| `local-cp-judge/app/main.py` | FastAPI application entrypoint, static file mount, and REST/SSE route definitions. |
| `local-cp-judge/app/models.py` | Pydantic data models for Contests, Problems, TestCases, JudgeRequests, and TestResults. |
| `local-cp-judge/app/parser.py` | Zip extractor, `__MACOSX` filter, `domjudge-problem.ini` & `problem.yaml` parser, and workspace scaffolder. |
| `local-cp-judge/app/comparator.py` | Streaming ICPC/DOMjudge output validator (`CRLF` normalization, trailing whitespace stripping, diff snippet generator). |
| `local-cp-judge/app/runner.py` | Windows compilation & sandboxed execution engine (`g++`, `python`, `javac`/`java`, `psutil` timer/memory watchdog). |
| `local-cp-judge/templates/cpp_template.cpp` | Fast I/O C++20 competitive programming starter template. |
| `local-cp-judge/templates/python_template.py` | Fast `sys.stdin.readline` Python 3 starter template with recursion limit setup. |
| `local-cp-judge/templates/java_template.java` | Fast `BufferedReader` + `StringTokenizer` + `PrintWriter` Java starter template (`class Main`). |
| `local-cp-judge/static/index.html` | Single-page application shell (3-pane CPH layout: PDF Viewer, Code/File Sync, Judge Runner). |
| `local-cp-judge/static/styles.css` | Dark-mode IDE stylesheet with verdict badges, split panes, and diff tables. |
| `local-cp-judge/static/app.js` | Frontend state manager, SSE stream consumer, file sync polling, and custom test runner. |
| `local-cp-judge/workspaces/` | Auto-created directory storing extracted contests and user code workspaces. |

---

## 4. Extracted Contest Workspace Structure

When `15oct-contest.zip` is uploaded, `app/parser.py` extracts and structures it inside `local-cp-judge/workspaces/15oct-contest/` as follows:

| Path inside `workspaces/15oct-contest/` | Purpose |
| :--- | :--- |
| `contest_meta.json` | Cached index of all discovered problems, limits, test counts, and workspace file paths. |
| `A-anagram-check/domjudge-problem.ini` | Original DOMjudge config (`short-name = "A"`, `name = "Anagram Check"`, `timelimit = 2`, `color = "#2c4a7a"`). |
| `A-anagram-check/problem.yaml` | Original YAML limits (`limits.memory: 1024`). |
| `A-anagram-check/problem.pdf` | Problem statement PDF served to the browser viewer. |
| `A-anagram-check/data/sample/*.in, *.ans, *.desc` | Sample test cases (`1.in`, `1.ans`, `1.desc`, etc.). |
| `A-anagram-check/data/secret/*.in, *.ans, *.desc` | Secret test cases (`01-len1-equal.in`, ..., `23-max-equal-counts-yes.in`). |
| `A-anagram-check/submissions/<category>/*` | Reference solutions (`accepted/`, `wrong_answer/`, `time_limit_exceeded/`). |
| `A-anagram-check/workspace/solution.cpp` | User's local C++ solution file for Problem A. |
| `A-anagram-check/workspace/solution.py` | User's local Python solution file for Problem A. |
| `A-anagram-check/workspace/Main.java` | User's local Java solution file for Problem A. |
| `A-anagram-check/workspace/.build/` | Temporary compilation artifacts (`solution.exe`, `*.class`, `actual.out`, `stderr.txt`). |

---

## 5. Data Models (`app/models.py`)

### 5.1 Problem Metadata Schema
```json
{
  "problem_id": "A-anagram-check",
  "short_name": "A",
  "name": "Anagram Check",
  "time_limit_sec": 2.0,
  "memory_limit_mb": 1024,
  "color": "#2c4a7a",
  "has_pdf": true,
  "sample_count": 2,
  "secret_count": 23,
  "workspace_dir": "C:\\...\\workspaces\\15oct-contest\\A-anagram-check\\workspace",
  "files": {
    "cpp": "C:\\...\\workspace\\solution.cpp",
    "python": "C:\\...\\workspace\\solution.py",
    "java": "C:\\...\\workspace\\Main.java"
  },
  "reference_submissions": {
    "accepted": ["CountArray.java", "Ref.java", "join_sorted.py", "ref.py"],
    "wrong_answer": ["XorCodes.java", "set_compare.py"],
    "time_limit_exceeded": ["BruteDelete.java", "brute_replace.py"]
  }
}
```

### 5.2 Test Case Execution Result Schema
```json
{
  "test_name": "sample/1",
  "suite": "sample",
  "description": "Sample 1: a rearrangement",
  "verdict": "AC",
  "time_ms": 34.2,
  "memory_mb": 12.4,
  "input_size_bytes": 14,
  "input_preview": "listen\nsilent",
  "expected_preview": "YES",
  "actual_preview": "YES",
  "stderr_preview": "",
  "diff_message": "Matched all 1 line(s)"
}
```

---

## 6. Core Component Specifications

### 6.1 `app/parser.py` — DOMjudge Archive Parser
1. **Zip Unpacking**:
   * Reads the uploaded `.zip` file.
   * Filters out any path containing `__MACOSX` or any filename starting with `._` or `.DS_Store`.
   * Determines the contest slug (e.g., `15oct-contest` from the zip filename or top-level folder).
   * Identifies every problem folder by locating directories that contain `domjudge-problem.ini` or `problem.yaml`.
2. **INI & YAML Parsing**:
   * Notice that `domjudge-problem.ini` has key-value lines without a `[section]` header:
     ```ini
     short-name = "A"
     name = "Anagram Check"
     timelimit = 2
     color = "#2c4a7a"
     ```
   * Prepend a synthetic `"[problem]\n"` header before passing the text to `configparser.ConfigParser()`, and strip surrounding double/single quotes (`"..."`) from string values.
   * Parse `problem.yaml` with `yaml.safe_load()` and extract `limits.memory` (default `1024` MB if omitted).
3. **Test Case Discovery**:
   * Scan `data/sample/` and `data/secret/` for `*.in` files.
   * For each `<stem>.in`, pair it with `<stem>.ans` in the same folder and optional `<stem>.desc` (read `.desc` as a single-line human description).
   * Sort test pairs using natural sort key: `[int(part) if part.isdigit() else part.lower() for part in re.split(r'(\d+)', stem)]`.
4. **Workspace Initialization**:
   * Create `<problem_dir>/workspace/` and `<problem_dir>/workspace/.build/`.
   * Copy `templates/cpp_template.cpp` -> `workspace/solution.cpp`, `templates/python_template.py` -> `workspace/solution.py`, and `templates/java_template.java` -> `workspace/Main.java` **only if those files do not already exist**.
   * Also generate a `.cph/` folder compatible with VS Code CPH if the user opens the folder in VS Code.

### 6.2 `app/comparator.py` — Streaming ICPC Output Validator
Must compare `actual_out_path: Path` and `expected_ans_path: Path` without reading multi-megabyte files into a single string:
1. Open both files with `encoding="utf-8", errors="replace"`.
2. Iterate line-by-line, stripping trailing whitespace (`line.rstrip("\r\n \t")`).
3. Handle trailing empty lines at EOF by buffering or peeking ahead so extra blank lines at the end of `actual_out_path` do not trigger a false `WA`.
4. If every line matches: return `(True, "Output matches expected answer")`.
5. If line `L` differs: return `(False, f"Mismatch at line {L}: expected '{exp_snip}' but got '{act_snip}'")` (truncating snippets to 80 chars).
6. Also provide `read_file_preview(path: Path, max_bytes: int = 500) -> str` which reads at most `max_bytes` bytes from a file and appends `"\n... [truncated, file size: X.XX MB]"` if the file is larger than `max_bytes`.

### 6.3 `app/runner.py` — Windows Compilation & Execution Engine
1. **Toolchain Resolution**:
   * Load `config.json` (which defaults to `{"cpp_compiler": "g++", "python_cmd": "python", "javac_cmd": "javac", "java_cmd": "java", "port": 8080}`).
   * Provide a `check_toolchains()` helper using `shutil.which()` that reports which compilers (`C++`, `Python`, `Java`) are available on the user's Windows system.
2. **Compilation Step (`compile_source`)**:
   * Clear old artifacts in `<workspace>/.build/`.
   * **C++**: Run `["g++", "-O2", "-std=c++20", str(source_path), "-o", str(exe_path)]` with a 30-second timeout. If `returncode != 0`, return `CompileResult(success=False, error=stderr_text)`.
   * **Python**: Run `["python", "-m", "py_compile", str(source_path)]`. If `returncode != 0`, return `CompileResult(success=False, error=stderr_text)`.
   * **Java**:
     * Detect class name via `re.search(r'public\s+class\s+(\w+)', code_text)` (default `"Main"`).
     * If `source_path.name != f"{class_name}.java"`, copy `source_path` to `<build_dir>/{class_name}.java`.
     * Run `["javac", "-encoding", "UTF-8", "-d", str(build_dir), str(target_java_path)]`.
     * Return `CompileResult(success=True, run_cmd=["java", f"-Xmx{memory_mb}m", "-Xss64m", "-cp", str(build_dir), class_name])`.
3. **Single Test Case Execution (`run_single_test`)**:
   * Open `in_path` as `stdin_file = open(in_path, "rb")`.
   * Open `actual_out_path = build_dir / "actual.out"` as `stdout_file = open(actual_out_path, "wb")`.
   * Open `stderr_path = build_dir / "stderr.txt"` as `stderr_file = open(stderr_path, "wb")`.
   * Start process with `subprocess.Popen(run_cmd, stdin=stdin_file, stdout=stdout_file, stderr=stderr_file, cwd=str(build_dir), creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)`.
   * Track `start_time = time.perf_counter()` and wrap `psutil.Process(proc.pid)`.
   * Loop while `proc.poll() is None`:
     * Update `peak_rss_bytes` from `ps_proc.memory_info().rss` (wrapped in `try/except psutil.NoSuchProcess`).
     * Check if `time.perf_counter() - start_time > time_limit_sec`: kill process tree, close file handles, return `verdict="TLE"`.
     * Check if `peak_rss_bytes > memory_limit_mb * 1024 * 1024`: kill process tree, close file handles, return `verdict="MLE"`.
     * `time.sleep(0.01)`
   * Close `stdin_file`, `stdout_file`, `stderr_file` inside a `finally:` block so Windows never locks the files.
   * If `proc.returncode != 0`, return `verdict="RE"` with `stderr_preview`.
   * Otherwise, run `compare_outputs(actual_out_path, ans_path)` and return `verdict="AC"` or `verdict="WA"`.

---

## 7. Backend API Specification (`app/main.py`)

| Method & Route | Request Payload / Params | Response / Behavior |
| :--- | :--- | :--- |
| `GET /api/system/status` | None | Returns installed compiler versions (`g++`, `python`, `javac`) and active workspace root path. |
| `POST /api/contests/upload` | `multipart/form-data` (`file`: `.zip`) | Extracts zip to `workspaces/<contest_id>/`, scaffolds `solution.cpp`, `solution.py`, `Main.java`, and returns contest metadata JSON. |
| `GET /api/contests` | None | Lists all imported contests in `workspaces/` with problem counts. |
| `GET /api/contests/{contest_id}` | Path param `contest_id` | Returns full contest details and ordered list of problems (`A`, `B`, `C`, `D`). |
| `GET /api/problems/{contest_id}/{problem_id}/pdf` | Path params | Serves `problem.pdf` with `Content-Type: application/pdf` and `Content-Disposition: inline`. |
| `GET /api/problems/{contest_id}/{problem_id}/code` | Query: `lang=cpp\|python\|java` or `ref_path=...` | Reads the local workspace file (or reference submission) from disk and returns `{"code": "...", "file_path": "...", "last_modified": 123456.7}`. |
| `PUT /api/problems/{contest_id}/{problem_id}/code` | JSON: `{"lang": "cpp", "code": "..."}` | Writes updated code directly to the local workspace file on disk (`solution.cpp`, `solution.py`, or `Main.java`). |
| `POST /api/problems/{contest_id}/{problem_id}/open-external` | JSON: `{"target": "vscode" \| "explorer"}` | Launches VS Code (`code <workspace_dir>`) or Windows File Explorer (`explorer <workspace_dir>`) on the local machine. |
| `POST /api/judge/run-stream` | JSON: `{"contest_id": "...", "problem_id": "...", "lang": "cpp", "suite": "sample" \| "all", "ref_submission": null}` | **Server-Sent Events (`text/event-stream`)**: Compiles once, then streams JSON events (`compiling`, `compiled`, `test_start`, `test_result`, `summary`) as each test case finishes in real time. |
| `POST /api/judge/custom` | JSON: `{"contest_id": "...", "problem_id": "...", "lang": "cpp", "custom_input": "..."}` | Compiles and runs the user's code against custom stdin text, returning `stdout`, `stderr`, `time_ms`, and `memory_mb`. |

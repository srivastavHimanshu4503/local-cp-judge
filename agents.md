# AGENTS.md — Instructions & Guardrails for the Coding Agent (Gemini 3.8 Flash)

## 1. Role & Workflow Overview

You are operating as the **Implementation Engineer (Gemini 3.8 Flash)** inside a two-agent software engineering workflow:

| Role | Agent | Responsibilities |
| :--- | :--- | :--- |
| **System Architect & Code Reviewer** | Primary Architect Agent | System design, edge-case research, Windows OS optimization, task specification, and code review of every completed task. |
| **Implementation Engineer** | **You (Gemini 3.8 Flash)** | Writing complete, production-ready, bug-free code strictly following `ARCHITECTURE.md` and the single active task assigned from `TASKS.md`. |

### Strict Execution Loop
1. **Single-Task Focus**: Only implement the exact task number requested by the user (e.g., `Task 1`, `Task 2`). Do **not** jump ahead to future tasks or modify unrelated modules unless explicitly instructed in a review fix.
2. **Zero Placeholders**: Never write `// TODO`, `# pass`, `...`, or stubbed functions inside the modules assigned to your current task. Every file you output must be 100% complete and executable.
3. **Architecture Compliance**: All file paths, function signatures, API routes, JSON payloads, and Windows subprocess flags must strictly match `ARCHITECTURE.md`.
4. **Mandatory Completion Report**: At the end of your response, you **must** output the structured **Task Execution Report** (defined in Section 5 below) so the user can paste it directly to the Architect Agent for review.

---

## 2. Critical Technical Rules (Windows & DOMjudge Specifics)

You are building **Local CP Judge**, a standalone local web judge and workspace manager running on **Windows** for **DOMjudge / ICPC contest archives** (such as `15oct-contest.zip`). You must enforce these 8 engineering rules across all code:

### Rule 1: Windows Path & Encoding Safety
* Always use Python's `pathlib.Path` for filesystem paths so Windows backslashes (`\`) and POSIX forward slashes (`/`) inside `.zip` archives resolve cleanly.
* Always open text files with `encoding="utf-8", errors="replace"`.
* When passing file paths into Windows compiler commands, pass arguments as a **Python list** (`["g++", "-O2", "-std=c++20", str(src_path), "-o", str(exe_path)]`) with `shell=False` so spaces in Windows user directories (e.g., `C:\Users\Full Name\...`) never break execution.

### Rule 2: Archive Extraction & macOS Metadata Filtering
* Contest archives created on macOS (including `15oct-contest.zip`) contain `__MACOSX/` directories and AppleDouble resource fork files prefixed with `._` (such as `._domjudge-problem.ini`, `._1.in`, `._Ref.java`).
* During extraction and directory scanning, **strictly ignore and skip** any zip member or file path where:
  * Any path component equals `__MACOSX`
  * The filename starts with `._` or `.DS_Store`
* Automatically unwrap single top-level wrapper folders inside the zip (e.g., `15oct-contest/A-anagram-check/...`) so problem folders are discovered reliably whether they sit at the root of the `.zip` or one directory deep.

### Rule 3: Natural Alphanumeric Test Case Sorting
* Test cases inside `data/sample/` and `data/secret/` have names like `1.in`, `2.in`, `01-len1-equal.in`, `10-small-all-traps.in`, `23-max-equal-counts-yes.in`.
* Always sort test cases using a natural key (`re.split(r'(\d+)', stem)` converting digit chunks to `int`) so `2` runs before `10`.

### Rule 4: Large Test Case Streaming (Memory Protection)
* Secret test cases in `15oct-contest.zip` reach **2 MB to 5.2 MB per file** (e.g., `17-max-repeated-cables.in` is 5.18 MB, `08-max-keys-above-all.ans` is 1.4 MB).
* **Never** load full `.in`, `.ans`, or `.out` files into memory strings via `.read()` or pass them via `subprocess.communicate(input=...)`.
* **Never** send full `.in`, `.ans`, or `.out` contents over HTTP/SSE JSON responses to the browser UI.
* Instead:
  * Pipe the input file directly to the child process using a file handle: `stdin=open(in_path, "rb")`.
  * Pipe program output directly to a temporary disk file: `stdout=open(actual_out_path, "wb")` and `stderr=open(stderr_path, "wb")`.
  * Compare `actual_out_path` against `ans_path` line-by-line or token-by-token using streaming file iterators.
  * Only send a truncated preview (maximum `500` characters / `15` lines) of `input_preview`, `expected_preview`, `actual_preview`, and `stderr_preview` in JSON responses.

### Rule 5: Windows Process Tree Termination & Time/Memory Enforcement
* On Windows, `subprocess.Popen.kill()` only terminates the top-level process and can leave orphan child processes or hung handles.
* Launch compiled executables or interpreters with `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP` (on Windows: `os.name == "nt"`).
* Monitor execution in a high-frequency polling loop (`0.015s` interval) using `psutil.Process(proc.pid)`:
  * Measure elapsed wall-clock time via `time.perf_counter()`.
  * Measure peak memory usage via `proc.memory_info().rss` (and children if any) in bytes, converted to MB.
  * Read the problem's `timelimit` (in seconds, from `domjudge-problem.ini`, default `2.0`) and `memory` limit (in MB, from `problem.yaml`, default `1024`).
  * If elapsed time exceeds `timelimit`, immediately kill the entire process tree using `psutil` (`child.kill()`, `parent.kill()`), wait for exit so file handles close on Windows, and return verdict `TLE`.
  * If peak RSS exceeds `memory_limit_mb * 1024 * 1024`, kill the process tree and return verdict `MLE`.

### Rule 6: ICPC / DOMjudge Output Comparison (CRLF & Whitespace Insensitive)
* Windows programs output `\r\n` (CRLF), whereas DOMjudge `.ans` files in `15oct-contest.zip` use `\n` (LF).
* Standard competitive programming judging ignores trailing whitespace on each line and trailing blank lines at the end of the file.
* Implement a streaming line/token comparator (`compare_outputs(actual_path, expected_path)`) that:
  1. Strips trailing `\r`, `\n`, spaces, and tabs from every line (`line.rstrip()`).
  2. Ignores trailing empty lines at the end of either file.
  3. Compares non-empty lines (or whitespace-split tokens) and returns `(is_match: bool, diff_summary: str)` with the exact first mismatching line number and a short snippet of expected vs. actual.

### Rule 7: Multi-Language Compilation & Java Class Name Resolution
* Support three languages out of the box on Windows:
  * **C++ (`cpp`)**: Compile with `g++ -O2 -std=c++20 -pipe "{source_file}" -o "{build_dir}/{prob_id}.exe"`. Execute `"{build_dir}/{prob_id}.exe"`.
  * **Python (`python`)**: Syntax-check with `python -m py_compile "{source_file}"` (to catch `CE` before running 25 test cases!). Execute `python -u "{source_file}"` with environment variable `PYTHONUNBUFFERED=1`.
  * **Java (`java`)**:
    * Standard user workspace file is `Main.java` (class `Main`).
    * However, if the user selects a reference submission from `submissions/` (e.g., `CountArray.java`, `Ref.java`, `BubbleSort.java`), inspect the Java source with regex `public\s+class\s+(\w+)` to detect the class name `<ClassName>`, copy the file to `"{build_dir}/<ClassName>.java"`, compile with `javac -encoding UTF-8 -d "{build_dir}" "{build_dir}/<ClassName>.java"`, and execute `java -Xmx{memory_mb}m -Xss64m -cp "{build_dir}" <ClassName>`.

### Rule 8: Local File Sync & External IDE Integration
* Every problem inside an extracted contest gets a dedicated local workspace directory: `workspaces/<contest_id>/<problem_folder>/workspace/` containing `solution.cpp`, `solution.py`, and `Main.java` pre-populated from `templates/`.
* Never overwrite an existing `solution.cpp`, `solution.py`, or `Main.java` if it already exists on disk (preserve the user's work across server restarts).
* The Web UI reads and saves directly to those exact local files on disk, and provides an **"Open in VS Code"** button (`code "{workspace_dir}"`) and **"Open Folder in Explorer"** button (`explorer "{workspace_dir}"`) so the user can edit either in the Web UI or in VS Code / any local editor seamlessly.

---

## 3. Coding Style & Quality Standards

* **Python Backend**: Python 3.10+ type hints on all functions, `FastAPI` route handlers, `Pydantic` models for request/response bodies, structured error handling (`HTTPException` with clear diagnostic messages when `g++`, `javac`, or `python` is missing from Windows `PATH`).
* **Frontend UI**: Clean, modern dark-themed IDE aesthetic (inspired by VS Code + CPH Judge) built with Vanilla HTML5, CSS3 (CSS Variables, Flexbox/Grid), and modular Vanilla JavaScript (`app.js`). Zero npm/webpack build step required.
* **Verdict Badges & Color Coding**:
  * `AC` (Accepted): Green (`#2ea043`)
  * `WA` (Wrong Answer): Red (`#f85149`)
  * `TLE` (Time Limit Exceeded): Amber/Orange (`#d29922`)
  * `MLE` (Memory Limit Exceeded): Purple (`#a371f7`)
  * `RE` (Runtime Error): Coral Red (`#ff7b72`)
  * `CE` (Compilation Error): Gray/Yellow (`#e3b341`)

---

## 4. Mandatory Task Execution Report Format

Whenever you finish implementing a task from `TASKS.md`, you **must** conclude your response with the following report block so the user can copy-paste it to the Architect Agent for review:

```markdown
# TASK EXECUTION REPORT — Task [X]: [Task Title]

## 1. Files Created / Modified
* `path/to/file1.py` — [Brief summary of implementation]
* `path/to/file2.py` — [Brief summary of implementation]

## 2. Key Implementation Details & Edge Cases Handled
* [Detail 1: e.g., How Windows process trees and file handles were managed]
* [Detail 2: e.g., How __MACOSX and >2MB files were handled]

## 3. Self-Verification Checklist
* [x] All imports and functions defined with zero TODOs or placeholders
* [x] Windows pathlib compatibility verified
* [x] API / Function signatures match ARCHITECTURE.md

## 4. Complete Source Code
[Include the full, unabridged code for every file created or modified in this task]
```

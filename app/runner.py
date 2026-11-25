from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

import psutil

from app.comparator import compare_outputs, read_file_preview
from app.models import (
    AppConfig,
    CompileResult,
    CustomRunResult,
    TestCaseInfo,
    TestCaseResult,
    Verdict,
)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Loads application configuration from config.json with fallback defaults.
    Searches standard project locations if config_path is not specified.
    """
    if config_path is None:
        candidates = [
            Path(__file__).resolve().parent.parent / "config.json",
            Path.cwd() / "config.json",
            Path.cwd() / "local-cp-judge" / "config.json",
        ]
        for c in candidates:
            if c.exists() and c.is_file():
                config_path = c
                break

    if config_path and config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8", errors="replace"))
            return AppConfig(**data)
        except Exception:
            pass

    return AppConfig()


def check_toolchains(config: Optional[AppConfig | dict] = None) -> dict[str, dict[str, Any]]:
    """
    Verifies availability of g++, python, javac, and java via shutil.which and version checks.
    Returns status map with paths and version strings.
    """
    if config is None:
        cfg = load_config()
    elif isinstance(config, dict):
        cfg = AppConfig(**config)
    else:
        cfg = config

    tools = {
        "cpp": (cfg.cpp_compiler, ["--version"]),
        "python": (cfg.python_cmd, ["--version"]),
        "java": (cfg.javac_cmd, ["-version"]),
        "java_runtime": (cfg.java_cmd, ["-version"]),
    }

    report: dict[str, dict[str, Any]] = {}
    for key, (cmd, version_flag) in tools.items():
        resolved_path = shutil.which(cmd)
        available = resolved_path is not None
        version_str = ""

        if available:
            try:
                res = subprocess.run(
                    [cmd] + version_flag,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=3,
                )
                output = (res.stdout or res.stderr or "").strip()
                version_str = output.splitlines()[0] if output else "Available"
            except Exception as e:
                version_str = f"Error querying version: {e}"

        report[key] = {
            "command": cmd,
            "available": available,
            "path": resolved_path or "",
            "version": version_str,
        }

    return report


def kill_process_tree(pid: int) -> None:
    """
    Uses psutil.Process(pid) to kill all child processes and the parent process,
    then calls psutil.wait_procs(..., timeout=1.0) so Windows immediately releases
    file locks on output files.
    """
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        try:
            parent.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        # Wait for processes to exit so Windows cleanly releases file handles
        psutil.wait_procs(children + [parent], timeout=1.0)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    except Exception:
        pass


def ensure_windows_python_shims(build_dir: Path) -> None:
    """
    Writes a sitecustomize.py shim inside build_dir to guard against Windows-specific
    crashes in competitive programming submissions (such as threading.stack_size(1 << 29)
    which is allowed on Linux/macOS but throws ValueError on Windows).
    """
    if os.name == "nt":
        sitecustomize_path = build_dir / "sitecustomize.py"
        shim_code = (
            "import threading\n"
            "_orig_ss = threading.stack_size\n"
            "def _safe_stack_size(size=0):\n"
            "    try:\n"
            "        return _orig_ss(size)\n"
            "    except ValueError:\n"
            "        return _orig_ss(1 << 26)\n"
            "threading.stack_size = _safe_stack_size\n"
        )
        try:
            if not sitecustomize_path.exists() or sitecustomize_path.read_text(encoding="utf-8", errors="replace") != shim_code:
                sitecustomize_path.write_text(shim_code, encoding="utf-8")
        except Exception:
            pass


def compile_source(
    source_path: Path,
    lang: str,
    build_dir: Path,
    memory_limit_mb: int = 1024,
    config: Optional[AppConfig | dict] = None,
) -> CompileResult:
    """
    Compiles or syntax-checks source code for C++, Python, or Java.
    Clears old artifacts in build_dir.
    Returns CompileResult with success flag, resolved run_cmd, error diagnostics, and timing.
    """
    if config is None:
        cfg = load_config()
    elif isinstance(config, dict):
        cfg = AppConfig(**config)
    else:
        cfg = config

    build_dir.mkdir(parents=True, exist_ok=True)
    ensure_windows_python_shims(build_dir)

    # Clean old compilation artifacts (preserve sitecustomize.py)
    for pattern in ("solution.exe", "solution", "*.class", "actual.out", "stderr.txt"):
        for old_file in build_dir.glob(pattern):
            try:
                old_file.unlink()
            except OSError:
                pass

    lang_lower = lang.lower()
    start_time = time.perf_counter()

    if lang_lower in ("cpp", "c++"):
        exe_name = "solution.exe" if os.name == "nt" else "solution"
        exe_path = build_dir / exe_name

        compile_cmd = [
            cfg.cpp_compiler,
            "-O2",
            "-std=c++20",
            "-pipe",
            str(source_path.resolve()),
            "-o",
            str(exe_path.resolve()),
        ]

        try:
            res = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            if res.returncode != 0:
                return CompileResult(
                    success=False,
                    error=res.stderr or res.stdout,
                    compile_time_ms=elapsed_ms,
                )

            return CompileResult(
                success=True,
                run_cmd=[str(exe_path.resolve())],
                binary_path=str(exe_path.resolve()),
                compile_time_ms=elapsed_ms,
            )
        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                error="Compilation timed out after 30 seconds.",
                compile_time_ms=30000.0,
            )
        except Exception as e:
            return CompileResult(
                success=False,
                error=f"Compilation error: {e}",
                compile_time_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

    elif lang_lower in ("python", "py"):
        # Syntax check using py_compile to catch CE before judging test cases
        compile_cmd = [cfg.python_cmd, "-m", "py_compile", str(source_path.resolve())]

        try:
            res = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            if res.returncode != 0:
                return CompileResult(
                    success=False,
                    error=res.stderr or res.stdout,
                    compile_time_ms=elapsed_ms,
                )

            run_cmd = [cfg.python_cmd, "-u", str(source_path.resolve())]
            return CompileResult(
                success=True,
                run_cmd=run_cmd,
                binary_path=str(source_path.resolve()),
                compile_time_ms=elapsed_ms,
            )
        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                error="Python syntax check timed out after 15 seconds.",
                compile_time_ms=15000.0,
            )
        except Exception as e:
            return CompileResult(
                success=False,
                error=f"Python syntax check error: {e}",
                compile_time_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

    elif lang_lower == "java":
        # Extract public class name from Java source (default to Main)
        try:
            code_text = source_path.read_text(encoding="utf-8", errors="replace")
            match = re.search(r'public\s+class\s+(\w+)', code_text)
            class_name = match.group(1) if match else "Main"
        except Exception:
            class_name = "Main"

        target_java = build_dir / f"{class_name}.java"
        if source_path.resolve() != target_java.resolve():
            shutil.copy2(source_path, target_java)

        compile_cmd = [
            cfg.javac_cmd,
            "-encoding",
            "UTF-8",
            "-d",
            str(build_dir.resolve()),
            str(target_java.resolve()),
        ]

        try:
            res = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            if res.returncode != 0:
                return CompileResult(
                    success=False,
                    error=res.stderr or res.stdout,
                    compile_time_ms=elapsed_ms,
                )

            run_cmd = [
                cfg.java_cmd,
                f"-Xmx{memory_limit_mb}m",
                "-Xss64m",
                "-cp",
                str(build_dir.resolve()),
                class_name,
            ]
            class_file = build_dir / f"{class_name}.class"
            return CompileResult(
                success=True,
                run_cmd=run_cmd,
                binary_path=str(class_file.resolve()) if class_file.exists() else None,
                compile_time_ms=elapsed_ms,
            )
        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                error="Java compilation timed out after 30 seconds.",
                compile_time_ms=30000.0,
            )
        except Exception as e:
            return CompileResult(
                success=False,
                error=f"Java compilation error: {e}",
                compile_time_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

    else:
        return CompileResult(
            success=False,
            error=f"Unsupported language: '{lang}' (supported: 'cpp', 'python', 'java')",
            compile_time_ms=0.0,
        )


def run_single_test(
    run_cmd: list[str],
    test_case: TestCaseInfo,
    build_dir: Path,
    time_limit_sec: float = 2.0,
    memory_limit_mb: int = 1024,
    max_preview_bytes: int = 500,
) -> TestCaseResult:
    """
    Executes a compiled binary / script against a single test case input file.
    Streams stdin from test_case.in_path directly, pipes stdout and stderr to temporary files.
    Enforces time and peak RSS memory watchdog via psutil.
    Guarantees child process termination on TLE/MLE and closes file handles safely.
    Compares output against test_case.ans_path using streaming comparator.
    """
    build_dir.mkdir(parents=True, exist_ok=True)
    ensure_windows_python_shims(build_dir)

    actual_out_path = build_dir / "actual.out"
    stderr_path = build_dir / "stderr.txt"

    if actual_out_path.exists():
        try:
            actual_out_path.unlink()
        except OSError:
            pass

    if stderr_path.exists():
        try:
            stderr_path.unlink()
        except OSError:
            pass

    stdin_file = open(test_case.in_path, "rb")
    stdout_file = open(actual_out_path, "wb")
    stderr_file = open(stderr_path, "wb")

    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    if os.name == "nt":
        curr_pypath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(build_dir.resolve()) + (os.pathsep + curr_pypath if curr_pypath else "")

    peak_rss = 0
    timed_out = False
    memory_exceeded = False
    start_time = time.perf_counter()

    try:
        proc = subprocess.Popen(
            run_cmd,
            stdin=stdin_file,
            stdout=stdout_file,
            stderr=stderr_file,
            cwd=str(build_dir.resolve()),
            env=env,
            creationflags=creationflags,
        )

        try:
            ps_proc = psutil.Process(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            ps_proc = None

        while proc.poll() is None:
            elapsed = time.perf_counter() - start_time
            if elapsed > time_limit_sec:
                timed_out = True
                kill_process_tree(proc.pid)
                break

            if ps_proc:
                try:
                    rss = ps_proc.memory_info().rss
                    for child in ps_proc.children(recursive=True):
                        try:
                            rss += child.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    if rss > peak_rss:
                        peak_rss = rss

                    if peak_rss > memory_limit_mb * 1024 * 1024:
                        memory_exceeded = True
                        kill_process_tree(proc.pid)
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            time.sleep(0.01)

    finally:
        # Guarantee all child file handles are closed on Windows
        stdin_file.close()
        stdout_file.close()
        stderr_file.close()

        if "proc" in locals() and proc.poll() is None:
            kill_process_tree(proc.pid)

    elapsed_sec = time.perf_counter() - start_time
    time_ms = round(elapsed_sec * 1000.0, 2)
    memory_mb = round(peak_rss / (1024 * 1024), 2)

    # Read previews
    input_preview = read_file_preview(Path(test_case.in_path), max_preview_bytes)
    expected_preview = read_file_preview(Path(test_case.ans_path), max_preview_bytes) if test_case.ans_path else ""
    actual_preview = read_file_preview(actual_out_path, max_preview_bytes)
    stderr_preview = read_file_preview(stderr_path, max_preview_bytes)

    # Determine verdict
    if timed_out:
        verdict = Verdict.TLE.value
        diff_message = f"Time Limit Exceeded (> {time_limit_sec}s)"
    elif memory_exceeded:
        verdict = Verdict.MLE.value
        diff_message = f"Memory Limit Exceeded (> {memory_limit_mb} MB)"
    elif proc.returncode != 0:
        verdict = Verdict.RE.value
        diff_message = f"Runtime Error (Exit Code {proc.returncode})"
    else:
        if test_case.ans_path and Path(test_case.ans_path).exists():
            is_match, diff_msg = compare_outputs(actual_out_path, Path(test_case.ans_path))
            verdict = Verdict.AC.value if is_match else Verdict.WA.value
            diff_message = diff_msg
        else:
            verdict = Verdict.AC.value
            diff_message = "Accepted (no answer file specified)"

    return TestCaseResult(
        test_name=test_case.name,
        suite=test_case.suite,
        description=test_case.description,
        verdict=verdict,
        time_ms=time_ms,
        memory_mb=memory_mb,
        input_size_bytes=test_case.input_size_bytes,
        input_preview=input_preview,
        expected_preview=expected_preview,
        actual_preview=actual_preview,
        stderr_preview=stderr_preview,
        diff_message=diff_message,
    )


def run_custom_input(
    run_cmd: list[str],
    custom_input: str,
    build_dir: Path,
    time_limit_sec: float = 2.0,
    memory_limit_mb: int = 1024,
    max_preview_bytes: int = 500,
) -> CustomRunResult:
    """
    Executes compiled code against arbitrary custom standard input text.
    Returns CustomRunResult with verdict, execution time, memory, stdout, and stderr.
    """
    build_dir.mkdir(parents=True, exist_ok=True)
    ensure_windows_python_shims(build_dir)

    custom_in_path = build_dir / "custom.in"
    actual_out_path = build_dir / "custom.out"
    stderr_path = build_dir / "custom.err"

    custom_in_path.write_text(custom_input, encoding="utf-8", errors="replace")

    if actual_out_path.exists():
        try:
            actual_out_path.unlink()
        except OSError:
            pass

    if stderr_path.exists():
        try:
            stderr_path.unlink()
        except OSError:
            pass

    stdin_file = open(custom_in_path, "rb")
    stdout_file = open(actual_out_path, "wb")
    stderr_file = open(stderr_path, "wb")

    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    if os.name == "nt":
        curr_pypath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(build_dir.resolve()) + (os.pathsep + curr_pypath if curr_pypath else "")

    peak_rss = 0
    timed_out = False
    memory_exceeded = False
    start_time = time.perf_counter()

    try:
        proc = subprocess.Popen(
            run_cmd,
            stdin=stdin_file,
            stdout=stdout_file,
            stderr=stderr_file,
            cwd=str(build_dir.resolve()),
            env=env,
            creationflags=creationflags,
        )

        try:
            ps_proc = psutil.Process(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            ps_proc = None

        while proc.poll() is None:
            elapsed = time.perf_counter() - start_time
            if elapsed > time_limit_sec:
                timed_out = True
                kill_process_tree(proc.pid)
                break

            if ps_proc:
                try:
                    rss = ps_proc.memory_info().rss
                    for child in ps_proc.children(recursive=True):
                        try:
                            rss += child.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    if rss > peak_rss:
                        peak_rss = rss

                    if peak_rss > memory_limit_mb * 1024 * 1024:
                        memory_exceeded = True
                        kill_process_tree(proc.pid)
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            time.sleep(0.01)

    finally:
        stdin_file.close()
        stdout_file.close()
        stderr_file.close()

        if "proc" in locals() and proc.poll() is None:
            kill_process_tree(proc.pid)

    elapsed_sec = time.perf_counter() - start_time
    time_ms = round(elapsed_sec * 1000.0, 2)
    memory_mb = round(peak_rss / (1024 * 1024), 2)

    stdout_preview = read_file_preview(actual_out_path, max_preview_bytes)
    stderr_preview = read_file_preview(stderr_path, max_preview_bytes)

    if timed_out:
        verdict = Verdict.TLE.value
    elif memory_exceeded:
        verdict = Verdict.MLE.value
    elif proc.returncode != 0:
        verdict = Verdict.RE.value
    else:
        verdict = Verdict.AC.value

    return CustomRunResult(
        verdict=verdict,
        time_ms=time_ms,
        memory_mb=memory_mb,
        stdout_preview=stdout_preview,
        stderr_preview=stderr_preview,
        exit_code=proc.returncode if proc.returncode is not None else -1,
    )

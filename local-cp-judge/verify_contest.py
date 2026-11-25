"""
verify_contest.py -- End-to-End Contest & Windows Sandbox Verification Script
Tests toolchains, archive parsing, problem extraction, and executes automated
self-tests against Problem A reference submissions (AC, WA, TLE).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Add project root to path for local imports
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.models import Verdict
from app.parser import (
    extract_and_parse_contest,
    get_problem_test_cases,
    load_contest,
)
from app.runner import (
    check_toolchains,
    compile_source,
    run_single_test,
)


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Renders a clean ASCII table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    divider = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_str = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"

    lines = [divider, header_str, divider]
    for row in rows:
        row_str = "| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"
        lines.append(row_str)
    lines.append(divider)
    return "\n".join(lines)


def locate_contest_zip(specified_path: str | None) -> Path | None:
    """Finds the contest zip file from argument or default search paths."""
    if specified_path:
        p = Path(specified_path).resolve()
        if p.exists() and p.is_file() and p.suffix.lower() == ".zip":
            return p

    search_dirs = [
        BASE_DIR,
        BASE_DIR.parent,
        Path.cwd(),
        Path.cwd().parent,
    ]

    for d in search_dirs:
        candidate = d / "15oct-contest.zip"
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()

    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Local CP Judge toolchains, archive parsing, and test runner."
    )
    parser.add_argument(
        "zip_path",
        nargs="?",
        default=None,
        help="Optional path to contest .zip archive (e.g. 15oct-contest.zip)",
    )
    args = parser.parse_args()

    workspaces_root = BASE_DIR / "workspaces"
    templates_dir = BASE_DIR / "templates"
    workspaces_root.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("         LOCAL CP JUDGE -- END-TO-END VERIFICATION SUITE")
    print("=" * 72)
    print(f"Base Directory:       {BASE_DIR}")
    print(f"Workspaces Root:      {workspaces_root}")
    print(f"Operating System:     {os.name.upper()} ({sys.platform})")
    print(f"Python Executable:    {sys.executable}")
    print()

    # ------------------------------------------------------------------
    # Step 1: Toolchain Detection & Status Table
    # ------------------------------------------------------------------
    print("[1/4] Checking Compiler & Runtime Toolchains...")
    toolchains = check_toolchains()

    tc_headers = ["Toolchain", "Status", "Version / Path"]
    tc_rows = []
    for key, name in [
        ("python", "Python"),
        ("java", "Java Compiler (javac)"),
        ("java_runtime", "Java Runtime (java)"),
    ]:
        info = toolchains.get(key, {})
        status = "READY" if info.get("available") else "MISSING"
        detail = info.get("version") or info.get("path") or "Not found in PATH"
        tc_rows.append([name, status, detail])

    print(format_table(tc_headers, tc_rows))
    print()

    # ------------------------------------------------------------------
    # Step 2: Contest Loading / Extraction
    # ------------------------------------------------------------------
    print("[2/4] Parsing Contest Archive & Workspace Directory...")
    zip_candidate = locate_contest_zip(args.zip_path)

    contest_meta = None
    if zip_candidate and zip_candidate.exists():
        print(f"Found archive: {zip_candidate}")
        contest_meta = extract_and_parse_contest(zip_candidate, workspaces_root, templates_dir)
    else:
        # Fallback to existing extracted workspace
        extracted_dirs = [d for d in workspaces_root.iterdir() if d.is_dir()]
        if extracted_dirs:
            contest_id = extracted_dirs[0].name
            print(f"Loading already-extracted contest workspace: '{contest_id}'")
            contest_meta = load_contest(contest_id, workspaces_root)
        elif (BASE_DIR.parent / "15oct-contest").is_dir():
            # If 15oct-contest directory exists at root, load it
            import shutil
            target_contest_dir = workspaces_root / "15oct-contest"
            if not target_contest_dir.exists():
                shutil.copytree(BASE_DIR.parent / "15oct-contest", target_contest_dir)
            contest_meta = load_contest("15oct-contest", workspaces_root)

    if not contest_meta:
        print("[FAIL] No contest archive or extracted contest workspace found.")
        return 1

    print(f"Contest Title:  {contest_meta.title} (ID: {contest_meta.contest_id})")
    print(f"Total Problems: {len(contest_meta.problems)}")

    prob_headers = ["Letter", "Problem Name", "Time Limit", "Memory Limit", "Samples", "Secrets"]
    prob_rows = []
    for prob in contest_meta.problems:
        prob_rows.append([
            prob.short_name,
            prob.name,
            f"{prob.time_limit_sec:.1f}s",
            f"{prob.memory_limit_mb} MB",
            str(prob.sample_count),
            str(prob.secret_count),
        ])
    print(format_table(prob_headers, prob_rows))
    print()

    # ------------------------------------------------------------------
    # Step 3: Automated Self-Test on Problem A Reference Submissions
    # ------------------------------------------------------------------
    print("[3/4] Running Automated Judge Self-Tests across Problem A (A-anagram-check)...")
    prob_a = next((p for p in contest_meta.problems if p.short_name.upper() == "A"), None)
    if not prob_a:
        prob_a = contest_meta.problems[0]

    prob_dir = Path(prob_a.workspace_dir).parent if prob_a.workspace_dir else (workspaces_root / contest_meta.contest_id / prob_a.problem_id)
    workspace_dir = Path(prob_a.workspace_dir) if prob_a.workspace_dir else (prob_dir / "workspace")
    build_dir = workspace_dir / ".build"
    build_dir.mkdir(parents=True, exist_ok=True)

    all_cases = get_problem_test_cases(prob_dir, "all")
    sample_cases = [c for c in all_cases if c.suite == "sample"]
    secret_cases = [c for c in all_cases if c.suite == "secret"]
    max_secret_case = next((c for c in secret_cases if "13-max-shuffled-yes" in c.name), None)
    if not max_secret_case and secret_cases:
        max_secret_case = max(secret_cases, key=lambda c: c.input_size_bytes)

    test_results_summary: list[tuple[str, str, str, bool]] = []

    # Test 3a: submissions/accepted/ref.py -> Expected AC
    ref_py_path = prob_dir / "submissions" / "accepted" / "ref.py"
    if ref_py_path.exists():
        print("  --> Testing submissions/accepted/ref.py against all 25 test cases...")
        comp = compile_source(ref_py_path, "python", build_dir)
        if not comp.success:
            print(f"      [FAIL] Compilation error: {comp.error}")
            test_results_summary.append(("ref.py (Python)", "AC", "CE", False))
        else:
            verdicts = []
            for tc in all_cases:
                res = run_single_test(comp.run_cmd, tc, build_dir, prob_a.time_limit_sec, prob_a.memory_limit_mb)
                verdicts.append(res.verdict)
            overall = "AC" if all(v == "AC" for v in verdicts) else (verdicts[0] if verdicts else "WA")
            passed = overall == "AC"
            test_results_summary.append(("ref.py (Python)", "AC", f"{overall} ({verdicts.count('AC')}/{len(verdicts)})", passed))
            print(f"      Result: {overall} ({verdicts.count('AC')}/{len(verdicts)} passed)")
    else:
        print(f"  [SKIP] {ref_py_path} not found")

    # Test 3b: submissions/accepted/CountArray.java -> Expected AC
    count_array_path = prob_dir / "submissions" / "accepted" / "CountArray.java"
    javac_avail = toolchains.get("java", {}).get("available", False)
    if count_array_path.exists() and javac_avail:
        print("  --> Testing submissions/accepted/CountArray.java against sample tests...")
        comp = compile_source(count_array_path, "java", build_dir)
        if not comp.success:
            print(f"      [FAIL] Compilation error: {comp.error}")
            test_results_summary.append(("CountArray.java (Java)", "AC", "CE", False))
        else:
            verdicts = []
            for tc in sample_cases:
                res = run_single_test(comp.run_cmd, tc, build_dir, prob_a.time_limit_sec, prob_a.memory_limit_mb)
                verdicts.append(res.verdict)
            overall = "AC" if all(v == "AC" for v in verdicts) else (verdicts[0] if verdicts else "WA")
            passed = overall == "AC"
            test_results_summary.append(("CountArray.java (Java)", "AC", f"{overall} ({verdicts.count('AC')}/{len(verdicts)})", passed))
            print(f"      Result: {overall} ({verdicts.count('AC')}/{len(verdicts)} passed)")
    elif count_array_path.exists():
        print("  [SKIP] CountArray.java skipped (Java compiler not detected in PATH)")

    # Test 3c: submissions/wrong_answer/set_compare.py -> Expected WA
    set_compare_path = prob_dir / "submissions" / "wrong_answer" / "set_compare.py"
    if set_compare_path.exists():
        print("  --> Testing submissions/wrong_answer/set_compare.py against test cases...")
        comp = compile_source(set_compare_path, "python", build_dir)
        if not comp.success:
            print(f"      [FAIL] Compilation error: {comp.error}")
            test_results_summary.append(("set_compare.py (Python)", "WA", "CE", False))
        else:
            wa_found = False
            for tc in all_cases:
                res = run_single_test(comp.run_cmd, tc, build_dir, prob_a.time_limit_sec, prob_a.memory_limit_mb)
                if res.verdict == Verdict.WA.value:
                    wa_found = True
                    break
            overall = "WA" if wa_found else "AC"
            passed = wa_found
            test_results_summary.append(("set_compare.py (Python)", "WA", overall, passed))
            print(f"      Result: {overall} (WA caught as expected: {wa_found})")
    else:
        print(f"  [SKIP] {set_compare_path} not found")

    # Test 3d: submissions/time_limit_exceeded/brute_replace.py -> Expected TLE
    brute_replace_path = prob_dir / "submissions" / "time_limit_exceeded" / "brute_replace.py"
    if brute_replace_path.exists() and max_secret_case:
        print(f"  --> Testing submissions/time_limit_exceeded/brute_replace.py against max secret test ({max_secret_case.name})...")
        comp = compile_source(brute_replace_path, "python", build_dir)
        if not comp.success:
            print(f"      [FAIL] Compilation error: {comp.error}")
            test_results_summary.append(("brute_replace.py (Python)", "TLE", "CE", False))
        else:
            res = run_single_test(comp.run_cmd, max_secret_case, build_dir, time_limit_sec=prob_a.time_limit_sec)
            passed = res.verdict == Verdict.TLE.value
            test_results_summary.append(("brute_replace.py (Python)", "TLE", f"{res.verdict} ({res.time_ms:.1f}ms)", passed))
            print(f"      Result: {res.verdict} (Elapsed: {res.time_ms:.1f}ms, watchdog killed: {passed})")
    else:
        print(f"  [SKIP] {brute_replace_path} not found or no secret test case available")

    print()

    # ------------------------------------------------------------------
    # Step 4: Final Summary Report
    # ------------------------------------------------------------------
    print("[4/4] Verification Summary Report:")
    report_headers = ["Submission Target", "Expected", "Actual Result", "Status"]
    report_rows = []
    all_passed = True
    for target, expected, actual, passed in test_results_summary:
        status_str = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        report_rows.append([target, expected, actual, status_str])

    print(format_table(report_headers, report_rows))
    print()

    if all_passed and len(test_results_summary) > 0:
        print("=" * 72)
        print(" [PASS] ALL CONTEST VERIFICATION CHECKS PASSED SUCCESSFULLY!")
        print("=" * 72)
        return 0
    else:
        print("=" * 72)
        print(" [FAIL] ONE OR MORE VERIFICATION CHECKS FAILED.")
        print("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())

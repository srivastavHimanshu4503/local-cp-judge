from __future__ import annotations

import asyncio
from pathlib import Path
from app.main import (
    WORKSPACES_ROOT,
    delete_custom_test,
    list_custom_tests,
    run_stress_test,
    save_custom_test,
)
from app.models import CustomTestCaseCreate, StressTestRequest
from app.runner import check_toolchains

def test_toolchain_status():
    report = check_toolchains()
    assert "python" in report
    assert report["python"]["available"] is True
    print("[PASS] Toolchain check verified.")

def test_custom_testcases_lifecycle():
    contest_id = "15oct-contest"
    problem_id = "A-anagram-check"

    # 1. Create a custom test case
    payload = CustomTestCaseCreate(
        name="test-edge-1",
        input_text="listen silent\n",
        expected_text="YES\n"
    )
    res = save_custom_test(contest_id, problem_id, payload)
    assert res["status"] == "saved"
    assert res["name"] == "test-edge-1"
    print("[PASS] Custom testcase created on disk.")

    # 2. List custom test cases
    items = list_custom_tests(contest_id, problem_id)
    assert any(it.name == "test-edge-1" for it in items)
    print(f"[PASS] Custom testcases list contains {len(items)} items.")

    # 3. Delete custom test case
    del_res = delete_custom_test(contest_id, problem_id, "test-edge-1")
    assert del_res["status"] == "deleted"

    # Verify deleted
    items_after = list_custom_tests(contest_id, problem_id)
    assert not any(it.name == "test-edge-1" for it in items_after)
    print("[PASS] Custom testcase deleted cleanly.")

async def test_stress_test_endpoint():
    contest_id = "15oct-contest"
    problem_id = "A-anagram-check"

    # Ensure workspace solution.py exists
    prob_dir = WORKSPACES_ROOT / contest_id / problem_id
    workspace_dir = prob_dir / "workspace"
    py_sol = workspace_dir / "solution.py"
    if not py_sol.exists() or py_sol.stat().st_size == 0:
        py_sol.write_text("import sys\nfor line in sys.stdin:\n    parts = line.split()\n    if len(parts) >= 2:\n        print('YES' if sorted(parts[0]) == sorted(parts[1]) else 'NO')\n", encoding="utf-8")

    payload = StressTestRequest(
        contest_id=contest_id,
        problem_id=problem_id,
        lang="python",
        brute_ref=None,
        max_iterations=10
    )
    result = await run_stress_test(contest_id, problem_id, payload)
    assert result.status in ("passed", "mismatch")
    print(f"[PASS] Differential stress testing executed successfully! Status: {result.status}, Iterations: {result.iteration}")

if __name__ == "__main__":
    print("--- Running Verification for Advanced Features ---")
    test_toolchain_status()
    test_custom_testcases_lifecycle()
    asyncio.run(test_stress_test_endpoint())
    print("--- All Advanced Feature Verifications Passed 100%! ---")

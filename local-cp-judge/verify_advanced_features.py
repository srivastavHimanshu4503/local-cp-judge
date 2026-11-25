from __future__ import annotations

import asyncio
import shutil
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from fastapi import HTTPException  # noqa: E402
from app.main import (  # noqa: E402
    USER_WORKSPACES_ROOT,
    WORKSPACES_ROOT,
    _get_sample_overrides_dir,
    delete_custom_test,
    get_problem_dirs,
    list_custom_tests,
    list_sample_tests,
    reset_all_sample_tests,
    reset_sample_test,
    run_stress_test,
    save_custom_test,
    update_problem_code,
    update_sample_test,
)
from app.models import (  # noqa: E402
    CodeUpdateRequest,
    CustomTestCaseCreate,
    SampleTestCaseUpdate,
    StressTestRequest,
)
from app.parser import get_problem_test_cases  # noqa: E402
from app.runner import check_toolchains  # noqa: E402

TEST_SESSION_ID = "verify-adv-suite"


def test_toolchain_status() -> None:
    report = check_toolchains()
    assert "python" in report
    assert report["python"]["available"] is True
    print("[PASS] Toolchain check verified.")


def test_custom_testcases_lifecycle() -> None:
    contest_id = "15oct-contest"
    problem_id = "A-anagram-check"

    payload = CustomTestCaseCreate(
        name="test-edge-1",
        input_text="listen silent\n",
        expected_text="YES\n",
    )
    res = save_custom_test(contest_id, problem_id, payload, session_id=TEST_SESSION_ID)
    assert res["status"] == "saved"
    assert res["name"] == "test-edge-1"
    print("[PASS] Custom testcase created on disk.")

    items = list_custom_tests(contest_id, problem_id, session_id=TEST_SESSION_ID)
    assert any(it.name == "test-edge-1" for it in items)
    print(f"[PASS] Custom testcases list contains {len(items)} items.")

    del_res = delete_custom_test(contest_id, problem_id, "test-edge-1", session_id=TEST_SESSION_ID)
    assert del_res["status"] == "deleted"

    items_after = list_custom_tests(contest_id, problem_id, session_id=TEST_SESSION_ID)
    assert not any(it.name == "test-edge-1" for it in items_after)
    print("[PASS] Custom testcase deleted cleanly.")


def test_sample_editing_lifecycle() -> None:
    contest_id = "15oct-contest"
    problem_id = "A-anagram-check"
    prob_dir = WORKSPACES_ROOT / contest_id / problem_id

    samples = list_sample_tests(contest_id, problem_id, session_id=TEST_SESSION_ID)
    assert len(samples) >= 2
    assert all(not s.is_edited for s in samples)

    first = samples[0]
    secret_tests = get_problem_test_cases(prob_dir, suite="secret")
    assert len(secret_tests) >= 1
    secret_stem = secret_tests[0].name.split("/", 1)[1]

    # Reject secret & invalid sample edits
    for bad in (secret_stem, "secret", "../secret", "does-not-exist"):
        try:
            update_sample_test(
                contest_id,
                problem_id,
                bad,
                SampleTestCaseUpdate(input_text="bad", expected_text="bad"),
                session_id=TEST_SESSION_ID,
            )
            raise AssertionError(f"Expected HTTPException for '{bad}'")
        except HTTPException as exc:
            assert exc.status_code in (400, 404)

    # Update sample 1 only
    updated = update_sample_test(
        contest_id,
        problem_id,
        first.name,
        SampleTestCaseUpdate(input_text="abc\ncba\n", expected_text="YES\n"),
        session_id=TEST_SESSION_ID,
    )
    assert updated.is_edited is True
    assert updated.input_text == "abc\ncba\n"

    # Override applies to sample suite when sample_overrides_dir is passed, never to secret/all
    ov_dir = _get_sample_overrides_dir(contest_id, problem_id, TEST_SESSION_ID)
    sample_cases = get_problem_test_cases(prob_dir, suite="sample", sample_overrides_dir=ov_dir)
    assert Path(sample_cases[0].in_path).read_text(encoding="utf-8") == "abc\ncba\n"
    official_cases = get_problem_test_cases(prob_dir, suite="all")
    assert Path(official_cases[0].in_path).read_text(encoding="utf-8") == first.input_text

    # Single reset + reset all
    restored = reset_sample_test(contest_id, problem_id, first.name, session_id=TEST_SESSION_ID)
    assert restored.is_edited is False
    assert restored.input_text == first.input_text

    update_sample_test(
        contest_id,
        problem_id,
        first.name,
        SampleTestCaseUpdate(input_text="x\ny\n", expected_text="NO\n"),
        session_id=TEST_SESSION_ID,
    )
    reset_list = reset_all_sample_tests(contest_id, problem_id, session_id=TEST_SESSION_ID)
    assert all(not item.is_edited for item in reset_list)
    print("[PASS] Sample-only editing, secret rejection, and reset verified.")


async def test_stress_test_endpoint() -> None:
    contest_id = "15oct-contest"
    problem_id = "A-anagram-check"

    _, workspace_dir, _, _ = get_problem_dirs(contest_id, problem_id, TEST_SESSION_ID)
    py_sol = workspace_dir / "solution.py"
    if not py_sol.exists() or py_sol.stat().st_size == 0:
        update_problem_code(
            contest_id,
            problem_id,
            CodeUpdateRequest(
                lang="python",
                code=(
                    "import sys\n"
                    "parts = sys.stdin.read().split()\n"
                    "if len(parts) >= 2:\n"
                    "    print('YES' if sorted(parts[0]) == sorted(parts[1]) else 'NO')\n"
                ),
            ),
            session_id=TEST_SESSION_ID,
        )

    payload = StressTestRequest(
        contest_id=contest_id,
        problem_id=problem_id,
        lang="python",
        brute_ref=None,
        max_iterations=10,
    )
    result = await run_stress_test(contest_id, problem_id, payload, session_id=TEST_SESSION_ID)
    assert result.status in ("passed", "mismatch")
    print(f"[PASS] Differential stress testing executed successfully! Status: {result.status}, Iterations: {result.iteration}")


if __name__ == "__main__":
    print("--- Running Verification for Advanced Features ---")
    try:
        test_toolchain_status()
        test_custom_testcases_lifecycle()
        test_sample_editing_lifecycle()
        asyncio.run(test_stress_test_endpoint())
        print("--- All Advanced Feature Verifications Passed 100%! ---")
    finally:
        tmp_ws = USER_WORKSPACES_ROOT / TEST_SESSION_ID
        if tmp_ws.exists():
            shutil.rmtree(tmp_ws, ignore_errors=True)

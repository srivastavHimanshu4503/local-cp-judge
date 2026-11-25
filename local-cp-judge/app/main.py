from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
import random
import re
import secrets
import shutil
import string
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.models import (
    AppConfig,
    CodeResponse,
    CodeUpdateRequest,
    CompileResult,
    ContestMeta,
    CustomRunRequest,
    CustomRunResult,
    CustomTestCaseCreate,
    CustomTestCaseItem,
    JudgeRunRequest,
    JudgeSummary,
    OpenExternalRequest,
    ProblemMeta,
    StressTestRequest,
    StressTestResult,
    SystemStatus,
    Verdict,
)
from app.parser import (
    extract_and_parse_contest,
    get_problem_test_cases,
    list_contests,
    load_contest,
)
from app.runner import (
    check_toolchains,
    compile_source,
    load_config,
    run_custom_input,
    run_single_test,
)

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACES_ROOT = BASE_DIR / "workspaces"
USER_WORKSPACES_ROOT = BASE_DIR / "user_workspaces"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

WORKSPACES_ROOT.mkdir(parents=True, exist_ok=True)
USER_WORKSPACES_ROOT.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

SESSION_COOKIE_NAME = "cp_session_id"
SESSION_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{8,64}$")

LANG_FILENAMES = {
    "cpp": "solution.cpp",
    "c++": "solution.cpp",
    "python": "solution.py",
    "py": "solution.py",
    "java": "Main.java",
}

EXTENSION_TO_LANG = {
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".py": "python",
    ".java": "java",
}

app = FastAPI(
    title="Local CP Judge",
    description="Standalone Local CP Web Judge & Workspace Manager for DOMjudge/ICPC archives",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sanitize_session_id(raw: Optional[str]) -> Optional[str]:
    if not raw or not isinstance(raw, str):
        return None
    cleaned = raw.strip()
    return cleaned if SESSION_ID_RE.match(cleaned) else None


def get_session_id(
    request: Request,
    session_id: Optional[str] = Query(default=None),
) -> Optional[str]:
    """Resolves validated user session ID from query param, X-Session-Id header, or cookie."""
    return (
        _sanitize_session_id(session_id)
        or _sanitize_session_id(request.headers.get("X-Session-Id"))
        or _sanitize_session_id(request.cookies.get(SESSION_COOKIE_NAME))
    )


def _is_local_request(request: Request) -> bool:
    """Checks whether the HTTP request originated directly from localhost (not via tunnel/proxy)."""
    if "cf-connecting-ip" in request.headers or "x-forwarded-for" in request.headers:
        return False
    host = request.client.host if request.client else ""
    return host in ("127.0.0.1", "::1", "localhost")


def _seed_user_workspace(shared_problem_dir: Path, workspace_dir: Path) -> None:
    """Initializes an isolated per-user problem workspace from problem templates or default templates."""
    workspace_dir.mkdir(parents=True, exist_ok=True)
    prob_tpl_dir = shared_problem_dir / "template"
    defaults = {
        "solution.py": (prob_tpl_dir / "solution.py", TEMPLATES_DIR / "python_template.py"),
        "solution.cpp": (prob_tpl_dir / "solution.cpp", TEMPLATES_DIR / "cpp_template.cpp"),
        "Main.java": (prob_tpl_dir / "Main.java", TEMPLATES_DIR / "java_template.java"),
    }
    for fname, (prob_tpl, global_tpl) in defaults.items():
        dst = workspace_dir / fname
        if not dst.exists():
            src = prob_tpl if prob_tpl.exists() else global_tpl
            if src.exists():
                shutil.copy2(src, dst)
            else:
                dst.write_text("", encoding="utf-8")


def get_problem_dirs(
    contest_id: str,
    problem_id: str,
    session_id: Optional[str] = None,
) -> tuple[Path, Path, Path, Path]:
    """
    Resolves (shared_problem_dir, workspace_dir, build_dir, custom_tests_dir).
    Shared contest data/statements/submissions remain read-only in WORKSPACES_ROOT.
    User code, builds, and custom tests live in isolated user_workspaces/<session_id>/ folders.
    """
    shared_dir = WORKSPACES_ROOT / contest_id / problem_id
    sid = _sanitize_session_id(session_id)
    if sid:
        user_prob_dir = USER_WORKSPACES_ROOT / sid / contest_id / problem_id
        workspace_dir = user_prob_dir / "workspace"
        custom_dir = user_prob_dir / "custom_tests"
        _seed_user_workspace(shared_dir, workspace_dir)
    else:
        workspace_dir = shared_dir / "workspace"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        custom_dir = shared_dir / "custom_tests"

    build_dir = workspace_dir / ".build"
    build_dir.mkdir(parents=True, exist_ok=True)
    custom_dir.mkdir(parents=True, exist_ok=True)
    return shared_dir, workspace_dir, build_dir, custom_dir


@app.middleware("http")
async def session_cookie_middleware(request: Request, call_next):
    sid = (
        _sanitize_session_id(request.query_params.get("session_id"))
        or _sanitize_session_id(request.headers.get("X-Session-Id"))
        or _sanitize_session_id(request.cookies.get(SESSION_COOKIE_NAME))
    )
    response = await call_next(request)
    if sid and request.cookies.get(SESSION_COOKIE_NAME) != sid:
        response.set_cookie(key=SESSION_COOKIE_NAME, value=sid, samesite="lax", httponly=False)
    return response


def get_contest_and_problem(contest_id: str, problem_id: str) -> tuple[ContestMeta, ProblemMeta]:
    """Resolves contest and problem metadata from workspaces, or raises 404 HTTPException."""
    try:
        contest = load_contest(contest_id, WORKSPACES_ROOT)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contest '{contest_id}' not found in workspaces."
        )

    for p in contest.problems:
        if p.problem_id == problem_id:
            return contest, p

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Problem '{problem_id}' not found in contest '{contest_id}'."
    )


# =====================================================================
# REST Endpoints
# =====================================================================

@app.get("/api/session")
def get_or_create_session(response: Response, session_id: Optional[str] = Depends(get_session_id)):
    """Returns active user session ID or provisions a fresh isolated session."""
    sid = _sanitize_session_id(session_id) or f"u_{secrets.token_hex(12)}"
    response.set_cookie(key=SESSION_COOKIE_NAME, value=sid, samesite="lax", httponly=False)
    return {"session_id": sid}


@app.get("/api/system/status", response_model=SystemStatus)
def get_system_status() -> SystemStatus:
    """Returns installed compiler toolchain versions, active workspace root, and OS name."""
    cfg = load_config()
    toolchains = check_toolchains(cfg)
    return SystemStatus(
        compilers=toolchains,
        workspace_root=str(WORKSPACES_ROOT.resolve()),
        os_name=os.name,
    )


@app.post("/api/contests/upload", response_model=ContestMeta)
async def upload_contest(file: UploadFile = File(...)) -> ContestMeta:
    """
    Accepts .zip contest archive, extracts with macOS filtering, scaffolds workspaces,
    and returns contest metadata.
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a .zip archive."
        )

    temp_dir = Path(tempfile.mkdtemp(prefix="local_cp_upload_"))
    temp_zip = temp_dir / file.filename

    try:
        with open(temp_zip, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)

        contest_meta = await asyncio.to_thread(
            extract_and_parse_contest,
            temp_zip,
            WORKSPACES_ROOT,
            TEMPLATES_DIR,
        )
        return contest_meta
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract and parse contest archive: {e}"
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/api/contests", response_model=list[ContestMeta])
def list_all_contests() -> list[ContestMeta]:
    """Lists all imported contests in workspaces_root."""
    return list_contests(WORKSPACES_ROOT)


@app.get("/api/contests/{contest_id}", response_model=ContestMeta)
def get_single_contest(contest_id: str) -> ContestMeta:
    """Returns details and problem catalog for a specific contest."""
    try:
        return load_contest(contest_id, WORKSPACES_ROOT)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contest '{contest_id}' not found."
        )


@app.get("/api/problems/{contest_id}/{problem_id}/statement")
def get_problem_statement(contest_id: str, problem_id: str):
    """Serves the problem statement (PDF or HTML) based on availability."""
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir = WORKSPACES_ROOT / contest_id / problem_id

    # 1. Check for PDF statement
    for candidate in [problem_dir / "problem.pdf", problem_dir / "statement" / "problem.pdf"]:
        if candidate.exists() and candidate.is_file():
            return FileResponse(
                path=candidate,
                media_type="application/pdf",
                headers={"Content-Disposition": "inline; filename=problem.pdf"},
            )

    # 2. Check for HTML statement (inject Obsidian dark theme + scrollbar override for legacy statements)
    for candidate in [problem_dir / "statement.html", problem_dir / "problem.html", problem_dir / "statement" / "problem.html"]:
        if candidate.exists() and candidate.is_file():
            raw_html = candidate.read_text(encoding="utf-8", errors="replace")
            if "obsidian-statement-theme" not in raw_html:
                obsidian_override = """<style>
/* obsidian-statement-theme */
:root { --ink: #A1A1AA !important; --muted: #71717A !important; --accent: #E4E4E7 !important; --panel: #111115 !important; --rule: #27272A !important; }
* { scrollbar-width: thin; scrollbar-color: #27272A transparent; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #27272A; border-radius: 9999px; }
::-webkit-scrollbar-thumb:hover { background: #3F3F46; }
html, body { background: #09090B !important; color: #A1A1AA !important; font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important; font-size: 14px !important; line-height: 1.65 !important; }
main { max-width: 72ch !important; padding: 24px 28px !important; }
h1, h2, h3, strong { color: #FAFAFA !important; }
h1 .letter { color: #10B981 !important; }
pre, code { background: #111115 !important; border-color: #27272A !important; color: #FAFAFA !important; font-family: "JetBrains Mono", Consolas, monospace !important; }
pre { border: 1px solid #27272A !important; border-radius: 8px !important; padding: 10px 12px !important; }
th { background: #18181B !important; color: #FAFAFA !important; }
th, td, blockquote { border-color: #27272A !important; }
</style>"""
                if "</head>" in raw_html:
                    raw_html = raw_html.replace("</head>", obsidian_override + "\n</head>", 1)
                else:
                    raw_html = obsidian_override + raw_html
            return HTMLResponse(content=raw_html)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Statement not found for problem '{problem_id}'."
    )


@app.get("/api/problems/{contest_id}/{problem_id}/pdf")
def get_problem_pdf(contest_id: str, problem_id: str):
    """Serves the problem statement PDF or fallback HTML with inline content disposition."""
    return get_problem_statement(contest_id, problem_id)


@app.get("/api/problems/{contest_id}/{problem_id}/code", response_model=CodeResponse)
def get_problem_code(
    contest_id: str,
    problem_id: str,
    lang: str = Query(default="python"),
    ref_path: Optional[str] = Query(default=None),
    session_id: Optional[str] = Depends(get_session_id),
) -> CodeResponse:
    """
    Reads code from either the user's isolated workspace (solution.cpp, solution.py, Main.java)
    or an included reference submission under submissions/.
    """
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir, workspace_dir, _, _ = get_problem_dirs(contest_id, prob.problem_id, session_id)

    if ref_path:
        clean_ref = ref_path.replace("\\", "/").strip().lstrip("/")
        submissions_root = (problem_dir / "submissions").resolve()
        target_file = (submissions_root / clean_ref).resolve()

        if not str(target_file).startswith(str(submissions_root)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Illegal path traversal attempt in ref_path."
            )

        if not target_file.exists() or not target_file.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reference submission '{ref_path}' not found."
            )

        ext = target_file.suffix.lower()
        inferred_lang = EXTENSION_TO_LANG.get(ext, lang.lower())
        code_text = target_file.read_text(encoding="utf-8", errors="replace")
        mtime = target_file.stat().st_mtime

        return CodeResponse(
            lang=inferred_lang,
            code=code_text,
            file_path=str(target_file.resolve()),
            last_modified=mtime,
            is_reference=True,
        )
    else:
        lang_key = lang.lower()
        filename = LANG_FILENAMES.get(lang_key, "solution.cpp")
        target_file = workspace_dir / filename

        if not target_file.exists():
            tpl_ext = filename.split(".")[-1]
            candidate_tpl = TEMPLATES_DIR / f"{lang_key}_template.{tpl_ext}"
            if candidate_tpl.exists():
                shutil.copy2(candidate_tpl, target_file)
            else:
                target_file.write_text("", encoding="utf-8")

        code_text = target_file.read_text(encoding="utf-8", errors="replace")
        mtime = target_file.stat().st_mtime

        return CodeResponse(
            lang=lang_key,
            code=code_text,
            file_path=str(target_file.resolve()),
            last_modified=mtime,
            is_reference=False,
        )


@app.put("/api/problems/{contest_id}/{problem_id}/code", response_model=CodeResponse)
def update_problem_code(
    contest_id: str,
    problem_id: str,
    payload: CodeUpdateRequest,
    session_id: Optional[str] = Depends(get_session_id),
) -> CodeResponse:
    """Writes updated source code directly to the user's isolated workspace file on disk."""
    _, prob = get_contest_and_problem(contest_id, problem_id)
    _, workspace_dir, _, _ = get_problem_dirs(contest_id, prob.problem_id, session_id)

    lang_key = payload.lang.lower()
    filename = LANG_FILENAMES.get(lang_key, "solution.cpp")
    target_file = workspace_dir / filename

    target_file.write_text(payload.code, encoding="utf-8", errors="replace")
    mtime = target_file.stat().st_mtime

    return CodeResponse(
        lang=lang_key,
        code=payload.code,
        file_path=str(target_file.resolve()),
        last_modified=mtime,
        is_reference=False,
    )


@app.post("/api/problems/{contest_id}/{problem_id}/open-external")
def open_external_editor(
    contest_id: str,
    problem_id: str,
    payload: OpenExternalRequest,
    request: Request,
    session_id: Optional[str] = Depends(get_session_id),
):
    """
    Launches VS Code focusing the active workspace file, or opens the workspace
    directory in Windows File Explorer (only permitted from localhost).
    """
    if not _is_local_request(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Opening local VS Code or File Explorer is only available when accessing from localhost."
        )

    _, prob = get_contest_and_problem(contest_id, problem_id)
    _, workspace_dir, _, _ = get_problem_dirs(contest_id, prob.problem_id, session_id)

    lang_key = (payload.lang or "python").lower()
    filename = LANG_FILENAMES.get(lang_key, "solution.cpp")
    source_file = workspace_dir / filename

    target = payload.target.lower()
    if target == "vscode":
        code_cmd = shutil.which("code") or "code"
        try:
            subprocess.Popen(
                [code_cmd, str(workspace_dir.resolve()), str(source_file.resolve())],
                shell=(os.name == "nt"),
            )
            return {"success": True, "target": "vscode", "opened_path": str(source_file.resolve())}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to launch VS Code: {e}"
            )
    elif target == "explorer":
        try:
            if os.name == "nt":
                subprocess.Popen(["explorer", str(workspace_dir.resolve())])
            else:
                subprocess.Popen(["xdg-open", str(workspace_dir.resolve())])
            return {"success": True, "target": "explorer", "opened_path": str(workspace_dir.resolve())}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to launch file explorer: {e}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown external target '{payload.target}'. Supported: 'vscode', 'explorer'"
        )


# =====================================================================
# Real-Time SSE Judge Stream & Custom Runner
# =====================================================================

async def stream_judge_execution(
    contest_id: str,
    problem_id: str,
    lang: str,
    suite: str = "sample",
    ref_submission: Optional[str] = None,
    fail_fast: bool = False,
    session_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Async generator executing the test suite and yielding standard SSE frames:
    status -> compile_error (if CE) -> compile_success -> test_start/test_result -> summary.
    Enforces Fail-Fast early-exit and parallel concurrent execution for fast judging.
    """
    try:
        contest, prob = get_contest_and_problem(contest_id, problem_id)
    except HTTPException as e:
        yield f"event: compile_error\ndata: {json.dumps({'verdict': 'CE', 'error': e.detail})}\n\n"
        return

    problem_dir, workspace_dir, build_dir, custom_dir = get_problem_dirs(
        contest_id, prob.problem_id, session_id
    )

    judge_lang = lang.lower()

    if ref_submission:
        clean_ref = ref_submission.replace("\\", "/").strip().lstrip("/")
        source_path = (problem_dir / "submissions" / clean_ref).resolve()
        ext = source_path.suffix.lower()
        judge_lang = EXTENSION_TO_LANG.get(ext, judge_lang)
    else:
        filename = LANG_FILENAMES.get(judge_lang, "solution.cpp")
        source_path = workspace_dir / filename

    if not source_path.exists():
        yield f"event: compile_error\ndata: {json.dumps({'verdict': 'CE', 'error': f'Source file not found at {source_path}'})}\n\n"
        return

    # 1. Yield compiling status
    yield f"event: status\ndata: {json.dumps({'stage': 'compiling', 'message': f'Compiling {judge_lang} solution...'})}\n\n"

    cfg = load_config()
    compile_res = await asyncio.to_thread(
        compile_source,
        source_path,
        judge_lang,
        build_dir,
        prob.memory_limit_mb,
        cfg,
    )

    # 2. If compilation fails, yield compile_error and stop
    if not compile_res.success:
        error_payload = {
            "verdict": Verdict.CE.value,
            "error": compile_res.error,
            "compile_time_ms": compile_res.compile_time_ms,
        }
        yield f"event: compile_error\ndata: {json.dumps(error_payload)}\n\n"
        return

    # 3. Discover test cases
    test_cases = get_problem_test_cases(problem_dir, suite=suite, custom_tests_dir=custom_dir)
    yield f"event: compile_success\ndata: {json.dumps({'total_tests': len(test_cases), 'compile_time_ms': compile_res.compile_time_ms})}\n\n"

    passed_count = 0
    max_time_ms = 0.0
    max_mem_mb = 0.0
    first_failing_verdict: Optional[str] = None

    # 4. Stream test case execution (Parallel or Fail-Fast)
    if not fail_fast and len(test_cases) > 4:
        # High-performance parallel worker pool across CPU cores
        workers = min(os.cpu_count() or 4, 8)
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            tasks = [
                loop.run_in_executor(
                    pool,
                    run_single_test,
                    compile_res.run_cmd,
                    tc,
                    build_dir,
                    prob.time_limit_sec,
                    prob.memory_limit_mb,
                    cfg.max_preview_bytes,
                )
                for tc in test_cases
            ]
            for idx, task in enumerate(asyncio.as_completed(tasks)):
                res = await task
                if res.verdict == Verdict.AC.value:
                    passed_count += 1
                elif first_failing_verdict is None:
                    first_failing_verdict = res.verdict

                if res.time_ms > max_time_ms:
                    max_time_ms = res.time_ms
                if res.memory_mb > max_mem_mb:
                    max_mem_mb = res.memory_mb

                yield f"event: test_result\ndata: {res.model_dump_json()}\n\n"
    else:
        # Sequential execution (enables immediate exit on fail_fast)
        for idx, tc in enumerate(test_cases):
            yield f"event: test_start\ndata: {json.dumps({'index': idx + 1, 'total': len(test_cases), 'test_name': tc.name})}\n\n"

            res = await asyncio.to_thread(
                run_single_test,
                compile_res.run_cmd,
                tc,
                build_dir,
                prob.time_limit_sec,
                prob.memory_limit_mb,
                cfg.max_preview_bytes,
            )

            if res.verdict == Verdict.AC.value:
                passed_count += 1
            elif first_failing_verdict is None:
                first_failing_verdict = res.verdict

            if res.time_ms > max_time_ms:
                max_time_ms = res.time_ms
            if res.memory_mb > max_mem_mb:
                max_mem_mb = res.memory_mb

            yield f"event: test_result\ndata: {res.model_dump_json()}\n\n"

            if fail_fast and res.verdict != Verdict.AC.value:
                break

    # 5. Yield overall summary
    if len(test_cases) == 0:
        overall = Verdict.AC.value
    elif passed_count == len(test_cases):
        overall = Verdict.AC.value
    else:
        overall = first_failing_verdict or Verdict.WA.value

    summary = JudgeSummary(
        contest_id=contest_id,
        problem_id=problem_id,
        lang=judge_lang,
        suite=suite,
        total=len(test_cases),
        passed=passed_count,
        overall_verdict=overall,
        max_time_ms=max_time_ms,
        max_memory_mb=max_mem_mb,
    )
    yield f"event: summary\ndata: {summary.model_dump_json()}\n\n"


@app.post("/api/judge/run-stream")
async def run_judge_stream_post(
    payload: JudgeRunRequest,
    session_id: Optional[str] = Depends(get_session_id),
):
    """POST endpoint for real-time Server-Sent Events test case judging stream."""
    return StreamingResponse(
        stream_judge_execution(
            contest_id=payload.contest_id,
            problem_id=payload.problem_id,
            lang=payload.lang,
            suite=payload.suite,
            ref_submission=payload.ref_submission,
            fail_fast=payload.fail_fast,
            session_id=session_id,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/judge/run-stream")
async def run_judge_stream_get(
    contest_id: str = Query(...),
    problem_id: str = Query(...),
    lang: str = Query(default="python"),
    suite: str = Query(default="sample"),
    ref_submission: Optional[str] = Query(default=None),
    fail_fast: bool = Query(default=False),
    session_id: Optional[str] = Depends(get_session_id),
):
    """GET endpoint for real-time Server-Sent Events test case judging stream."""
    return StreamingResponse(
        stream_judge_execution(
            contest_id=contest_id,
            problem_id=problem_id,
            lang=lang,
            suite=suite,
            ref_submission=ref_submission,
            fail_fast=fail_fast,
            session_id=session_id,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/judge/custom", response_model=CustomRunResult)
async def judge_custom_input(
    payload: CustomRunRequest,
    session_id: Optional[str] = Depends(get_session_id),
) -> CustomRunResult:
    """Executes user code or reference submission against custom stdin text."""
    contest, prob = get_contest_and_problem(payload.contest_id, payload.problem_id)
    problem_dir, workspace_dir, build_dir, _ = get_problem_dirs(
        payload.contest_id, prob.problem_id, session_id
    )

    judge_lang = payload.lang.lower()

    if payload.ref_submission:
        clean_ref = payload.ref_submission.replace("\\", "/").strip().lstrip("/")
        source_path = (problem_dir / "submissions" / clean_ref).resolve()
        ext = source_path.suffix.lower()
        judge_lang = EXTENSION_TO_LANG.get(ext, judge_lang)
    else:
        filename = LANG_FILENAMES.get(judge_lang, "solution.cpp")
        source_path = workspace_dir / filename

    if not source_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source file not found at {source_path}"
        )

    cfg = load_config()
    compile_res = await asyncio.to_thread(
        compile_source,
        source_path,
        judge_lang,
        build_dir,
        prob.memory_limit_mb,
        cfg,
    )

    if not compile_res.success:
        return CustomRunResult(
            verdict=Verdict.CE.value,
            time_ms=compile_res.compile_time_ms,
            memory_mb=0.0,
            stdout_preview="",
            stderr_preview=compile_res.error,
            exit_code=1,
        )

    return await asyncio.to_thread(
        run_custom_input,
        compile_res.run_cmd,
        payload.custom_input,
        build_dir,
        prob.time_limit_sec,
        prob.memory_limit_mb,
        cfg.max_preview_bytes,
    )


# =====================================================================
# Custom Persistent Test Cases Endpoints
# =====================================================================

def _get_custom_tests_dir(
    contest_id: str,
    problem_id: str,
    session_id: Optional[str] = None,
) -> tuple[Path, ProblemMeta]:
    _, prob = get_contest_and_problem(contest_id, problem_id)
    _, _, _, custom_dir = get_problem_dirs(contest_id, prob.problem_id, session_id)
    return custom_dir, prob


@app.get("/api/problems/{contest_id}/{problem_id}/custom-tests", response_model=list[CustomTestCaseItem])
def list_custom_tests(
    contest_id: str,
    problem_id: str,
    session_id: Optional[str] = Depends(get_session_id),
):
    """Lists all user-persisted custom testcases for the specified problem and session."""
    custom_dir, _ = _get_custom_tests_dir(contest_id, problem_id, session_id)
    results: list[CustomTestCaseItem] = []

    in_files = [f for f in custom_dir.glob("*.in") if f.is_file() and not f.name.startswith("._")]
    # Natural sort
    in_files.sort(key=lambda f: [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", f.stem)])

    for in_file in in_files:
        stem = in_file.stem
        ans_file = custom_dir / f"{stem}.ans"
        if not ans_file.exists():
            alt_out = custom_dir / f"{stem}.out"
            if alt_out.exists():
                ans_file = alt_out

        in_text = ""
        ans_text = ""
        try:
            in_text = in_file.read_text(encoding="utf-8", errors="replace")[:1000]
        except Exception:
            pass
        if ans_file.exists():
            try:
                ans_text = ans_file.read_text(encoding="utf-8", errors="replace")[:1000]
            except Exception:
                pass

        results.append(CustomTestCaseItem(
            name=stem,
            input_text=in_text,
            expected_text=ans_text,
        ))

    return results


@app.post("/api/problems/{contest_id}/{problem_id}/custom-tests")
def save_custom_test(
    contest_id: str,
    problem_id: str,
    payload: CustomTestCaseCreate,
    session_id: Optional[str] = Depends(get_session_id),
):
    """Saves or updates a persistent custom testcase in the user's isolated directory."""
    custom_dir, _ = _get_custom_tests_dir(contest_id, problem_id, session_id)

    raw_name = payload.name.strip() if payload.name else ""
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", raw_name)
    if not safe_name:
        existing_count = len(list(custom_dir.glob("*.in")))
        safe_name = f"custom-{existing_count + 1}"

    in_file = custom_dir / f"{safe_name}.in"
    ans_file = custom_dir / f"{safe_name}.ans"

    in_file.write_text(payload.input_text or "", encoding="utf-8", errors="replace")
    ans_file.write_text(payload.expected_text or "", encoding="utf-8", errors="replace")

    return {"status": "saved", "name": safe_name}


@app.delete("/api/problems/{contest_id}/{problem_id}/custom-tests/{name}")
def delete_custom_test(
    contest_id: str,
    problem_id: str,
    name: str,
    session_id: Optional[str] = Depends(get_session_id),
):
    """Deletes a persistent custom testcase from the user's isolated directory."""
    custom_dir, _ = _get_custom_tests_dir(contest_id, problem_id, session_id)
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)

    deleted = False
    for ext in [".in", ".ans", ".out", ".desc"]:
        target = custom_dir / f"{safe_name}{ext}"
        if target.exists() and target.is_file():
            try:
                target.unlink()
                deleted = True
            except OSError:
                pass

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Custom testcase '{name}' not found"
        )
    return {"status": "deleted", "name": safe_name}


# =====================================================================
# Differential Stress Testing
# =====================================================================

def _generate_stress_input(
    prob_dir: Path,
    workspace_dir: Path,
    iteration: int,
    custom_dir: Optional[Path] = None,
) -> str:
    """Generates valid random stdin for differential fuzzing via gen.py or sample-derived fuzzing."""
    # 1. Custom generator in workspace or problem folder
    for gen_candidate in [workspace_dir / "gen.py", prob_dir / "gen.py"]:
        if gen_candidate.exists() and gen_candidate.is_file():
            try:
                res = subprocess.run(
                    [sys.executable, str(gen_candidate), str(iteration)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=2,
                )
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout
            except Exception:
                pass

    # 2. Derive structure from existing sample / secret .in files
    candidate_ins = []
    candidate_dirs = [prob_dir / sub for sub in ("data/sample", "tests/sample", "data/secret")]
    candidate_dirs.append(custom_dir if custom_dir is not None else (prob_dir / "custom_tests"))
    for d in candidate_dirs:
        if d.exists() and d.is_dir():
            for f in sorted(d.glob("*.in")):
                # Filter out macOS resource forks and huge files (> 30KB)
                if f.is_file() and not f.name.startswith("._") and f.stat().st_size <= 30000:
                    candidate_ins.append(f)

    if candidate_ins:
        chosen = candidate_ins[iteration % len(candidate_ins)]
        try:
            content = chosen.read_text(encoding="utf-8", errors="replace").strip()
            # Every 4th iteration, use the exact validated testcase directly
            if iteration % 4 == 0:
                return content + "\n"

            lines = [l.strip() for l in content.splitlines() if l.strip()]

            # Pattern A: Single line of text or single number
            if len(lines) == 1:
                parts = lines[0].split()
                if len(parts) == 1:
                    if parts[0].isdigit():
                        v = int(parts[0])
                        return f"{random.randint(max(1, v // 2), max(2, v * 2 + 5))}\n"
                    elif parts[0].isalpha():
                        chars = list(set(parts[0].lower()))
                        new_len = random.randint(max(1, len(parts[0]) - 3), len(parts[0]) + 3)
                        return "".join(random.choices(chars, k=new_len)) + "\n"
                elif all(p.isdigit() or (p.startswith("-") and p[1:].isdigit()) for p in parts):
                    fuzzed = [str(random.randint(max(1, int(p) // 2), int(p) * 2 + 5)) for p in parts]
                    return " ".join(fuzzed) + "\n"

            # Pattern B: Line 1 is N, Line 2 is N space-separated tokens
            if len(lines) == 2 and lines[0].isdigit():
                toks = lines[1].split()
                orig_n = int(lines[0])
                if len(toks) == orig_n:
                    new_n = random.randint(max(2, orig_n // 2), max(3, min(25, orig_n * 2)))
                    if all(t.isdigit() or (t.startswith("-") and t[1:].isdigit()) for t in toks):
                        int_vals = [int(t) for t in toks]
                        min_v, max_v = min(int_vals), max(int_vals)
                        new_toks = [str(random.randint(min_v, max(min_v + 1, max_v))) for _ in range(new_n)]
                    else:
                        new_toks = random.choices(toks, k=new_n)
                    return f"{new_n}\n" + " ".join(new_toks) + "\n"

            # Pattern C: Two strings on separate lines (e.g. anagram check, subsequence)
            if len(lines) == 2 and all(not l.isdigit() for l in lines):
                chars = list(string.ascii_lowercase)
                s1_len = random.randint(4, 12)
                s1 = "".join(random.choices(chars[:6], k=s1_len))
                if random.random() < 0.5:
                    s2_chars = list(s1)
                    random.shuffle(s2_chars)
                    s2 = "".join(s2_chars)
                else:
                    s2 = "".join(random.choices(chars[:6], k=random.randint(4, 12)))
                return f"{s1}\n{s2}\n"

            # Pattern D: General structure preservation
            # Keep line count and token count per line IDENTICAL to chosen valid testcase
            fuzzed_lines = []
            for line in lines:
                parts = line.split()
                fuzzed_parts = []
                for p in parts:
                    if p.isdigit():
                        val = int(p)
                        val_min = max(0, val - random.randint(0, 5))
                        val_max = val + random.randint(0, 10)
                        fuzzed_parts.append(str(random.randint(val_min, max(val_min + 1, val_max))))
                    elif p.startswith("-") and p[1:].isdigit():
                        val = int(p)
                        fuzzed_parts.append(str(val + random.randint(-5, 5)))
                    elif p.isalpha():
                        chars = list(set(p.lower())) or list("abcde")
                        fuzzed_parts.append("".join(random.choices(chars, k=len(p))))
                    else:
                        fuzzed_parts.append(p)
                fuzzed_lines.append(" ".join(fuzzed_parts))
            return "\n".join(fuzzed_lines) + "\n"
        except Exception:
            pass

    # 3. Standard fallback: N integers
    n = random.randint(3, 10)
    nums = [str(random.randint(1, 50)) for _ in range(n)]
    return f"{n}\n" + " ".join(nums) + "\n"


def _compare_stress_outputs(actual_out: str, expected_out: str) -> tuple[bool, str]:
    """CRLF & trailing whitespace insensitive line comparison."""
    act_lines = [l.rstrip("\r\n \t") for l in actual_out.splitlines()]
    exp_lines = [l.rstrip("\r\n \t") for l in expected_out.splitlines()]

    while act_lines and act_lines[-1] == "":
        act_lines.pop()
    while exp_lines and exp_lines[-1] == "":
        exp_lines.pop()

    if act_lines == exp_lines:
        return True, "Outputs match exactly"

    max_len = max(len(act_lines), len(exp_lines))
    for i in range(max_len):
        act_line = act_lines[i] if i < len(act_lines) else "<EOF>"
        exp_line = exp_lines[i] if i < len(exp_lines) else "<EOF>"
        if act_line != exp_line:
            return False, f"Mismatch at line {i + 1}: expected '{exp_line[:60]}', got '{act_line[:60]}'"

    return False, "Outputs differ"


@app.post("/api/problems/{contest_id}/{problem_id}/stress-test", response_model=StressTestResult)
async def run_stress_test(
    contest_id: str,
    problem_id: str,
    payload: StressTestRequest,
    session_id: Optional[str] = Depends(get_session_id),
):
    """
    Executes automated randomized differential testing comparing user solution
    against a reference brute-force solution until discrepancy or max iterations.
    """
    _, prob = get_contest_and_problem(contest_id, problem_id)
    sid = session_id if isinstance(session_id, str) else None
    prob_dir, workspace_dir, build_dir, custom_dir = get_problem_dirs(
        contest_id, prob.problem_id, sid
    )
    cfg = load_config()

    user_lang = payload.lang or "python"
    user_filename = LANG_FILENAMES.get(user_lang, "solution.py")
    user_source = workspace_dir / user_filename

    if not user_source.exists():
        return StressTestResult(
            status="error",
            message=f"User solution not found at {user_source.name}. Please write or save your solution first.",
        )

    # 1. Compile User Solution
    user_compile = await asyncio.to_thread(
        compile_source,
        user_source,
        user_lang,
        build_dir,
        prob.memory_limit_mb,
        cfg,
    )
    if not user_compile.success:
        return StressTestResult(
            status="error",
            message=f"Compilation error in user solution:\n{user_compile.error}",
        )

    # 2. Locate Reference Solution candidates
    sub_dir = prob_dir / "submissions"
    ref_candidates: list[Path] = []

    if payload.brute_ref:
        clean_ref = payload.brute_ref.replace("\\", "/").strip().lstrip("/")
        stripped_sub = clean_ref[12:] if clean_ref.startswith("submissions/") else clean_ref
        for cand in [
            workspace_dir / clean_ref,
            prob_dir / clean_ref,
            sub_dir / clean_ref,
            sub_dir / stripped_sub,
            prob_dir / stripped_sub,
        ]:
            if cand.exists() and cand.is_file():
                ref_candidates.append(cand)
                break

    if not ref_candidates:
        # Check workspace first for custom brute force
        for w_cand in [
            workspace_dir / "brute.py",
            workspace_dir / "brute.cpp",
            workspace_dir / "solution_brute.py",
            workspace_dir / "ref.py",
        ]:
            if w_cand.exists() and w_cand.is_file():
                ref_candidates.append(w_cand)

        # Collect all viable reference files under submissions
        sub_files: list[tuple[bool, int, Path]] = []
        if sub_dir.exists():
            for f in sub_dir.rglob("*"):
                if f.is_file() and not f.name.startswith("._") and f.suffix.lower() in EXTENSION_TO_LANG:
                    is_accepted = "accepted" in [p.lower() for p in f.parts]
                    f_ext = f.suffix.lower()
                    f_lang = EXTENSION_TO_LANG.get(f_ext, "")
                    # Prioritize matching user language, then Python, then C++, then Java
                    lang_score = 0
                    if f_lang == user_lang:
                        lang_score = 4
                    elif f_lang == "python":
                        lang_score = 3
                    elif f_lang == "cpp":
                        lang_score = 2
                    elif f_lang == "java":
                        lang_score = 1
                    sub_files.append((is_accepted, lang_score, f))

        # Sort: accepted first, then highest lang score
        sub_files.sort(key=lambda x: (1 if x[0] else 0, x[1]), reverse=True)
        for _, _, f in sub_files:
            ref_candidates.append(f)

    if not ref_candidates:
        return StressTestResult(
            status="error",
            message="No brute-force or reference submission found for differential testing on this problem.",
        )

    # 3. Compile Reference Solution (try candidates until one compiles successfully)
    ref_compile = None
    ref_path = None
    ref_build_dir = build_dir / "ref_build"
    ref_build_dir.mkdir(parents=True, exist_ok=True)

    for cand_path in ref_candidates:
        cand_ext = cand_path.suffix.lower()
        cand_lang = EXTENSION_TO_LANG.get(cand_ext, "cpp")
        c_res = await asyncio.to_thread(
            compile_source,
            cand_path,
            cand_lang,
            ref_build_dir,
            prob.memory_limit_mb,
            cfg,
        )
        if c_res.success:
            ref_compile = c_res
            ref_path = cand_path
            break

    if not ref_compile or not ref_path:
        return StressTestResult(
            status="error",
            message=f"Failed to compile reference solution from available candidates ({ref_candidates[0].name}).",
        )

    # 4. Run Iterations
    iterations = max(1, min(payload.max_iterations, 300))
    valid_tested = 0
    max_attempts = iterations * 2

    for it in range(1, max_attempts + 1):
        if valid_tested >= iterations:
            break

        test_input = _generate_stress_input(prob_dir, workspace_dir, it, custom_dir=custom_dir)

        # Run reference solution first (acts as the oracle)
        ref_res: CustomRunResult = await asyncio.to_thread(
            run_custom_input,
            ref_compile.run_cmd,
            test_input,
            ref_build_dir,
            prob.time_limit_sec,
            prob.memory_limit_mb,
            cfg.max_preview_bytes,
        )

        # If reference solution did not succeed (e.g. invalid input for problem), skip
        if ref_res.verdict != Verdict.AC.value:
            continue

        valid_tested += 1

        # Run user solution
        user_res: CustomRunResult = await asyncio.to_thread(
            run_custom_input,
            user_compile.run_cmd,
            test_input,
            build_dir,
            prob.time_limit_sec,
            prob.memory_limit_mb,
            cfg.max_preview_bytes,
        )

        # Check if user solution failed while reference succeeded
        if user_res.verdict != Verdict.AC.value:
            return StressTestResult(
                status="mismatch",
                iteration=valid_tested,
                input_text=test_input[:1000],
                actual_output=user_res.stdout_preview or user_res.stderr_preview,
                expected_output=ref_res.stdout_preview,
                diff_message=f"User solution encountered {user_res.verdict} on valid testcase #{valid_tested} (Reference gave AC)",
                message=f"Failed on testcase #{valid_tested} with {user_res.verdict}",
            )

        # Compare outputs
        is_match, diff_msg = _compare_stress_outputs(user_res.stdout_preview, ref_res.stdout_preview)
        if not is_match:
            return StressTestResult(
                status="mismatch",
                iteration=valid_tested,
                input_text=test_input[:1000],
                actual_output=user_res.stdout_preview,
                expected_output=ref_res.stdout_preview,
                diff_message=diff_msg,
                message=f"Discrepancy found on iteration #{valid_tested}!",
            )

    return StressTestResult(
        status="passed",
        iteration=valid_tested,
        message=f"Passed all {valid_tested} randomized stress test iterations against {ref_path.name} with zero discrepancies!",
    )


# =====================================================================
# Static File Mount & Root Route
# =====================================================================

@app.get("/")
def get_index():
    """Serves index.html or welcome placeholder if frontend is not yet created."""
    index_html = STATIC_DIR / "index.html"
    if index_html.exists() and index_html.is_file():
        return FileResponse(index_html, media_type="text/html")

    return HTMLResponse(
        content="""<!DOCTYPE html>
<html>
<head><title>Local CP Judge</title></head>
<body style="background:#1e1e1e;color:#eee;font-family:sans-serif;padding:2rem;">
  <h2>Local CP Judge Backend Running</h2>
  <p>Visit <a href="/docs" style="color:#58a6ff;">/docs</a> for interactive Swagger API documentation.</p>
</body>
</html>"""
    )


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

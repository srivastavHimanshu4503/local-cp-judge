from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
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
    JudgeRunRequest,
    JudgeSummary,
    OpenExternalRequest,
    ProblemMeta,
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
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

WORKSPACES_ROOT.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

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


@app.get("/api/problems/{contest_id}/{problem_id}/pdf")
def get_problem_pdf(contest_id: str, problem_id: str):
    """Serves the problem statement PDF with inline content disposition."""
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir = WORKSPACES_ROOT / contest_id / problem_id
    pdf_path = problem_dir / "problem.pdf"

    if not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"problem.pdf not found for problem '{problem_id}'."
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=problem.pdf"},
    )


@app.get("/api/problems/{contest_id}/{problem_id}/code", response_model=CodeResponse)
def get_problem_code(
    contest_id: str,
    problem_id: str,
    lang: str = Query(default="cpp"),
    ref_path: Optional[str] = Query(default=None),
) -> CodeResponse:
    """
    Reads code from either the user's local workspace (solution.cpp, solution.py, Main.java)
    or an included reference submission under submissions/.
    """
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir = WORKSPACES_ROOT / contest_id / problem_id

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
        workspace_dir = problem_dir / "workspace"
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
) -> CodeResponse:
    """Writes updated source code directly to the local workspace file on disk."""
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir = WORKSPACES_ROOT / contest_id / problem_id
    workspace_dir = problem_dir / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)

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
):
    """
    Launches VS Code focusing the active workspace file, or opens the workspace
    directory in Windows File Explorer.
    """
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir = WORKSPACES_ROOT / contest_id / problem_id
    workspace_dir = problem_dir / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    lang_key = (payload.lang or "cpp").lower()
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
) -> AsyncGenerator[str, None]:
    """
    Async generator executing the test suite and yielding standard SSE frames:
    status -> compile_error (if CE) -> compile_success -> test_start/test_result -> summary.
    """
    try:
        contest, prob = get_contest_and_problem(contest_id, problem_id)
    except HTTPException as e:
        yield f"event: compile_error\ndata: {json.dumps({'verdict': 'CE', 'error': e.detail})}\n\n"
        return

    problem_dir = WORKSPACES_ROOT / contest_id / problem_id
    workspace_dir = problem_dir / "workspace"
    build_dir = workspace_dir / ".build"
    build_dir.mkdir(parents=True, exist_ok=True)

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
    test_cases = get_problem_test_cases(problem_dir, suite=suite)
    yield f"event: compile_success\ndata: {json.dumps({'total_tests': len(test_cases), 'compile_time_ms': compile_res.compile_time_ms})}\n\n"

    passed_count = 0
    max_time_ms = 0.0
    max_mem_mb = 0.0
    first_failing_verdict: Optional[str] = None

    # 4. Stream each test case execution
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
async def run_judge_stream_post(payload: JudgeRunRequest):
    """POST endpoint for real-time Server-Sent Events test case judging stream."""
    return StreamingResponse(
        stream_judge_execution(
            contest_id=payload.contest_id,
            problem_id=payload.problem_id,
            lang=payload.lang,
            suite=payload.suite,
            ref_submission=payload.ref_submission,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/judge/run-stream")
async def run_judge_stream_get(
    contest_id: str = Query(...),
    problem_id: str = Query(...),
    lang: str = Query(default="cpp"),
    suite: str = Query(default="sample"),
    ref_submission: Optional[str] = Query(default=None),
):
    """GET endpoint for real-time Server-Sent Events test case judging stream."""
    return StreamingResponse(
        stream_judge_execution(
            contest_id=contest_id,
            problem_id=problem_id,
            lang=lang,
            suite=suite,
            ref_submission=ref_submission,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/judge/custom", response_model=CustomRunResult)
async def judge_custom_input(payload: CustomRunRequest) -> CustomRunResult:
    """Executes user code or reference submission against custom stdin text."""
    contest, prob = get_contest_and_problem(payload.contest_id, payload.problem_id)
    problem_dir = WORKSPACES_ROOT / payload.contest_id / payload.problem_id
    workspace_dir = problem_dir / "workspace"
    build_dir = workspace_dir / ".build"
    build_dir.mkdir(parents=True, exist_ok=True)

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

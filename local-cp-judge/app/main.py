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
    ChecklistPayload,
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
    OfficialSolutionItem,
    OpenExternalRequest,
    ProblemMeta,
    ProblemSolutionsResponse,
    SampleTestCaseItem,
    SampleTestCaseUpdate,
    StressTestRequest,
    StressTestResult,
    SystemStatus,
    Verdict,
)
from app.parser import (
    MOCK_QUIZ_CONTEST_ID,
    extract_and_parse_contest,
    generate_mock_quiz,
    get_problem_test_cases,
    is_ignored_path,
    list_contests,
    load_contest,
    natural_sort_key,
    resolve_problem_template,
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
    "python": "solution.py",
    "py": "solution.py",
    "java": "Main.java",
}

EXTENSION_TO_LANG = {
    ".py": "python",
    ".java": "java",
}


def _resolve_supported_lang(lang: str) -> str:
    """Validates and normalizes language to 'python' or 'java'."""
    lang_key = (lang or "").lower().strip()
    if lang_key in ("python", "py"):
        return "python"
    if lang_key == "java":
        return "java"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported language '{lang}'. Only Python and Java are supported.",
    )

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
    """Initializes an isolated per-user workspace strictly from problem templates (or empty files)."""
    workspace_dir.mkdir(parents=True, exist_ok=True)
    for lang_key, fname in (("python", "solution.py"), ("java", "Main.java")):
        dst = workspace_dir / fname
        if not dst.exists():
            prob_tpl = resolve_problem_template(shared_problem_dir, lang_key)
            if prob_tpl and prob_tpl.exists():
                shutil.copy2(prob_tpl, dst)
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


def _get_sample_overrides_dir(
    contest_id: str,
    problem_id: str,
    session_id: Optional[str] = None,
) -> Path:
    """
    Returns per-session directory for edited sample testcases without ever touching
    canonical problem data/sample or data/secret files.
    """
    shared_dir = WORKSPACES_ROOT / contest_id / problem_id
    sid = _sanitize_session_id(session_id)
    if sid:
        sample_dir = USER_WORKSPACES_ROOT / sid / contest_id / problem_id / "sample_overrides"
    else:
        sample_dir = shared_dir / "workspace" / "sample_overrides"
    sample_dir.mkdir(parents=True, exist_ok=True)
    return sample_dir


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


def _get_checklist_file(session_id: Optional[str]) -> Path:
    sid = _sanitize_session_id(session_id)
    if sid:
        base = USER_WORKSPACES_ROOT / sid
        base.mkdir(parents=True, exist_ok=True)
        return base / "checklist.json"
    return WORKSPACES_ROOT / ".checklist.json"


@app.get("/api/checklist", response_model=ChecklistPayload)
def get_contest_checklist(session_id: Optional[str] = Depends(get_session_id)) -> ChecklistPayload:
    """Loads persisted contest completion checklist for the active session."""
    path = _get_checklist_file(session_id)
    if not path.exists() or not path.is_file():
        return ChecklistPayload(contests={}, updated_at=None)
    try:
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        if isinstance(raw, dict):
            return ChecklistPayload.model_validate(raw)
    except Exception:
        pass
    return ChecklistPayload(contests={}, updated_at=None)


@app.put("/api/checklist", response_model=ChecklistPayload)
def save_contest_checklist(
    payload: ChecklistPayload,
    session_id: Optional[str] = Depends(get_session_id),
) -> ChecklistPayload:
    """Persists contest completion checklist state to disk for the active session."""
    path = _get_checklist_file(session_id)
    path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    return payload


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


def _ensure_mock_quiz_exists() -> None:
    """Seeds an initial 4-question Mock Quiz contest if none exists yet."""
    mock_meta = WORKSPACES_ROOT / MOCK_QUIZ_CONTEST_ID / "contest_meta.json"
    if mock_meta.exists():
        return
    try:
        generate_mock_quiz(WORKSPACES_ROOT, TEMPLATES_DIR, contest_id=MOCK_QUIZ_CONTEST_ID, seed=42)
    except Exception:
        pass


@app.post("/api/contests/mock-quiz", response_model=ContestMeta)
async def create_or_shuffle_mock_quiz(
    seed: Optional[int] = Query(default=None),
    session_id: Optional[str] = Depends(get_session_id),
) -> ContestMeta:
    """Generates a fresh 4-question Mockup Quiz (A, B, C, D) from different available contests."""
    try:
        contest_meta = await asyncio.to_thread(
            generate_mock_quiz,
            WORKSPACES_ROOT,
            TEMPLATES_DIR,
            MOCK_QUIZ_CONTEST_ID,
            seed,
        )
        sid = _sanitize_session_id(session_id)
        if sid:
            user_mock_dir = USER_WORKSPACES_ROOT / sid / MOCK_QUIZ_CONTEST_ID
            if user_mock_dir.exists():
                shutil.rmtree(user_mock_dir, ignore_errors=True)
        return contest_meta
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate mock quiz: {e}",
        )


@app.get("/api/contests", response_model=list[ContestMeta])
def list_all_contests() -> list[ContestMeta]:
    """Lists all imported contests in workspaces_root."""
    _ensure_mock_quiz_exists()
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


OBSIDIAN_STATEMENT_CSS = """<style id="obsidian-markdown-v2">
/* obsidian-markdown-v2 */
:root {
  --ink: #D4D4D8 !important;
  --muted: #A1A1AA !important;
  --accent: #FAFAFA !important;
  --paper: #09090B !important;
  --panel: #111115 !important;
  --rule: #27272A !important;
  --line: #27272A !important;
  --bg-app: #09090B !important;
  --bg-panel: #111115 !important;
  --bg-surface-subtle: #18181B !important;
  --border-subtle: #27272A !important;
  --text-primary: #FAFAFA !important;
  --text-secondary: #D4D4D8 !important;
  --text-muted: #A1A1AA !important;
}
* {
  box-sizing: border-box;
  scrollbar-width: thin;
  scrollbar-color: #27272A transparent;
}
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #27272A; border-radius: 9999px; }
::-webkit-scrollbar-thumb:hover { background: #3F3F46; }
html {
  background: #09090B !important;
  color: #D4D4D8 !important;
  max-width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
}
body {
  background: #09090B !important;
  color: #D4D4D8 !important;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
  font-size: 18px !important;
  line-height: 1.75 !important;
  max-width: 100% !important;
  margin: 0 !important;
  padding: 24px 28px 44px !important;
  -webkit-font-smoothing: antialiased;
}
main, .statement-container {
  max-width: 82ch !important;
  margin: 0 auto !important;
  padding: 0 !important;
}
header, header#title-block-header {
  margin: 0 0 18px 0 !important;
  text-align: left !important;
  padding-bottom: 14px !important;
  border-bottom: 1px solid #27272A !important;
}
h1, h1.title, .title-row h1 {
  font-size: 28px !important;
  line-height: 1.25 !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em !important;
  color: #FAFAFA !important;
  margin: 0 0 8px 0 !important;
}
.letter {
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  color: #10B981 !important;
  margin: 0 0 6px 0 !important;
}
h1 .letter {
  font-size: 1.05em !important;
  color: #10B981 !important;
  margin-right: 0.35em !important;
}
h2, .section-title {
  font-size: 21px !important;
  line-height: 1.35 !important;
  font-weight: 600 !important;
  color: #FAFAFA !important;
  margin: 26px 0 12px 0 !important;
  padding-bottom: 6px !important;
  border-bottom: 1px solid #27272A !important;
}
h3 {
  font-size: 19px !important;
  font-weight: 600 !important;
  color: #F4F4F5 !important;
  margin: 18px 0 10px 0 !important;
}
p, li {
  font-size: 18px !important;
  line-height: 1.75 !important;
  color: #D4D4D8 !important;
  max-width: none !important;
}
p { margin: 0 0 13px 0 !important; }
ul, ol { padding-left: 1.45em !important; margin: 8px 0 16px 0 !important; }
li { margin: 6px 0 !important; }
strong, b { color: #FAFAFA !important; font-weight: 600 !important; }
em {
  font-size: inherit !important;
  color: #F4F4F5 !important;
  font-style: italic;
}
.subtitle, .meta, h1 + p em {
  color: #A1A1AA !important;
  font-size: 15.5px !important;
  font-style: normal !important;
}
.explain, .example-explanation {
  font-size: 17px !important;
  line-height: 1.72 !important;
  color: #E4E4E7 !important;
  background: #111115 !important;
  border: 1px solid #27272A !important;
  padding: 12px 14px !important;
  border-radius: 8px !important;
}
.dp-analysis-card {
  background: #111115 !important;
  border: 1px solid #3F3F46 !important;
  border-left: 3px solid #10B981 !important;
  border-radius: 10px !important;
  padding: 18px 20px !important;
  margin-top: 26px !important;
  color: #E4E4E7 !important;
}
.dp-analysis-card h3 {
  font-size: 20px !important;
  color: #34D399 !important;
  margin: 0 0 12px 0 !important;
}
.dp-analysis-card p, .dp-analysis-card li {
  font-size: 18px !important;
  line-height: 1.75 !important;
  color: #E4E4E7 !important;
}
.dp-analysis-card pre {
  background: #09090B !important;
  border: 1px solid #27272A !important;
  border-left: 3px solid #10B981 !important;
}
.sample h3, .example h3 {
  font-size: 15px !important;
  color: #D4D4D8 !important;
  margin: 0 0 8px 0 !important;
}
hr, .page-break {
  border-color: #27272A !important;
}
a, a:visited, .source-link { color: #60A5FA !important; font-size: 15px !important; }
.meta-chip {
  font-size: 14px !important;
  padding: 5px 12px !important;
  background: #18181B !important;
  border: 1px solid #27272A !important;
  color: #E4E4E7 !important;
}
code {
  background: #18181B !important;
  border: 1px solid #27272A !important;
  color: #FAFAFA !important;
  font-family: "JetBrains Mono", Consolas, monospace !important;
  font-size: 0.92em !important;
  padding: 2px 6px !important;
  border-radius: 5px !important;
}
pre, div.sourceCode, .io-card, .insight-box {
  background: #111115 !important;
  border: 1px solid #27272A !important;
  border-radius: 10px !important;
  color: #FAFAFA !important;
}
pre, .io-card pre {
  border-left: 3px solid #3F3F46 !important;
  padding: 13px 16px !important;
  margin: 10px 0 16px 0 !important;
  font-family: "JetBrains Mono", Consolas, monospace !important;
  font-size: 16px !important;
  line-height: 1.62 !important;
  color: #FAFAFA !important;
  overflow-x: auto !important;
}
.io-card pre {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 2px 0 !important;
  margin: 0 !important;
}
pre code {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  font-size: 16px !important;
}
.io-card .io-header, .io-card-header {
  background: #18181B !important;
  border-bottom: 1px solid #27272A !important;
  font-size: 15px !important;
  color: #E4E4E7 !important;
}
.io-card-title {
  font-size: 15px !important;
  font-weight: 600 !important;
  color: #FAFAFA !important;
}
.btn-copy-sample {
  font-size: 13.5px !important;
  color: #A1A1AA !important;
}
.io-card .io-body {
  font-size: 16px !important;
  color: #FAFAFA !important;
}
table {
  border-collapse: collapse !important;
  width: 100% !important;
  margin: 14px 0 20px 0 !important;
  font-size: 16.5px !important;
  display: table !important;
}
tbody { border-color: #27272A !important; }
th {
  background: #18181B !important;
  color: #FAFAFA !important;
  border: 1px solid #27272A !important;
  padding: 8px 12px !important;
}
td {
  background: #09090B !important;
  color: #D4D4D8 !important;
  border: 1px solid #27272A !important;
  padding: 8px 12px !important;
}
blockquote {
  background: #111115 !important;
  border: 1px solid #27272A !important;
  border-left: 3px solid #10B981 !important;
  color: #D4D4D8 !important;
  padding: 12px 16px !important;
  margin: 14px 0 !important;
  border-radius: 8px !important;
}
blockquote p { margin: 0 !important; }
.obsidian-origin-banner {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  flex-wrap: wrap !important;
  gap: 8px !important;
  padding: 9px 14px !important;
  margin-bottom: 16px !important;
  background: rgba(139, 92, 246, 0.1) !important;
  border: 1px solid rgba(139, 92, 246, 0.32) !important;
  border-radius: 8px !important;
  font-size: 14px !important;
  color: #E4E4E7 !important;
}
.obsidian-origin-tag {
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 0.05em !important;
  text-transform: uppercase !important;
  color: #DDD6FE !important;
  background: rgba(139, 92, 246, 0.22) !important;
  padding: 2px 7px !important;
  border-radius: 5px !important;
  margin-right: 8px !important;
}
</style>"""


def _render_plain_markdown_to_html(md_text: str, title: str = "Problem Statement") -> str:
    """Lightweight Markdown-to-HTML fallback when only .md or extracted PDF text is present."""
    import html as html_lib

    lines = md_text.splitlines()
    out: list[str] = []
    in_code = False
    in_list = False
    for line in lines:
        if line.strip().startswith("```"):
            if in_list:
                out.append("</ul>")
                in_list = False
            if not in_code:
                out.append("<pre><code>")
                in_code = True
            else:
                out.append("</code></pre>")
                in_code = False
            continue
        if in_code:
            out.append(html_lib.escape(line))
            continue
        s = line.strip()
        if not s:
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        if s.startswith("# "):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<h1>{html_lib.escape(s[2:].strip())}</h1>")
        elif s.startswith("## "):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<h2>{html_lib.escape(s[3:].strip())}</h2>")
        elif s.startswith("### "):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<h3>{html_lib.escape(s[4:].strip())}</h3>")
        elif s.startswith(("- ", "* ")):
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = re.sub(r"`([^`]+)`", lambda m: f"<code>{html_lib.escape(m.group(1))}</code>", html_lib.escape(s[2:].strip()))
            out.append(f"<li>{item}</li>")
        else:
            if in_list: out.append("</ul>"); in_list = False
            para = re.sub(r"`([^`]+)`", lambda m: f"<code>{html_lib.escape(m.group(1))}</code>", html_lib.escape(s))
            para = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", para)
            out.append(f"<p>{para}</p>")
    if in_list:
        out.append("</ul>")
    if in_code:
        out.append("</code></pre>")
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html_lib.escape(title)}</title></head><body><main>{''.join(out)}</main></body></html>"


def _inject_obsidian_css(raw_html: str, prob: Optional[ProblemMeta] = None) -> str:
    """Appends Obsidian Dark Markdown CSS last in document order and optional mock source banner."""
    import html as html_lib

    html_out = raw_html
    if prob and prob.source_contest_title and "obsidian-origin-banner" not in html_out:
        origin_text = f"{prob.source_contest_title} &bull; Problem {html_lib.escape(prob.short_name)}"
        if prob.source_problem_id:
            origin_text += f" ({html_lib.escape(prob.source_problem_id)})"
        banner_html = (
            '<div class="obsidian-origin-banner">'
            '<div><span class="obsidian-origin-tag">Mockup Source</span>'
            f'<span>Belongs to <strong>{origin_text}</strong></span></div>'
            '</div>'
        )
        if "<main>" in html_out:
            html_out = html_out.replace("<main>", f"<main>\n{banner_html}", 1)
        elif re.search(r"<body[^>]*>", html_out, flags=re.IGNORECASE):
            html_out = re.sub(r"(<body[^>]*>)", rf"\1\n{banner_html}", html_out, count=1, flags=re.IGNORECASE)

    if "obsidian-markdown-v2" in html_out:
        return html_out
    if "</body>" in html_out:
        return html_out.replace("</body>", OBSIDIAN_STATEMENT_CSS + "\n</body>", 1)
    if "</html>" in html_out:
        return html_out.replace("</html>", OBSIDIAN_STATEMENT_CSS + "\n</html>", 1)
    return html_out + "\n" + OBSIDIAN_STATEMENT_CSS


@app.get("/api/problems/{contest_id}/{problem_id}/statement")
def get_problem_statement(
    contest_id: str,
    problem_id: str,
    format: str = Query(default="auto"),
    embed: int = Query(default=0),
):
    """Serves unified dark Markdown/HTML statement by default, or PDF when format='pdf'."""
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir = WORKSPACES_ROOT / contest_id / problem_id
    req_fmt = (format or "auto").lower().strip()
    banner_prob = None if embed else prob

    pdf_candidates = [problem_dir / "problem.pdf", problem_dir / "statement" / "problem.pdf"]

    # Explicit PDF request
    if req_fmt == "pdf":
        for candidate in pdf_candidates:
            if candidate.exists() and candidate.is_file():
                return FileResponse(
                    path=candidate,
                    media_type="application/pdf",
                    headers={"Content-Disposition": "inline; filename=problem.pdf"},
                )

    # 1. Prefer HTML statements and wrap/override uniformly in Obsidian Dark Markdown v2
    for candidate in [problem_dir / "statement.html", problem_dir / "problem.html", problem_dir / "statement" / "problem.html"]:
        if candidate.exists() and candidate.is_file():
            raw_html = _inject_obsidian_css(candidate.read_text(encoding="utf-8", errors="replace"), prob=banner_prob)
            return HTMLResponse(content=raw_html)

    # 2. Markdown fallback if only .md exists
    for candidate in [problem_dir / "problem.md", problem_dir / "statement.md", problem_dir / "statement" / "problem.md"]:
        if candidate.exists() and candidate.is_file():
            md_html = _render_plain_markdown_to_html(candidate.read_text(encoding="utf-8", errors="replace"), title=prob.name)
            return HTMLResponse(content=_inject_obsidian_css(md_html, prob=banner_prob))

    # 3. PDF-only fallback (try pdftotext -> dark view, else inline PDF)
    for candidate in pdf_candidates:
        if candidate.exists() and candidate.is_file():
            pdftotext_cmd = shutil.which("pdftotext") or (
                r"C:\Program Files\poppler-25.12.0\Library\bin\pdftotext.exe"
                if Path(r"C:\Program Files\poppler-25.12.0\Library\bin\pdftotext.exe").exists()
                else None
            )
            if req_fmt != "pdf" and pdftotext_cmd:
                try:
                    ext = subprocess.run([pdftotext_cmd, str(candidate), "-"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5)
                    if ext.returncode == 0 and ext.stdout.strip():
                        md_html = _render_plain_markdown_to_html(ext.stdout, title=prob.name)
                        return HTMLResponse(content=_inject_obsidian_css(md_html, prob=banner_prob))
                except Exception:
                    pass
            return FileResponse(
                path=candidate,
                media_type="application/pdf",
                headers={"Content-Disposition": "inline; filename=problem.pdf"},
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Statement not found for problem '{problem_id}'."
    )


@app.get("/api/problems/{contest_id}/{problem_id}/pdf")
def get_problem_pdf(contest_id: str, problem_id: str):
    """Serves the problem statement PDF with inline content disposition."""
    return get_problem_statement(contest_id, problem_id, format="pdf")


def _solution_priority(file_path: Path, short_name: str, lang: str) -> tuple[int, list[int | str]]:
    """Orders accepted solutions so the clearest canonical reference appears first."""
    name_lower = file_path.name.lower()
    stem_lower = file_path.stem.lower()
    short_lower = (short_name or "").lower()
    if lang == "python":
        if name_lower == "ref.py":
            rank = 0
        elif name_lower == "solution.py":
            rank = 1
        elif short_lower and stem_lower == short_lower:
            rank = 2
        else:
            rank = 3
    else:
        if name_lower == "ref.java":
            rank = 0
        elif name_lower == "main.java":
            rank = 1
        elif name_lower == "solution.java":
            rank = 2
        elif short_lower and stem_lower == short_lower:
            rank = 3
        else:
            rank = 4
    return (rank, natural_sort_key(file_path.name))


@app.get("/api/problems/{contest_id}/{problem_id}/solutions", response_model=ProblemSolutionsResponse)
def get_problem_solutions(contest_id: str, problem_id: str) -> ProblemSolutionsResponse:
    """Returns official accepted Python and Java solutions for Practice Mode inspection."""
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir = WORKSPACES_ROOT / contest_id / prob.problem_id

    candidate_roots = [problem_dir / "submissions" / "accepted", problem_dir / "solutions" / "accepted"]
    if prob.source_contest_id and prob.source_problem_id:
        src_dir = WORKSPACES_ROOT / prob.source_contest_id / prob.source_problem_id
        candidate_roots.extend([src_dir / "submissions" / "accepted", src_dir / "solutions" / "accepted"])

    by_lang_files: dict[str, dict[str, Path]] = {"python": {}, "java": {}}
    for acc_dir in candidate_roots:
        if not acc_dir.exists() or not acc_dir.is_dir():
            continue
        for f in acc_dir.iterdir():
            if not f.is_file() or is_ignored_path(f):
                continue
            lang_key = EXTENSION_TO_LANG.get(f.suffix.lower())
            if lang_key and f.name not in by_lang_files[lang_key]:
                by_lang_files[lang_key][f.name] = f

    grouped: dict[str, list[OfficialSolutionItem]] = {"python": [], "java": []}
    for lang_key in ("python", "java"):
        files = sorted(by_lang_files[lang_key].values(), key=lambda p: _solution_priority(p, prob.short_name, lang_key))
        for idx, sol_file in enumerate(files):
            grouped[lang_key].append(
                OfficialSolutionItem(
                    lang=lang_key,
                    filename=sol_file.name,
                    ref_path=f"accepted/{sol_file.name}",
                    code=sol_file.read_text(encoding="utf-8", errors="replace"),
                    is_primary=(idx == 0),
                )
            )

    return ProblemSolutionsResponse(
        contest_id=contest_id,
        problem_id=prob.problem_id,
        python=grouped["python"],
        java=grouped["java"],
    )


@app.get("/api/problems/{contest_id}/{problem_id}/code", response_model=CodeResponse)
def get_problem_code(
    contest_id: str,
    problem_id: str,
    lang: str = Query(default="python"),
    ref_path: Optional[str] = Query(default=None),
    session_id: Optional[str] = Depends(get_session_id),
) -> CodeResponse:
    """
    Reads code from either the user's isolated workspace (solution.py, Main.java)
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
        if ext not in EXTENSION_TO_LANG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported reference submission extension '{ext}'. Only Python and Java are supported.",
            )
        inferred_lang = EXTENSION_TO_LANG[ext]
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
        lang_key = _resolve_supported_lang(lang)
        filename = LANG_FILENAMES[lang_key]
        target_file = workspace_dir / filename

        # Treat 0-byte files as un-initialized so the global template is applied.
        file_uninitialized = target_file.exists() and target_file.stat().st_size == 0
        if not target_file.exists() or file_uninitialized:
            prob_tpl = resolve_problem_template(problem_dir, lang_key)
            global_tpl_name = "python_template.py" if lang_key == "python" else "java_template.java"
            global_tpl = TEMPLATES_DIR / global_tpl_name
            if prob_tpl and prob_tpl.exists():
                shutil.copy2(prob_tpl, target_file)
            elif global_tpl.exists():
                shutil.copy2(global_tpl, target_file)
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

    lang_key = _resolve_supported_lang(payload.lang)
    filename = LANG_FILENAMES[lang_key]
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

    lang_key = _resolve_supported_lang(payload.lang or "python")
    filename = LANG_FILENAMES[lang_key]
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

    judge_lang = (lang or "python").lower().strip()

    if ref_submission:
        clean_ref = ref_submission.replace("\\", "/").strip().lstrip("/")
        source_path = (problem_dir / "submissions" / clean_ref).resolve()
        ext = source_path.suffix.lower()
        judge_lang = EXTENSION_TO_LANG.get(ext, "")
        if not judge_lang:
            yield f"event: compile_error\ndata: {json.dumps({'verdict': 'CE', 'error': f'Unsupported reference file extension {ext}. Only Python and Java are supported.'})}\n\n"
            return
    else:
        if judge_lang not in LANG_FILENAMES:
            yield f"event: compile_error\ndata: {json.dumps({'verdict': 'CE', 'error': f'Unsupported language {lang}. Only Python and Java are supported.'})}\n\n"
            return
        judge_lang = "python" if judge_lang == "py" else judge_lang
        filename = LANG_FILENAMES[judge_lang]
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

    # 3. Discover test cases (apply session sample overrides only when running sample suite)
    sample_overrides_dir = (
        _get_sample_overrides_dir(contest_id, prob.problem_id, session_id)
        if suite == "sample"
        else None
    )
    test_cases = get_problem_test_cases(
        problem_dir,
        suite=suite,
        custom_tests_dir=custom_dir,
        sample_overrides_dir=sample_overrides_dir,
    )
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

    if payload.ref_submission:
        clean_ref = payload.ref_submission.replace("\\", "/").strip().lstrip("/")
        source_path = (problem_dir / "submissions" / clean_ref).resolve()
        ext = source_path.suffix.lower()
        if ext not in EXTENSION_TO_LANG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported reference file extension '{ext}'. Only Python and Java are supported.",
            )
        judge_lang = EXTENSION_TO_LANG[ext]
    else:
        judge_lang = _resolve_supported_lang(payload.lang)
        filename = LANG_FILENAMES[judge_lang]
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
# Editable Sample Test Cases Endpoints (Sample Suite Only; Secret Locked)
# =====================================================================

MAX_EDITABLE_SAMPLE_BYTES = 65536


def _find_canonical_sample_dir(problem_dir: Path) -> Optional[Path]:
    for sub in (problem_dir / "data" / "sample", problem_dir / "tests" / "sample"):
        if sub.exists() and sub.is_dir():
            return sub
    return None


def _safe_read_sample_file(path: Optional[Path]) -> tuple[str, bool]:
    if not path or not path.exists() or not path.is_file():
        return "", False
    try:
        size = path.stat().st_size
    except OSError:
        return "", False
    if size > MAX_EDITABLE_SAMPLE_BYTES:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(MAX_EDITABLE_SAMPLE_BYTES), True
    return path.read_text(encoding="utf-8", errors="replace"), False


def _iter_canonical_samples(problem_dir: Path) -> list[tuple[str, Path, Optional[Path], Optional[Path]]]:
    sample_dir = _find_canonical_sample_dir(problem_dir)
    if not sample_dir:
        return []

    in_files = [
        f for f in sample_dir.glob("*.in")
        if f.is_file() and not is_ignored_path(f)
    ]
    in_files.sort(key=lambda f: natural_sort_key(f.stem))

    entries: list[tuple[str, Path, Optional[Path], Optional[Path]]] = []
    for in_file in in_files:
        stem = in_file.stem
        ans_file: Optional[Path] = sample_dir / f"{stem}.ans"
        if not ans_file.exists():
            alt_out = sample_dir / f"{stem}.out"
            ans_file = alt_out if alt_out.exists() else None
        desc_file = sample_dir / f"{stem}.desc"
        entries.append((
            stem,
            in_file,
            ans_file,
            desc_file if desc_file.exists() and not is_ignored_path(desc_file) else None,
        ))
    return entries


def _resolve_canonical_sample_entry(
    problem_dir: Path,
    sample_name: str,
) -> tuple[str, Path, Optional[Path], Optional[Path]]:
    raw = (sample_name or "").strip()
    if (
        not raw
        or ".." in raw
        or "/" in raw
        or "\\" in raw
        or raw.lower().startswith("secret")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only sample test cases can be edited; secret or path-qualified test names are not allowed.",
        )

    for stem, in_file, ans_file, desc_file in _iter_canonical_samples(problem_dir):
        if stem == raw:
            return stem, in_file, ans_file, desc_file

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Sample test case '{raw}' not found. Only existing sample test cases can be edited.",
    )


def _build_sample_item(
    stem: str,
    canon_in: Path,
    canon_ans: Optional[Path],
    desc_file: Optional[Path],
    overrides_dir: Path,
) -> SampleTestCaseItem:
    ov_in = overrides_dir / f"{stem}.in"
    ov_ans = overrides_dir / f"{stem}.ans"
    has_ov_in = ov_in.exists() and ov_in.is_file()
    has_ov_ans = ov_ans.exists() and ov_ans.is_file()

    in_text, in_trunc = _safe_read_sample_file(ov_in if has_ov_in else canon_in)
    ans_text, ans_trunc = _safe_read_sample_file(ov_ans if has_ov_ans else canon_ans)

    desc_text = ""
    if desc_file:
        try:
            desc_text = desc_file.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            desc_text = ""

    return SampleTestCaseItem(
        name=stem,
        test_name=f"sample/{stem}",
        input_text=in_text,
        expected_text=ans_text,
        description=desc_text,
        is_edited=(has_ov_in or has_ov_ans),
        is_truncated=(in_trunc or ans_trunc),
    )


@app.get("/api/problems/{contest_id}/{problem_id}/sample-tests", response_model=list[SampleTestCaseItem])
def list_sample_tests(
    contest_id: str,
    problem_id: str,
    session_id: Optional[str] = Depends(get_session_id),
):
    """Lists canonical sample test cases merged with any active session edits (never secret tests)."""
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir = WORKSPACES_ROOT / contest_id / prob.problem_id
    overrides_dir = _get_sample_overrides_dir(contest_id, prob.problem_id, session_id)

    return [
        _build_sample_item(stem, in_file, ans_file, desc_file, overrides_dir)
        for stem, in_file, ans_file, desc_file in _iter_canonical_samples(problem_dir)
    ]


@app.put("/api/problems/{contest_id}/{problem_id}/sample-tests/{sample_name}", response_model=SampleTestCaseItem)
def update_sample_test(
    contest_id: str,
    problem_id: str,
    sample_name: str,
    payload: SampleTestCaseUpdate,
    session_id: Optional[str] = Depends(get_session_id),
):
    """Saves session-isolated edits for an existing sample test case only."""
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir = WORKSPACES_ROOT / contest_id / prob.problem_id
    stem, canon_in, canon_ans, desc_file = _resolve_canonical_sample_entry(problem_dir, sample_name)

    _, in_trunc = _safe_read_sample_file(canon_in)
    _, ans_trunc = _safe_read_sample_file(canon_ans)
    if in_trunc or ans_trunc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sample test case '{stem}' exceeds {MAX_EDITABLE_SAMPLE_BYTES} bytes and cannot be edited in the UI.",
        )

    in_text = payload.input_text or ""
    exp_text = payload.expected_text or ""
    if (
        len(in_text.encode("utf-8", errors="replace")) > MAX_EDITABLE_SAMPLE_BYTES
        or len(exp_text.encode("utf-8", errors="replace")) > MAX_EDITABLE_SAMPLE_BYTES
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Edited sample content exceeds the {MAX_EDITABLE_SAMPLE_BYTES}-byte limit.",
        )

    overrides_dir = _get_sample_overrides_dir(contest_id, prob.problem_id, session_id)
    ov_in = overrides_dir / f"{stem}.in"
    ov_ans = overrides_dir / f"{stem}.ans"

    with open(ov_in, "w", encoding="utf-8", errors="replace", newline="\n") as f:
        f.write(in_text)
    with open(ov_ans, "w", encoding="utf-8", errors="replace", newline="\n") as f:
        f.write(exp_text)

    return _build_sample_item(stem, canon_in, canon_ans, desc_file, overrides_dir)


@app.delete("/api/problems/{contest_id}/{problem_id}/sample-tests/{sample_name}", response_model=SampleTestCaseItem)
def reset_sample_test(
    contest_id: str,
    problem_id: str,
    sample_name: str,
    session_id: Optional[str] = Depends(get_session_id),
):
    """Resets a single edited sample test case back to the original contest file."""
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir = WORKSPACES_ROOT / contest_id / prob.problem_id
    stem, canon_in, canon_ans, desc_file = _resolve_canonical_sample_entry(problem_dir, sample_name)
    overrides_dir = _get_sample_overrides_dir(contest_id, prob.problem_id, session_id)

    for ext in (".in", ".ans"):
        target = overrides_dir / f"{stem}{ext}"
        if target.exists() and target.is_file():
            target.unlink(missing_ok=True)

    return _build_sample_item(stem, canon_in, canon_ans, desc_file, overrides_dir)


@app.delete("/api/problems/{contest_id}/{problem_id}/sample-tests", response_model=list[SampleTestCaseItem])
def reset_all_sample_tests(
    contest_id: str,
    problem_id: str,
    session_id: Optional[str] = Depends(get_session_id),
):
    """Resets all edited sample test cases for this problem back to original contest files."""
    _, prob = get_contest_and_problem(contest_id, problem_id)
    problem_dir = WORKSPACES_ROOT / contest_id / prob.problem_id
    overrides_dir = _get_sample_overrides_dir(contest_id, prob.problem_id, session_id)

    for f in overrides_dir.iterdir():
        if f.is_file():
            f.unlink(missing_ok=True)

    return [
        _build_sample_item(stem, in_file, ans_file, desc_file, overrides_dir)
        for stem, in_file, ans_file, desc_file in _iter_canonical_samples(problem_dir)
    ]


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

            # Pattern B1: Line 1 is N, Line 2 is N space-separated tokens
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

            # Pattern B2: Line 1 is "N K" (or "N"), Line 2 is a single string of length N (e.g. Medical Certificates)
            hdr_parts = lines[0].split()
            if len(lines) == 2 and hdr_parts and hdr_parts[0].isdigit() and " " not in lines[1]:
                orig_n = int(hdr_parts[0])
                if len(lines[1]) == orig_n:
                    alphabet = sorted(set(lines[1])) or ["A", "P"]
                    new_n = random.randint(max(2, orig_n // 2), max(4, min(30, orig_n * 2)))
                    new_str = "".join(random.choices(alphabet, k=new_n))
                    if len(hdr_parts) == 2 and hdr_parts[1].isdigit():
                        new_k = random.randint(0, min(new_n, max(1, int(hdr_parts[1]) * 2)))
                        return f"{new_n} {new_k}\n{new_str}\n"
                    return f"{new_n}\n{new_str}\n"

            # Pattern B3: Line 1 is "N M", Line 2 has N items, Line 3 has M items (e.g. Exam Halls)
            if len(lines) == 3 and len(hdr_parts) == 2 and hdr_parts[0].isdigit() and hdr_parts[1].isdigit():
                n0, m0 = int(hdr_parts[0]), int(hdr_parts[1])
                t1, t2 = lines[1].split(), lines[2].split()
                if len(t1) == n0 and len(t2) == m0:
                    def _fuzz_arr(arr: list[str], new_len: int) -> list[str]:
                        if all(x.isdigit() or (x.startswith("-") and x[1:].isdigit()) for x in arr):
                            iv = [int(x) for x in arr]
                            lo, hi = min(iv), max(iv)
                            return [str(random.randint(lo, max(lo + 1, hi))) for _ in range(new_len)]
                        return random.choices(arr, k=new_len)

                    new_n = random.randint(1, max(3, min(15, n0 * 2)))
                    new_m = random.randint(1, max(3, min(15, m0 * 2)))
                    return f"{new_n} {new_m}\n" + " ".join(_fuzz_arr(t1, new_n)) + "\n" + " ".join(_fuzz_arr(t2, new_m)) + "\n"

            # Pattern B4: Line 1 is N followed by N grid strings of length N (e.g. Damaged Board Queens)
            if len(lines) >= 3 and lines[0].isdigit():
                n0 = int(lines[0])
                if len(lines) - 1 == n0 and all(" " not in row and len(row) == n0 for row in lines[1:]):
                    grid_chars = list(set("".join(lines[1:]))) or [".", "#"]
                    new_n = random.randint(4, min(9, max(4, n0 + 2)))
                    rows = ["".join(random.choices(grid_chars, k=new_n)) for _ in range(new_n)]
                    return f"{new_n}\n" + "\n".join(rows) + "\n"

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

            # Pattern D: Structure-preserving perturbation (keeps header line 0 fixed so counts/dims remain valid)
            data_ints = [
                int(tok)
                for line in lines[1:]
                for tok in line.split()
                if tok.isdigit() or (tok.startswith("-") and tok[1:].isdigit())
            ]
            hdr_n = int(hdr_parts[0]) if hdr_parts and hdr_parts[0].isdigit() else None
            is_vertex_indexed = bool(
                hdr_n is not None and data_ints and min(data_ints) >= 1 and max(data_ints) <= hdr_n and len(lines) > 2
            )

            fuzzed_lines = [lines[0]]
            for line in lines[1:]:
                parts = line.split()
                fuzzed_parts = []
                for p in parts:
                    if p.isdigit() or (p.startswith("-") and p[1:].isdigit()):
                        val = int(p)
                        if is_vertex_indexed:
                            fuzzed_parts.append(str(random.randint(1, max(1, hdr_n))))
                        else:
                            lo = min(data_ints) if data_ints else val
                            hi = max(data_ints) if data_ints else val + 5
                            if val >= 1:
                                lo = max(1, lo)
                            fuzzed_parts.append(str(random.randint(lo, max(lo + 1, hi))))
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

    raw_user_lang = (payload.lang or "python").lower().strip()
    if raw_user_lang not in LANG_FILENAMES:
        return StressTestResult(
            status="error",
            message=f"Unsupported language '{payload.lang}'. Only Python and Java are supported.",
        )
    user_lang = "python" if raw_user_lang == "py" else raw_user_lang
    user_filename = LANG_FILENAMES[user_lang]
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
            workspace_dir / "Brute.java",
            workspace_dir / "solution_brute.py",
            workspace_dir / "ref.py",
        ]:
            if w_cand.exists() and w_cand.is_file():
                ref_candidates.append(w_cand)

        # Collect all viable reference files under submissions/ (or solutions/ fallback)
        sub_files: list[tuple[bool, int, int, Path]] = []
        for ref_root in (sub_dir, prob_dir / "solutions"):
            if ref_root.exists():
                for f in ref_root.rglob("*"):
                    if f.is_file() and not f.name.startswith("._") and f.suffix.lower() in EXTENSION_TO_LANG:
                        is_accepted = "accepted" in [p.lower() for p in f.parts]
                        f_ext = f.suffix.lower()
                        f_lang = EXTENSION_TO_LANG.get(f_ext, "")
                        # Prioritize matching user language, then Python, then Java
                        lang_score = 0
                        if f_lang == user_lang:
                            lang_score = 3
                        elif f_lang == "python":
                            lang_score = 2
                        elif f_lang == "java":
                            lang_score = 1
                        # Prefer canonical ref.py / solution.py first
                        canonical_score = 1 if f.name.lower() in ("ref.py", "solution.py", "ref.java", "brute.py", "brute.java") else 0
                        sub_files.append((is_accepted, lang_score, canonical_score, f))

        # Sort: accepted first, then highest lang score, then canonical filename
        sub_files.sort(key=lambda x: (1 if x[0] else 0, x[1], x[2]), reverse=True)
        for _, _, _, f in sub_files:
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
        cand_lang = EXTENSION_TO_LANG.get(cand_ext, "")
        if not cand_lang:
            continue
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

    if valid_tested == 0:
        return StressTestResult(
            status="error",
            iteration=0,
            message=f"Reference solution ({ref_path.name}) failed on generated inputs. Add a custom workspace/gen.py generator for this problem.",
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

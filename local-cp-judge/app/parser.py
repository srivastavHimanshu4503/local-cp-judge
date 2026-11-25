from __future__ import annotations

import configparser
import json
import os
import random
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from app.models import ContestMeta, ProblemMeta, TestCaseInfo


def is_ignored_path(p: Path | str) -> bool:
    """
    Check if a path component is __MACOSX, or the filename starts with ._ or is .DS_Store.
    Filters macOS metadata and resource fork artifacts.
    """
    path_obj = Path(p)
    for part in path_obj.parts:
        if part == "__MACOSX":
            return True
        if part.startswith("._") or part == ".DS_Store":
            return True
    if path_obj.name.startswith("._") or path_obj.name == ".DS_Store":
        return True
    return False


def natural_sort_key(s: str) -> list[int | str]:
    """
    Splits string into numeric and non-numeric chunks for natural alphanumeric sorting.
    Ensures '2' sorts before '10', '01-len1' sorts before '02-len1'.
    """
    return [int(chunk) if chunk.isdigit() else chunk.lower() for chunk in re.split(r'(\d+)', s)]


MONTH_ORDER = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

KNOWN_CONTEST_SCHEDULE: dict[str, tuple[int, int, str]] = {
    "10sep-contest": (9, 10, "10Sep Contest"),
    "17sep-contest": (9, 17, "17Sep Contest"),
    "graph-traversal-problems": (9, 24, "24Sep Contest 3 (Graph Traversal)"),
    "graph-contest-4": (10, 5, "5Oct Contest 4 (Graph)"),
    "15oct-contest": (10, 15, "15Oct Contest"),
    "22oct-contest": (10, 22, "22Oct Contest"),
    "makeup-contest": (10, 24, "24Oct Makeup Contest"),
    "29oct-source": (10, 29, "29Oct Source"),
    "contest-25nov": (11, 25, "25Nov Contest"),
}


def contest_sort_key(contest_id: str) -> tuple:
    """
    Orders contests chronologically from earliest date (10 Sep -> 17 Sep -> 24 Sep -> 5 Oct -> ...)
    followed by any undated future contests in natural alphanumeric order.
    """
    known = KNOWN_CONTEST_SCHEDULE.get(contest_id.lower())
    if known:
        month, day, _ = known
        return (0, month, day, natural_sort_key(contest_id))

    match = re.search(
        r'(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
        contest_id.lower(),
    )
    if match:
        day = int(match.group(1))
        month = MONTH_ORDER[match.group(2)]
        return (0, month, day, natural_sort_key(contest_id))
    return (1, 0, 0, natural_sort_key(contest_id))


def clean_quoted_string(val: str) -> str:
    """Strips surrounding whitespace and single/double quotes from INI/YAML values."""
    s = val.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1].strip()
    return s


def unwrap_single_folder(target_dir: Path) -> None:
    """
    If target_dir contains only a single directory holding problem folders,
    moves all contents up one level and removes the wrapper folder.
    Repeats up to 3 levels to handle arbitrarily nested archive roots.
    """
    for _ in range(3):
        visible_children = [item for item in target_dir.iterdir() if not is_ignored_path(item)]
        if len(visible_children) != 1 or not visible_children[0].is_dir():
            break

        wrapper = visible_children[0]
        wrapper_sub_items = [sub for sub in wrapper.iterdir() if not is_ignored_path(sub)]

        # Check if wrapper holds problem folders or contest contents
        has_problem_indicators = any(
            sub.is_dir() and (
                (sub / "domjudge-problem.ini").exists() or
                (sub / "problem.yaml").exists() or
                (sub / "problem.pdf").exists() or
                (sub / "data").exists()
            )
            for sub in wrapper_sub_items
        )

        if not has_problem_indicators and not any(sub.is_dir() for sub in wrapper_sub_items):
            break

        # Move each item up to target_dir
        for sub in wrapper_sub_items:
            dest = target_dir / sub.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(sub), str(dest))

        # Safely remove empty wrapper
        try:
            wrapper.rmdir()
        except OSError:
            shutil.rmtree(wrapper, ignore_errors=True)


def get_problem_test_cases(
    problem_dir: Path,
    suite: str = "all",
    custom_tests_dir: Optional[Path] = None,
    sample_overrides_dir: Optional[Path] = None,
) -> list[TestCaseInfo]:
    """
    Scan and return test cases for the specified problem folder.
    Supports suite='sample', 'secret', 'custom', or 'all'.
    Pairs .in files with corresponding .ans (or .out) and optional .desc files.
    Applies optional session-isolated sample_overrides_dir strictly to canonical sample stems.
    Applies natural alphanumeric sorting and filters out macOS resource forks.
    """
    suites_to_scan: list[str] = []
    if suite in ("sample", "all"):
        suites_to_scan.append("sample")
    if suite in ("custom",):
        suites_to_scan.append("custom")
    if suite in ("secret", "all"):
        suites_to_scan.append("secret")

    results: list[TestCaseInfo] = []

    for current_suite in suites_to_scan:
        if current_suite == "custom":
            suite_dir = custom_tests_dir if custom_tests_dir is not None else (problem_dir / "custom_tests")
            if not suite_dir.exists() or not suite_dir.is_dir():
                continue
        else:
            suite_dir = problem_dir / "data" / current_suite
            if not suite_dir.exists() or not suite_dir.is_dir():
                alt_suite_dir = problem_dir / "tests" / current_suite
                if alt_suite_dir.exists() and alt_suite_dir.is_dir():
                    suite_dir = alt_suite_dir
                else:
                    continue

        in_files = [
            f for f in suite_dir.glob("*.in")
            if f.is_file() and not is_ignored_path(f)
        ]

        # Natural alphanumeric sort: 1, 2, ..., 10
        in_files.sort(key=lambda f: natural_sort_key(f.stem))

        use_sample_overrides = (
            current_suite == "sample"
            and sample_overrides_dir is not None
            and sample_overrides_dir.exists()
            and sample_overrides_dir.is_dir()
        )

        for in_file in in_files:
            stem = in_file.stem

            # Pair with .ans (or .out fallback)
            ans_file = suite_dir / f"{stem}.ans"
            if not ans_file.exists():
                out_alt = suite_dir / f"{stem}.out"
                if out_alt.exists():
                    ans_file = out_alt

            effective_in = in_file
            effective_ans = ans_file
            if use_sample_overrides:
                ov_in = sample_overrides_dir / f"{stem}.in"
                if ov_in.exists() and ov_in.is_file():
                    effective_in = ov_in
                ov_ans = sample_overrides_dir / f"{stem}.ans"
                if ov_ans.exists() and ov_ans.is_file():
                    effective_ans = ov_ans

            # Optional .desc description file
            desc_file = suite_dir / f"{stem}.desc"
            desc_text = ""
            if desc_file.exists() and not is_ignored_path(desc_file):
                try:
                    desc_text = desc_file.read_text(encoding="utf-8", errors="replace").strip()
                except Exception:
                    desc_text = ""

            input_size_bytes = 0
            try:
                input_size_bytes = effective_in.stat().st_size
            except OSError:
                input_size_bytes = 0

            results.append(TestCaseInfo(
                name=f"{current_suite}/{stem}",
                suite=current_suite,
                in_path=str(effective_in.resolve()),
                ans_path=str(effective_ans.resolve()),
                desc_path=str(desc_file.resolve()) if desc_file.exists() else None,
                description=desc_text,
                input_size_bytes=input_size_bytes,
            ))

    return results


def resolve_problem_template(problem_dir: Path, lang: str) -> Optional[Path]:
    """
    Returns a problem-specific starter template under problem_dir/template/
    for 'python' or 'java', or None if no problem-specific template exists.
    Checks standard naming conventions (solution.py/main.py, Main.java/main.java).
    """
    prob_template_dir = problem_dir / "template"
    if not prob_template_dir.exists() or not prob_template_dir.is_dir():
        return None

    lang_key = lang.lower()
    if lang_key in ("python", "py"):
        candidates = ("solution.py", "main.py")
        ext = ".py"
    elif lang_key == "java":
        candidates = ("Main.java", "main.java", "solution.java")
        ext = ".java"
    else:
        return None

    for name in candidates:
        cand = prob_template_dir / name
        if cand.exists() and cand.is_file() and not is_ignored_path(cand):
            return cand

    matches = sorted(
        (
            f for f in prob_template_dir.iterdir()
            if f.is_file() and not is_ignored_path(f) and f.suffix.lower() == ext
        ),
        key=lambda p: natural_sort_key(p.name),
    )
    return matches[0] if matches else None


def scaffold_problem_workspace(
    problem_dir: Path,
    templates_dir: Path,
    problem_name: str,
    time_limit_sec: float,
    memory_limit_mb: int,
    sample_tests: list[TestCaseInfo],
) -> tuple[Path, dict[str, str]]:
    """
    Initializes <problem_dir>/workspace/ and .build/ directory.
    Copies problem-specific starter templates (solution.py, Main.java) when provided
    under template/ without overwriting existing user files; creates empty files otherwise.
    Generates VS Code CPH (.cph/) test configuration files.
    """
    workspace_dir = problem_dir / "workspace"
    build_dir = workspace_dir / ".build"
    cph_dir = workspace_dir / ".cph"

    workspace_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    cph_dir.mkdir(parents=True, exist_ok=True)

    py_target = workspace_dir / "solution.py"
    java_target = workspace_dir / "Main.java"

    py_src = resolve_problem_template(problem_dir, "python")
    java_src = resolve_problem_template(problem_dir, "java")

    if not py_target.exists():
        if py_src and py_src.exists():
            shutil.copy2(py_src, py_target)
        else:
            py_target.write_text("", encoding="utf-8")

    if not java_target.exists():
        if java_src and java_src.exists():
            shutil.copy2(java_src, java_target)
        else:
            java_target.write_text("", encoding="utf-8")

    files_dict = {
        "python": str(py_target.resolve()),
        "java": str(java_target.resolve()),
    }

    # Generate VS Code CPH extension test configurations
    cph_tests: list[dict[str, object]] = []
    for idx, tc in enumerate(sample_tests, start=1):
        in_content = ""
        ans_content = ""
        try:
            in_path_obj = Path(tc.in_path)
            if in_path_obj.exists() and in_path_obj.stat().st_size <= 65536:
                in_content = in_path_obj.read_text(encoding="utf-8", errors="replace")
        except Exception:
            in_content = ""

        try:
            ans_path_obj = Path(tc.ans_path)
            if ans_path_obj.exists() and ans_path_obj.stat().st_size <= 65536:
                ans_content = ans_path_obj.read_text(encoding="utf-8", errors="replace")
        except Exception:
            ans_content = ""

        cph_tests.append({
            "id": idx,
            "input": in_content,
            "output": ans_content,
        })

    for target_file in (py_target, java_target):
        cph_config = {
            "name": problem_name,
            "url": "",
            "tests": cph_tests,
            "interactive": False,
            "memoryLimit": memory_limit_mb,
            "timeLimit": int(time_limit_sec * 1000),
            "group": "Local CP Judge",
            "local": True,
            "srcPath": str(target_file.resolve()),
        }
        cph_prob_file = cph_dir / f".{target_file.name}.prob"
        cph_prob_file.write_text(json.dumps(cph_config, indent=2), encoding="utf-8")

    return workspace_dir, files_dict


def parse_single_problem(problem_dir: Path, templates_dir: Path) -> ProblemMeta:
    """
    Parses problem metadata (domjudge-problem.ini, problem.yaml), catalogs test cases,
    indexes reference submissions, and scaffolds workspace.
    """
    problem_id = problem_dir.name
    short_name = ""
    name = ""
    time_limit_sec = 2.0
    color = "#2c4a7a"
    memory_limit_mb = 1024

    # 1. Parse domjudge-problem.ini (prepend synthetic [problem] section header)
    ini_path = problem_dir / "domjudge-problem.ini"
    if ini_path.exists() and not is_ignored_path(ini_path):
        try:
            content = ini_path.read_text(encoding="utf-8", errors="replace")
            config = configparser.ConfigParser(interpolation=None)
            config.read_string("[problem]\n" + content)
            sec = config["problem"] if "problem" in config else {}

            if "short-name" in sec:
                short_name = clean_quoted_string(sec["short-name"])
            if "name" in sec:
                name = clean_quoted_string(sec["name"])
            if "timelimit" in sec:
                try:
                    time_limit_sec = float(clean_quoted_string(sec["timelimit"]))
                except ValueError:
                    time_limit_sec = 2.0
            if "color" in sec:
                color = clean_quoted_string(sec["color"])
        except Exception:
            pass

    # 2. Parse problem.yaml (extract name and memory limit)
    yaml_path = problem_dir / "problem.yaml"
    if yaml_path.exists() and not is_ignored_path(yaml_path):
        try:
            with open(yaml_path, "r", encoding="utf-8", errors="replace") as f:
                ydata = yaml.safe_load(f)
                if isinstance(ydata, dict):
                    if not name and "name" in ydata:
                        name = clean_quoted_string(str(ydata["name"]))
                    limits = ydata.get("limits", {})
                    if isinstance(limits, dict) and "memory" in limits:
                        try:
                            memory_limit_mb = int(limits["memory"])
                        except (ValueError, TypeError):
                            memory_limit_mb = 1024
        except Exception:
            pass

    # Fallbacks if short_name or name missing
    if not short_name:
        match = re.match(r'^([A-Za-z0-9]+)', problem_id)
        short_name = match.group(1).upper() if match else problem_id[:1].upper()

    if not name:
        cleaned = re.sub(r'^[A-Za-z0-9]+[-_.]\s*', '', problem_id)
        name = cleaned.replace('-', ' ').replace('_', ' ').strip().title() or problem_id

    # 3. Check for problem statement (PDF, HTML) — prefer HTML/Markdown dark rendering by default
    has_pdf = (problem_dir / "problem.pdf").exists() or (problem_dir / "statement" / "problem.pdf").exists()
    has_html = (
        (problem_dir / "statement.html").exists()
        or (problem_dir / "problem.html").exists()
        or (problem_dir / "statement" / "problem.html").exists()
        or (problem_dir / "problem.md").exists()
        or (problem_dir / "statement" / "problem.md").exists()
    )
    has_statement = has_pdf or has_html
    statement_type = "html" if has_html else ("pdf" if has_pdf else "none")

    # 4. Count test cases
    sample_tests = get_problem_test_cases(problem_dir, suite="sample")
    secret_tests = get_problem_test_cases(problem_dir, suite="secret")
    sample_count = len(sample_tests)
    secret_count = len(secret_tests)

    # 5. Catalog reference submissions
    reference_submissions: dict[str, list[str]] = {}
    submissions_dir = problem_dir / "submissions"
    if submissions_dir.exists() and submissions_dir.is_dir():
        for category_dir in submissions_dir.iterdir():
            if category_dir.is_dir() and not is_ignored_path(category_dir):
                sub_files = [
                    f.name for f in category_dir.iterdir()
                    if f.is_file() and not is_ignored_path(f)
                ]
                sub_files.sort(key=lambda s: natural_sort_key(s))
                reference_submissions[category_dir.name] = sub_files

    # 6. Scaffold workspace files and .cph
    workspace_dir, files_dict = scaffold_problem_workspace(
        problem_dir=problem_dir,
        templates_dir=templates_dir,
        problem_name=name,
        time_limit_sec=time_limit_sec,
        memory_limit_mb=memory_limit_mb,
        sample_tests=sample_tests,
    )

    return ProblemMeta(
        problem_id=problem_id,
        short_name=short_name,
        name=name,
        time_limit_sec=time_limit_sec,
        memory_limit_mb=memory_limit_mb,
        color=color,
        has_pdf=has_pdf,
        has_statement=has_statement,
        statement_type=statement_type,
        sample_count=sample_count,
        secret_count=secret_count,
        workspace_dir=str(workspace_dir.resolve()),
        files=files_dict,
        reference_submissions=reference_submissions,
    )


def parse_contest_dir(
    contest_dir: Path,
    templates_dir: Path,
    contest_id: Optional[str] = None,
    contest_title: Optional[str] = None,
) -> ContestMeta:
    """
    Parses an already extracted or existing contest directory, indexing all problems,
    scaffolding workspaces, and saving contest_meta.json.
    """
    if not contest_id:
        contest_id = contest_dir.name

    # Discover problem directories
    problem_dirs: list[Path] = []
    for item in contest_dir.iterdir():
        if not item.is_dir() or is_ignored_path(item):
            continue
        # Identified by domjudge-problem.ini, problem.yaml, problem.pdf, or data/
        if (
            (item / "domjudge-problem.ini").exists() or
            (item / "problem.yaml").exists() or
            (item / "problem.pdf").exists() or
            (item / "data").exists()
        ):
            problem_dirs.append(item)

    problems: list[ProblemMeta] = []
    for prob_dir in problem_dirs:
        problem_meta = parse_single_problem(prob_dir, templates_dir)
        problems.append(problem_meta)

    # Sort problems by short_name (A, B, C, D)
    problems.sort(key=lambda p: natural_sort_key(p.short_name))

    known = KNOWN_CONTEST_SCHEDULE.get(contest_id.lower())
    if contest_title:
        clean_title = contest_title
    elif known:
        clean_title = known[2]
    elif contest_id == MOCK_QUIZ_CONTEST_ID:
        clean_title = "Mock Quiz (Mixed)"
    else:
        clean_title = contest_id.replace('-', ' ').replace('_', ' ').title()
    contest = ContestMeta(
        contest_id=contest_id,
        title=clean_title,
        created_at=datetime.now(timezone.utc).isoformat(),
        problems=problems,
    )
    _attach_mock_sources(contest_dir, contest)

    # Persist contest_meta.json in contest root
    meta_path = contest_dir / "contest_meta.json"
    meta_path.write_text(contest.model_dump_json(indent=2), encoding="utf-8")

    return contest


def extract_and_parse_contest(
    zip_path: Path,
    workspaces_root: Path,
    templates_dir: Path,
) -> ContestMeta:
    """
    Extracts a DOMjudge / ICPC contest .zip archive, filters out __MACOSX and ._* files,
    flattens single wrapper directories, parses all problem metadata, scaffolds workspaces,
    and returns a ContestMeta object.
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"Archive file not found: {zip_path}")

    contest_id = zip_path.stem
    contest_dir = workspaces_root / contest_id
    workspaces_root.mkdir(parents=True, exist_ok=True)
    contest_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            # Check normalized path components
            norm_name = member.filename.replace("\\", "/")
            parts = [p for p in norm_name.split("/") if p]
            if any(p == "__MACOSX" for p in parts):
                continue
            if any(p.startswith("._") or p == ".DS_Store" for p in parts):
                continue

            zf.extract(member, contest_dir)

    # Automatically unwrap single top-level folder if present
    unwrap_single_folder(contest_dir)

    # 1. Unpack nested zips if present (e.g. graph-contest-4)
    for nz in list(contest_dir.glob("*.zip")):
        prob_name = nz.stem
        target_prob_dir = contest_dir / prob_name
        target_prob_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(nz, "r") as sub_zf:
                for m in sub_zf.infolist():
                    parts = m.filename.replace("\\", "/").split("/")
                    if any(p == "__MACOSX" for p in parts) or any(p.startswith("._") for p in parts):
                        continue
                    sub_zf.extract(m, target_prob_dir)
            nz.unlink(missing_ok=True)
        except Exception:
            pass

    # 2. Copy jury solutions if jury-tools exists
    jury_tools = contest_dir / "jury-tools"
    if jury_tools.exists():
        for prob_dir in contest_dir.iterdir():
            if not prob_dir.is_dir() or prob_dir.name in ("jury-tools", "statements", "tools", "__MACOSX"):
                continue
            letter = prob_dir.name[0].upper()
            acc_dir = prob_dir / "submissions" / "accepted"
            acc_dir.mkdir(parents=True, exist_ok=True)
            for sol_f in (jury_tools / "sol").glob(f"{letter}.*"):
                shutil.copy2(sol_f, acc_dir / sol_f.name)
            wa_dir = prob_dir / "submissions" / "wrong_answer"
            wa_dir.mkdir(parents=True, exist_ok=True)
            for wa_f in (jury_tools / "wrong").glob(f"{letter}_*.*"):
                shutil.copy2(wa_f, wa_dir / wa_f.name)

    # 3. Normalize tests/ -> data/ if tests/ exists
    for prob_dir in contest_dir.iterdir():
        if not prob_dir.is_dir():
            continue
        tests_dir = prob_dir / "tests"
        data_dir = prob_dir / "data"
        if tests_dir.exists() and not data_dir.exists():
            shutil.copytree(tests_dir, data_dir)

    # 4. Materialize test cases using generator/gen.py if tests are missing
    import subprocess
    import sys
    from app.runner import ensure_windows_python_shims

    for prob_dir in contest_dir.iterdir():
        if not prob_dir.is_dir():
            continue
        gen_py = prob_dir / "generator" / "gen.py"
        data_sample = prob_dir / "data" / "sample"
        if gen_py.exists() and (not data_sample.exists() or len(list(data_sample.glob("*.in"))) == 0):
            try:
                subprocess.run([sys.executable, str(gen_py), str(prob_dir)], capture_output=True, timeout=60)
                subs = list((prob_dir / "submissions" / "accepted").glob("*.py"))
                if not subs:
                    subs = list((prob_dir / "solutions" / "accepted").glob("*.py"))
                if subs:
                    # Prefer ref.py (or non-recursive reference if present)
                    ref = next(
                        (s for s in subs if s.name == "ref.py"),
                        next((s for s in subs if "parent_walk" in s.name or "sort" in s.name), subs[0]),
                    )
                    shim_dir = prob_dir / "workspace" / ".build"
                    shim_dir.mkdir(parents=True, exist_ok=True)
                    ensure_windows_python_shims(shim_dir)
                    env = os.environ.copy()
                    existing_pp = env.get("PYTHONPATH", "")
                    env["PYTHONPATH"] = f"{shim_dir.resolve()}{os.pathsep}{existing_pp}" if existing_pp else str(shim_dir.resolve())
                    for suite in ("sample", "secret"):
                        s_dir = prob_dir / "data" / suite
                        if s_dir.exists():
                            for inf in s_dir.glob("*.in"):
                                ans_f = inf.with_suffix(".ans")
                                if not ans_f.exists():
                                    with open(inf, "rb") as fin, open(ans_f, "wb") as fout:
                                        subprocess.run(
                                            [sys.executable, str(ref)],
                                            stdin=fin,
                                            stdout=fout,
                                            env=env,
                                            timeout=30,
                                        )
            except Exception:
                pass

    # 5. Normalize statements to problem root
    for prob_dir in contest_dir.iterdir():
        if not prob_dir.is_dir() or prob_dir.name in ("tools", "statements", "jury-tools", "__MACOSX"):
            continue
        if not (prob_dir / "problem.pdf").exists() and not (prob_dir / "statement.html").exists():
            if (prob_dir / "statement" / "problem.pdf").exists():
                shutil.copy2(prob_dir / "statement" / "problem.pdf", prob_dir / "problem.pdf")
            elif (prob_dir / "statement" / "problem.html").exists():
                shutil.copy2(prob_dir / "statement" / "problem.html", prob_dir / "statement.html")
            elif (prob_dir / "problem.html").exists():
                shutil.copy2(prob_dir / "problem.html", prob_dir / "statement.html")

            statements_dir = contest_dir / "statements"
            if statements_dir.exists():
                for f in statements_dir.iterdir():
                    if prob_dir.name in f.name:
                        if f.suffix.lower() == ".pdf" and not (prob_dir / "problem.pdf").exists():
                            shutil.copy2(f, prob_dir / "problem.pdf")
                        elif f.suffix.lower() == ".html" and not (prob_dir / "statement.html").exists():
                            shutil.copy2(f, prob_dir / "statement.html")

    # Parse and structure the contest
    return parse_contest_dir(contest_dir, templates_dir, contest_id=contest_id)


def _attach_mock_sources(contest_dir: Path, meta: ContestMeta) -> ContestMeta:
    """Enriches mockup contest problems with their source contest metadata from mock_quiz_sources.json."""
    sources_path = contest_dir / "mock_quiz_sources.json"
    if not sources_path.exists() or not sources_path.is_file():
        return meta
    try:
        raw = json.loads(sources_path.read_text(encoding="utf-8", errors="replace"))
        records = raw.get("sources", []) if isinstance(raw, dict) else []
    except Exception:
        return meta

    by_slot = {
        str(item.get("slot", "")).upper(): item
        for item in records
        if isinstance(item, dict) and item.get("slot")
    }
    by_prob = {
        str(item.get("source_problem", "")): item
        for item in records
        if isinstance(item, dict) and item.get("source_problem")
    }
    for p in meta.problems:
        slot = (p.short_name or p.problem_id[:1]).upper()
        rec = by_prob.get(p.problem_id) or by_slot.get(slot)
        if rec:
            p.source_contest_id = rec.get("source_contest") or None
            p.source_contest_title = rec.get("source_contest_title") or None
            p.source_problem_id = rec.get("source_problem") or None
    return meta


def _meta_needs_refresh(contest_dir: Path, meta: ContestMeta) -> bool:
    """Detects stale contest_meta.json missing statement flags, accepted solutions, mock origin, or removed cpp entries."""
    known = KNOWN_CONTEST_SCHEDULE.get(meta.contest_id.lower())
    if known and meta.title != known[2]:
        return True
    has_mock_sources = (contest_dir / "mock_quiz_sources.json").exists()
    for p in meta.problems:
        if "cpp" in p.files:
            return True
        if has_mock_sources and not p.source_contest_id:
            return True
        prob_dir = contest_dir / p.problem_id
        acc_dir = prob_dir / "submissions" / "accepted"
        actual_acc = len([f for f in acc_dir.iterdir() if f.is_file() and not is_ignored_path(f)]) if acc_dir.exists() else 0
        cached_acc = len(p.reference_submissions.get("accepted", []))
        if actual_acc != cached_acc:
            return True
        has_pdf = (prob_dir / "problem.pdf").exists() or (prob_dir / "statement" / "problem.pdf").exists()
        has_html = (
            (prob_dir / "statement.html").exists()
            or (prob_dir / "problem.html").exists()
            or (prob_dir / "statement" / "problem.html").exists()
            or (prob_dir / "problem.md").exists()
            or (prob_dir / "statement" / "problem.md").exists()
        )
        if (has_pdf or has_html) and not p.has_statement:
            return True
        if has_pdf != p.has_pdf or (has_html and p.statement_type == "pdf"):
            return True
    return False


MOCK_QUIZ_CONTEST_ID = "mock-quiz"
MOCK_QUIZ_EXCLUDED_DIRS = {"workspace", ".build", ".cph", "custom_tests", "sample_overrides", "__MACOSX"}


def _mock_copy_ignore(_src_dir: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name in MOCK_QUIZ_EXCLUDED_DIRS or name.startswith("._") or name == ".DS_Store":
            ignored.add(name)
    return ignored


def _select_mock_problems(
    candidates_by_slot: dict[str, list[tuple[ContestMeta, ProblemMeta]]],
    prev_pairs: set[tuple[str, str]],
    rng: random.Random,
) -> list[tuple[str, ContestMeta, ProblemMeta]]:
    slots = ["A", "B", "C", "D"]
    ordered: dict[str, list[tuple[ContestMeta, ProblemMeta]]] = {}
    for slot in slots:
        pool = list(candidates_by_slot.get(slot, []))
        rng.shuffle(pool)
        # Prefer problems that were not in the previous mock quiz
        pool.sort(key=lambda pair: 1 if (pair[0].contest_id, pair[1].problem_id) in prev_pairs else 0)
        ordered[slot] = pool

    # Backtracking search enforcing distinct source contests across A, B, C, D
    picked: list[tuple[str, ContestMeta, ProblemMeta]] = []
    used_contests: set[str] = set()

    def backtrack(idx: int) -> bool:
        if idx == len(slots):
            return True
        slot = slots[idx]
        for contest_meta, prob_meta in ordered[slot]:
            if contest_meta.contest_id in used_contests:
                continue
            used_contests.add(contest_meta.contest_id)
            picked.append((slot, contest_meta, prob_meta))
            if backtrack(idx + 1):
                return True
            picked.pop()
            used_contests.remove(contest_meta.contest_id)
        return False

    if backtrack(0):
        return picked

    # Fallback if fewer than 4 distinct contests exist
    fallback: list[tuple[str, ContestMeta, ProblemMeta]] = []
    for slot in slots:
        pool = ordered[slot]
        if not pool:
            continue
        unused = next(((c, p) for c, p in pool if c.contest_id not in {x[1].contest_id for x in fallback}), pool[0])
        fallback.append((slot, unused[0], unused[1]))
    return fallback


def generate_mock_quiz(
    workspaces_root: Path,
    templates_dir: Path,
    contest_id: str = MOCK_QUIZ_CONTEST_ID,
    seed: Optional[int] = None,
) -> ContestMeta:
    """
    Creates a 4-question Mockup Quiz contest (slots A, B, C, D) by picking one problem
    per difficulty slot from 4 distinct contests across all available contests.
    """
    all_contests = list_contests(workspaces_root)
    source_contests = [c for c in all_contests if not c.contest_id.startswith("mock-quiz")]
    if not source_contests:
        raise ValueError("No source contests available to build a mock quiz.")

    candidates_by_slot: dict[str, list[tuple[ContestMeta, ProblemMeta]]] = {"A": [], "B": [], "C": [], "D": []}
    for c in source_contests:
        for p in c.problems:
            slot = (p.short_name or p.problem_id[:1]).upper()
            if slot in candidates_by_slot:
                candidates_by_slot[slot].append((c, p))

    target_dir = workspaces_root / contest_id
    prev_pairs: set[tuple[str, str]] = set()
    sources_meta_path = target_dir / "mock_quiz_sources.json"
    if sources_meta_path.exists():
        try:
            old_data = json.loads(sources_meta_path.read_text(encoding="utf-8", errors="replace"))
            for item in old_data.get("sources", []):
                prev_pairs.add((item.get("source_contest", ""), item.get("source_problem", "")))
        except Exception:
            pass

    rng = random.Random(seed) if seed is not None else random.Random()
    selected = _select_mock_problems(candidates_by_slot, prev_pairs, rng)
    if len(selected) < 4:
        raise ValueError("Not enough A/B/C/D problems across available contests to build a 4-question mock quiz.")

    staging_dir = workspaces_root / f".staging_{contest_id}"
    if staging_dir.exists():
        shutil.rmtree(staging_dir, ignore_errors=True)
    staging_dir.mkdir(parents=True, exist_ok=True)

    source_records: list[dict[str, str]] = []
    for slot, src_contest, src_prob in selected:
        src_prob_dir = workspaces_root / src_contest.contest_id / src_prob.problem_id
        dest_prob_dir = staging_dir / src_prob.problem_id
        # Ensure unique folder name if a fallback collision ever happened
        if dest_prob_dir.exists():
            dest_prob_dir = staging_dir / f"{slot}-{src_contest.contest_id}-{src_prob.problem_id}"

        shutil.copytree(src_prob_dir, dest_prob_dir, ignore=_mock_copy_ignore)
        source_records.append({
            "slot": slot,
            "source_contest": src_contest.contest_id,
            "source_contest_title": src_contest.title,
            "source_problem": src_prob.problem_id,
            "name": src_prob.name,
        })

    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
    shutil.move(str(staging_dir), str(target_dir))

    (target_dir / "mock_quiz_sources.json").write_text(
        json.dumps({"sources": source_records}, indent=2),
        encoding="utf-8",
    )

    return parse_contest_dir(
        target_dir,
        templates_dir,
        contest_id=contest_id,
        contest_title="Mock Quiz (Mixed)",
    )


def list_contests(workspaces_root: Path) -> list[ContestMeta]:
    """
    Scans workspaces_root for imported contests containing contest_meta.json.
    Auto-refreshes stale metadata if statement detection or language maps changed.
    Returns a list of ContestMeta objects.
    """
    if not workspaces_root.exists() or not workspaces_root.is_dir():
        return []

    contests: list[ContestMeta] = []
    templates_dir = workspaces_root.parent / "templates"
    for item in workspaces_root.iterdir():
        if item.is_dir() and not is_ignored_path(item) and not item.name.startswith("."):
            meta_path = item / "contest_meta.json"
            if meta_path.exists() and meta_path.is_file():
                try:
                    content = meta_path.read_text(encoding="utf-8", errors="replace")
                    meta = ContestMeta.model_validate_json(content)
                    if _meta_needs_refresh(item, meta):
                        custom_title = meta.title if (item / "mock_quiz_sources.json").exists() else None
                        meta = parse_contest_dir(item, templates_dir, contest_id=meta.contest_id, contest_title=custom_title)
                    contests.append(meta)
                except Exception:
                    pass

    contests.sort(key=lambda c: contest_sort_key(c.contest_id))
    return contests


def load_contest(contest_id: str, workspaces_root: Path) -> ContestMeta:
    """
    Loads and returns ContestMeta for a given contest_id from workspaces_root.
    Auto-refreshes stale metadata if statement detection or language maps changed.
    Raises FileNotFoundError if contest_meta.json does not exist.
    """
    contest_dir = workspaces_root / contest_id
    meta_path = contest_dir / "contest_meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Contest metadata not found for contest '{contest_id}' at {meta_path}")

    content = meta_path.read_text(encoding="utf-8", errors="replace")
    meta = ContestMeta.model_validate_json(content)
    if _meta_needs_refresh(contest_dir, meta):
        custom_title = meta.title if (contest_dir / "mock_quiz_sources.json").exists() else None
        meta = parse_contest_dir(contest_dir, workspaces_root.parent / "templates", contest_id=meta.contest_id, contest_title=custom_title)
    return meta

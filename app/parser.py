from __future__ import annotations

import configparser
import json
import os
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


def get_problem_test_cases(problem_dir: Path, suite: str = "all") -> list[TestCaseInfo]:
    """
    Scan and return test cases for the specified problem folder.
    Supports suite='sample', 'secret', or 'all'.
    Pairs .in files with corresponding .ans (or .out) and optional .desc files.
    Applies natural alphanumeric sorting and filters out macOS resource forks.
    """
    suites_to_scan: list[str] = []
    if suite in ("sample", "all"):
        suites_to_scan.append("sample")
    if suite in ("secret", "all"):
        suites_to_scan.append("secret")

    results: list[TestCaseInfo] = []

    for current_suite in suites_to_scan:
        suite_dir = problem_dir / "data" / current_suite
        if not suite_dir.exists() or not suite_dir.is_dir():
            continue

        in_files = [
            f for f in suite_dir.glob("*.in")
            if f.is_file() and not is_ignored_path(f)
        ]

        # Natural alphanumeric sort: 1, 2, ..., 10
        in_files.sort(key=lambda f: natural_sort_key(f.stem))

        for in_file in in_files:
            stem = in_file.stem

            # Pair with .ans (or .out fallback)
            ans_file = suite_dir / f"{stem}.ans"
            if not ans_file.exists():
                out_alt = suite_dir / f"{stem}.out"
                if out_alt.exists():
                    ans_file = out_alt

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
                input_size_bytes = in_file.stat().st_size
            except OSError:
                input_size_bytes = 0

            results.append(TestCaseInfo(
                name=f"{current_suite}/{stem}",
                suite=current_suite,
                in_path=str(in_file.resolve()),
                ans_path=str(ans_file.resolve()),
                desc_path=str(desc_file.resolve()) if desc_file.exists() else None,
                description=desc_text,
                input_size_bytes=input_size_bytes,
            ))

    return results


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
    Copies starter templates (solution.cpp, solution.py, Main.java) without
    overwriting existing user files.
    Generates VS Code CPH (.cph/) test configuration files.
    """
    workspace_dir = problem_dir / "workspace"
    build_dir = workspace_dir / ".build"
    cph_dir = workspace_dir / ".cph"

    workspace_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    cph_dir.mkdir(parents=True, exist_ok=True)

    cpp_target = workspace_dir / "solution.cpp"
    py_target = workspace_dir / "solution.py"
    java_target = workspace_dir / "Main.java"

    cpp_src = templates_dir / "cpp_template.cpp"
    py_src = templates_dir / "python_template.py"
    java_src = templates_dir / "java_template.java"

    if not cpp_target.exists() and cpp_src.exists():
        shutil.copy2(cpp_src, cpp_target)
    if not py_target.exists() and py_src.exists():
        shutil.copy2(py_src, py_target)
    if not java_target.exists() and java_src.exists():
        shutil.copy2(java_src, java_target)

    files_dict = {
        "cpp": str(cpp_target.resolve()),
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

    for target_file in (cpp_target, py_target, java_target):
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

    # 3. Check for problem statement PDF
    has_pdf = (problem_dir / "problem.pdf").exists()

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

    clean_title = contest_id.replace('-', ' ').replace('_', ' ').title()
    contest = ContestMeta(
        contest_id=contest_id,
        title=clean_title,
        created_at=datetime.now(timezone.utc).isoformat(),
        problems=problems,
    )

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

    # Parse and structure the contest
    return parse_contest_dir(contest_dir, templates_dir, contest_id=contest_id)


def list_contests(workspaces_root: Path) -> list[ContestMeta]:
    """
    Scans workspaces_root for imported contests containing contest_meta.json.
    Returns a list of ContestMeta objects.
    """
    if not workspaces_root.exists() or not workspaces_root.is_dir():
        return []

    contests: list[ContestMeta] = []
    for item in workspaces_root.iterdir():
        if item.is_dir() and not is_ignored_path(item):
            meta_path = item / "contest_meta.json"
            if meta_path.exists() and meta_path.is_file():
                try:
                    content = meta_path.read_text(encoding="utf-8", errors="replace")
                    contests.append(ContestMeta.model_validate_json(content))
                except Exception:
                    pass

    contests.sort(key=lambda c: natural_sort_key(c.contest_id))
    return contests


def load_contest(contest_id: str, workspaces_root: Path) -> ContestMeta:
    """
    Loads and returns ContestMeta for a given contest_id from workspaces_root.
    Raises FileNotFoundError if contest_meta.json does not exist.
    """
    meta_path = workspaces_root / contest_id / "contest_meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Contest metadata not found for contest '{contest_id}' at {meta_path}")

    content = meta_path.read_text(encoding="utf-8", errors="replace")
    return ContestMeta.model_validate_json(content)

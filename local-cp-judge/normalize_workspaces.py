import shutil
from pathlib import Path

from app.parser import parse_contest_dir, resolve_problem_template

workspaces_root = Path(r"E:\Personal projects\DSA Visualizer\local-cp-judge\workspaces")
templates_root = Path(r"E:\Personal projects\DSA Visualizer\local-cp-judge\templates")

# remove duplicate 15oct-contest/15oct-contest if present
dup = workspaces_root / "15oct-contest" / "15oct-contest"
if dup.exists():
    shutil.rmtree(dup, ignore_errors=True)

for cdir in workspaces_root.iterdir():
    if not cdir.is_dir():
        continue
    for pdir in cdir.iterdir():
        if not pdir.is_dir() or pdir.name in ("tools", "statements", "jury-tools", "__MACOSX", ".git", "contest-package"):
            continue

        # 1. Statement normalization: Ensure problem.pdf or statement.html exists at problem root
        if not (pdir / "problem.pdf").exists() and not (pdir / "statement.html").exists():
            if (pdir / "statement" / "problem.pdf").exists():
                shutil.copy2(pdir / "statement" / "problem.pdf", pdir / "problem.pdf")
            elif (pdir / "statement" / "problem.html").exists():
                shutil.copy2(pdir / "statement" / "problem.html", pdir / "statement.html")
            elif (pdir / "problem.html").exists():
                shutil.copy2(pdir / "problem.html", pdir / "statement.html")

            statements_dir = cdir / "statements"
            if statements_dir.exists():
                for f in statements_dir.iterdir():
                    if pdir.name in f.name:
                        if f.suffix.lower() == ".pdf" and not (pdir / "problem.pdf").exists():
                            shutil.copy2(f, pdir / "problem.pdf")
                        elif f.suffix.lower() == ".html" and not (pdir / "statement.html").exists():
                            shutil.copy2(f, pdir / "statement.html")

        # 2. Workspace normalization: remove legacy cpp file; copy problem-specific templates or empty files
        ws_dir = pdir / "workspace"
        ws_dir.mkdir(parents=True, exist_ok=True)
        (ws_dir / ".build").mkdir(parents=True, exist_ok=True)

        cpp_f = ws_dir / "solution.cpp"
        if cpp_f.exists():
            cpp_f.unlink()

        for lang_key, fname in (("python", "solution.py"), ("java", "Main.java")):
            target_f = ws_dir / fname
            if not target_f.exists():
                tmpl_file = resolve_problem_template(pdir, lang_key)
                if tmpl_file and tmpl_file.exists():
                    shutil.copy2(tmpl_file, target_f)
                else:
                    target_f.write_text("", encoding="utf-8")

    parse_contest_dir(cdir, templates_root, contest_id=cdir.name)

print("Normalized all problem directories!")

import shutil
from pathlib import Path

workspaces_root = Path(r"E:\Personal projects\DSA Visualizer\local-cp-judge\workspaces")

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

        # 2. Workspace normalization: Ensure workspace directory and files exist
        ws_dir = pdir / "workspace"
        ws_dir.mkdir(parents=True, exist_ok=True)
        (ws_dir / ".build").mkdir(parents=True, exist_ok=True)

        cpp_f = ws_dir / "solution.cpp"
        py_f = ws_dir / "solution.py"
        java_f = ws_dir / "Main.java"

        if not cpp_f.exists():
            cpp_f.write_text("#include <iostream>\nusing namespace std;\n\nint main() {\n    return 0;\n}\n", encoding="utf-8")
        if not py_f.exists():
            tmpl_py = pdir / "template" / "main.py"
            if tmpl_py.exists():
                shutil.copy2(tmpl_py, py_f)
            else:
                py_f.write_text("import sys\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n", encoding="utf-8")
        if not java_f.exists():
            tmpl_java = pdir / "template" / "Main.java"
            if tmpl_java.exists():
                shutil.copy2(tmpl_java, java_f)
            else:
                java_f.write_text("import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n    }\n}\n", encoding="utf-8")

print("Normalized all problem directories!")

"""Extract and materialize all root contest *.zip archives into local-cp-judge/workspaces/."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_ROOT = ROOT / "local-cp-judge"
sys.path.insert(0, str(APP_ROOT))

from app.parser import extract_and_parse_contest


def main() -> None:
    workspaces_root = APP_ROOT / "workspaces"
    templates_dir = APP_ROOT / "templates"
    workspaces_root.mkdir(parents=True, exist_ok=True)

    zips = sorted(ROOT.glob("*.zip"))
    if not zips:
        print("No contest .zip archives found in repository root.")
        return

    for zp in zips:
        contest_dir = workspaces_root / zp.stem
        if (contest_dir / "contest_meta.json").exists():
            print(f"[SKIP] {zp.stem} already extracted.")
            continue
        print(f"[EXTRACT] {zp.name} -> {contest_dir} ...")
        meta = extract_and_parse_contest(zp, workspaces_root, templates_dir)
        print(f"  -> Ready: {meta.title} ({len(meta.problems)} problems)")


if __name__ == "__main__":
    main()

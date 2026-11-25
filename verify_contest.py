"""
verify_contest.py — Root forwarder and verification runner.
Delegates to local-cp-judge/verify_contest.py.
"""
import sys
from pathlib import Path

target = Path(__file__).resolve().parent / "local-cp-judge" / "verify_contest.py"
if target.exists():
    import subprocess
    sys.exit(subprocess.call([sys.executable, str(target)] + sys.argv[1:]))
else:
    print("local-cp-judge/verify_contest.py not found.")
    sys.exit(1)

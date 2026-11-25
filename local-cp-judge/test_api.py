from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.main import USER_WORKSPACES_ROOT  # noqa: E402


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _get(base_url: str, path: str, headers: dict[str, str] | None = None) -> tuple[int, str, bytes]:
    req = urllib.request.Request(base_url + path, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, (resp.headers.get("Content-Type") or ""), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, (exc.headers.get("Content-Type") or ""), exc.read()


def main() -> int:
    sid = "verify-test-api-session"
    headers = {"X-Session-Id": sid}
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=str(APP_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        for _ in range(30):
            try:
                sc, _, _ = _get(base_url, "/api/system/status")
                if sc == 200:
                    break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("Uvicorn test server failed to start.")

        # 1. Root page & system status
        sc, _, home_bytes = _get(base_url, "/")
        home_text = home_bytes.decode("utf-8", errors="replace")
        assert sc == 200
        assert 'id="lang-select"' in home_text
        assert 'id="view-samples"' in home_text
        assert 'id="btn-toggle-pdf"' in home_text

        sc, _, sys_bytes = _get(base_url, "/api/system/status")
        assert sc == 200
        print("System status:", sc, json.loads(sys_bytes.decode("utf-8"))["os_name"])

        # 2. List all contests (chronological order)
        sc, _, contests_bytes = _get(base_url, "/api/contests")
        assert sc == 200
        contests = json.loads(contests_bytes.decode("utf-8"))
        print("Contests count:", len(contests))
        assert len(contests) >= 9

        pdf_contests = {"15oct-contest", "22oct-contest", "makeup-contest", "29oct-source"}
        total_problems = 0
        total_samples = 0
        total_secrets = 0

        for c in contests:
            cid = c["contest_id"]
            probs = c["problems"]
            print(f"\n--- Contest: {cid} ({len(probs)} problems) ---")
            for p in probs:
                pid = p["problem_id"]
                total_problems += 1
                total_samples += p["sample_count"]
                total_secrets += p["secret_count"]
                assert p["statement_type"] == "html", f"{cid}/{pid} expected html statement"

                st_sc, content_type, st_bytes = _get(base_url, f"/api/problems/{cid}/{pid}/statement")
                st_text = st_bytes.decode("utf-8", errors="replace")
                assert st_sc == 200
                assert "obsidian-markdown-v2" in st_text

                if cid in pdf_contests:
                    assert p["has_pdf"] is True
                    pdf_sc, _, pdf_bytes = _get(base_url, f"/api/problems/{cid}/{pid}/statement?format=pdf")
                    assert pdf_sc == 200
                    assert pdf_bytes.startswith(b"%PDF")

                py_sc, _, _ = _get(base_url, f"/api/problems/{cid}/{pid}/code?lang=python", headers=headers)
                java_sc, _, _ = _get(base_url, f"/api/problems/{cid}/{pid}/code?lang=java", headers=headers)
                assert py_sc == 200 and java_sc == 200

                smp_sc, _, smp_bytes = _get(base_url, f"/api/problems/{cid}/{pid}/sample-tests", headers=headers)
                assert smp_sc == 200
                assert len(json.loads(smp_bytes.decode("utf-8"))) == p["sample_count"]

                print(
                    f"  [{p['short_name']}] {p['name']}"
                    f" | Samples: {p['sample_count']} | Secrets: {p['secret_count']}"
                    f" | Statement: {st_sc} ({content_type[:16]})"
                    f" | Code: {py_sc}/{java_sc}"
                )

        print(
            f"\nVERIFICATION TOTALS: {len(contests)} Contests, {total_problems} Problems, "
            f"{total_samples} Samples, {total_secrets} Secrets."
        )
        print("ALL ENDPOINTS RETURNED 200 OK CLEANLY!")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        tmp_dir = USER_WORKSPACES_ROOT / sid
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

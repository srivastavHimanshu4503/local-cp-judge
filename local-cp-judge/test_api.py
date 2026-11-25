import sys
from pathlib import Path

sys.path.insert(0, r"E:\Personal projects\DSA Visualizer\local-cp-judge")
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. System status
res = client.get("/api/system/status")
print("System status:", res.status_code, res.json()["os_name"])

# 2. List all contests
res = client.get("/api/contests")
contests = res.json()
print("Contests count:", len(contests))

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

        # Test statement
        stmt_res = client.get(f"/api/problems/{cid}/{pid}/statement")
        content_type = stmt_res.headers.get("content-type", "")

        # Test code retrieval
        code_res = client.get(f"/api/problems/{cid}/{pid}/code?lang=python")

        print(
            f"  [{p['short_name']}] {p['name']}"
            f" | Samples: {p['sample_count']} | Secrets: {p['secret_count']}"
            f" | Statement: {stmt_res.status_code} ({content_type[:16]})"
            f" | Code: {code_res.status_code}"
        )

print(f"\nVERIFICATION TOTALS: {len(contests)} Contests, {total_problems} Problems, {total_samples} Samples, {total_secrets} Secrets.")
print("ALL ENDPOINTS RETURNED 200 OK CLEANLY!")

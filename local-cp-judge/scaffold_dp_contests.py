from __future__ import annotations

import sys
from pathlib import Path
from app.parser import parse_contest_dir

base_dir = Path(__file__).resolve().parent
ws = base_dir / "workspaces"
tpl = base_dir / "templates"

def setup_10sep():
    c_dir = ws / "10sep-contest"
    c_dir.mkdir(parents=True, exist_ok=True)

    # 1A: Rabbit / Frog 1
    p1a = c_dir / "A-rabbit-frog-1"
    p1a.mkdir(parents=True, exist_ok=True)
    (p1a / "domjudge-problem.ini").write_text('short-name = A\nname = "Rabbit / Frog 1"\ntimelimit = 2\ncolor = "#4C51BF"\n', encoding="utf-8")
    (p1a / "problem.yaml").write_text("name: Rabbit / Frog 1\nlimits:\n  memory: 1024\n", encoding="utf-8")
    (p1a / "statement.html").write_text("""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:1.5rem;background:#161720;color:#e2e8f0;line-height:1.6;">
<h2>Problem A — Rabbit / Frog 1 (AtCoder dp_a)</h2>
<p><strong>Time limit:</strong> 2.0s &bull; <strong>Memory limit:</strong> 1024 MB</p>
<p>There are $N$ stones, numbered $1, 2, \\dots, N$. For each $i$, Stone $i$ has height $h_i$. A frog starts on Stone 1 and wants to reach Stone $N$.</p>
<p>From Stone $i$, the frog can jump to Stone $i+1$ or Stone $i+2$, incurring cost $|h_i - h_j|$.</p>
<p>Find the minimum total cost to reach Stone $N$.</p>
<div style="background:#12131a;border:1px solid #242634;border-radius:6px;padding:10px 14px;margin-top:14px;">
  <strong>Key Idea (1D DP):</strong> <code>dp[i] = min(dp[i-1] + |h[i] - h[i-1]|, dp[i-2] + |h[i] - h[i-2]|)</code>
</div>
</body></html>""", encoding="utf-8")
    s = p1a / "data" / "sample"
    s.mkdir(parents=True, exist_ok=True)
    (s / "1.in").write_text("4\n10 30 40 20\n", encoding="utf-8")
    (s / "1.ans").write_text("30\n", encoding="utf-8")
    (s / "2.in").write_text("2\n10 10\n", encoding="utf-8")
    (s / "2.ans").write_text("0\n", encoding="utf-8")
    (s / "3.in").write_text("6\n30 10 60 10 60 50\n", encoding="utf-8")
    (s / "3.ans").write_text("40\n", encoding="utf-8")
    acc = p1a / "submissions" / "accepted"
    acc.mkdir(parents=True, exist_ok=True)
    (acc / "solution.py").write_text("""n = int(input())
h = list(map(int, input().split()))
dp = [0] * n
for i in range(1, n):
    dp[i] = dp[i-1] + abs(h[i] - h[i-1])
    if i > 1:
        dp[i] = min(dp[i], dp[i-2] + abs(h[i] - h[i-2]))
print(dp[-1])
""", encoding="utf-8")

    # 1B: Is Subsequence
    p1b = c_dir / "B-is-subsequence"
    p1b.mkdir(parents=True, exist_ok=True)
    (p1b / "domjudge-problem.ini").write_text('short-name = B\nname = "Is Subsequence"\ntimelimit = 2\ncolor = "#3182CE"\n', encoding="utf-8")
    (p1b / "problem.yaml").write_text("name: Is Subsequence\nlimits:\n  memory: 1024\n", encoding="utf-8")
    (p1b / "statement.html").write_text("""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:1.5rem;background:#161720;color:#e2e8f0;line-height:1.6;">
<h2>Problem B — Is Subsequence (LeetCode 392)</h2>
<p><strong>Time limit:</strong> 2.0s &bull; <strong>Memory limit:</strong> 1024 MB</p>
<p>Given two strings $s$ and $t$, return <code>true</code> if $s$ is a subsequence of $t$, or <code>false</code> otherwise.</p>
<div style="background:#12131a;border:1px solid #242634;border-radius:6px;padding:10px 14px;margin-top:14px;">
  <strong>Key Idea (Two Pointers):</strong> Walk through $t$ and advance a pointer in $s$ on each match.
</div>
</body></html>""", encoding="utf-8")
    s = p1b / "data" / "sample"
    s.mkdir(parents=True, exist_ok=True)
    (s / "1.in").write_text("abc\nahbgdc\n", encoding="utf-8")
    (s / "1.ans").write_text("true\n", encoding="utf-8")
    (s / "2.in").write_text("axc\nahbgdc\n", encoding="utf-8")
    (s / "2.ans").write_text("false\n", encoding="utf-8")
    acc = p1b / "submissions" / "accepted"
    acc.mkdir(parents=True, exist_ok=True)
    (acc / "solution.py").write_text("""import sys
parts = sys.stdin.read().split()
if len(parts) >= 2:
    s, t = parts[0], parts[1]
elif len(parts) == 1:
    s, t = parts[0], ""
else:
    s, t = "", ""
i = 0
for ch in t:
    if i < len(s) and s[i] == ch:
        i += 1
print("true" if i == len(s) else "false")
""", encoding="utf-8")

    # 1C: Minimum Path Sum
    p1c = c_dir / "C-minimum-path-sum"
    p1c.mkdir(parents=True, exist_ok=True)
    (p1c / "domjudge-problem.ini").write_text('short-name = C\nname = "Minimum Path Sum"\ntimelimit = 2\ncolor = "#805AD5"\n', encoding="utf-8")
    (p1c / "problem.yaml").write_text("name: Minimum Path Sum\nlimits:\n  memory: 1024\n", encoding="utf-8")
    (p1c / "statement.html").write_text("""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:1.5rem;background:#161720;color:#e2e8f0;line-height:1.6;">
<h2>Problem C — Minimum Path Sum (LeetCode 64)</h2>
<p><strong>Time limit:</strong> 2.0s &bull; <strong>Memory limit:</strong> 1024 MB</p>
<p>Given an $m \\times n$ grid filled with non-negative numbers, find a path from top-left to bottom-right that minimizes the sum of all numbers along its path. You can only move either down or right at any point in time.</p>
<div style="background:#12131a;border:1px solid #242634;border-radius:6px;padding:10px 14px;margin-top:14px;">
  <strong>Key Idea (Grid DP):</strong> <code>grid[i][j] += min(grid[i-1][j], grid[i][j-1])</code>
</div>
</body></html>""", encoding="utf-8")
    s = p1c / "data" / "sample"
    s.mkdir(parents=True, exist_ok=True)
    (s / "1.in").write_text("3 3\n1 3 1\n1 5 1\n4 2 1\n", encoding="utf-8")
    (s / "1.ans").write_text("7\n", encoding="utf-8")
    (s / "2.in").write_text("2 3\n1 2 3\n4 5 6\n", encoding="utf-8")
    (s / "2.ans").write_text("12\n", encoding="utf-8")
    acc = p1c / "submissions" / "accepted"
    acc.mkdir(parents=True, exist_ok=True)
    (acc / "solution.py").write_text("""import sys
data = list(map(int, sys.stdin.read().split()))
if data:
    m, n = data[0], data[1]
    grid = []
    p = 2
    for _ in range(m):
        grid.append(data[p:p+n])
        p += n
    for i in range(m):
        for j in range(n):
            if i == 0 and j == 0:
                continue
            up = grid[i-1][j] if i > 0 else float('inf')
            left = grid[i][j-1] if j > 0 else float('inf')
            grid[i][j] += min(up, left)
    print(grid[-1][-1])
""", encoding="utf-8")

    # 1D: Vacation
    p1d = c_dir / "D-vacation"
    p1d.mkdir(parents=True, exist_ok=True)
    (p1d / "domjudge-problem.ini").write_text('short-name = D\nname = "Vacation"\ntimelimit = 2\ncolor = "#D69E2E"\n', encoding="utf-8")
    (p1d / "problem.yaml").write_text("name: Vacation\nlimits:\n  memory: 1024\n", encoding="utf-8")
    (p1d / "statement.html").write_text("""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:1.5rem;background:#161720;color:#e2e8f0;line-height:1.6;">
<h2>Problem D — Vacation (AtCoder dp_c)</h2>
<p><strong>Time limit:</strong> 2.0s &bull; <strong>Memory limit:</strong> 1024 MB</p>
<p>The summer vacation consists of $N$ days. On day $i$, Taro can choose activity A (gain $a_i$), B (gain $b_i$), or C (gain $c_i$). He cannot do the same activity on two consecutive days.</p>
<p>Find the maximum possible total happiness points.</p>
<div style="background:#12131a;border:1px solid #242634;border-radius:6px;padding:10px 14px;margin-top:14px;">
  <strong>Key Idea (DP with States):</strong> <code>a, b, c = x + max(b, c), y + max(a, c), z + max(a, b)</code>
</div>
</body></html>""", encoding="utf-8")
    s = p1d / "data" / "sample"
    s.mkdir(parents=True, exist_ok=True)
    (s / "1.in").write_text("3\n10 40 70\n20 50 80\n30 60 90\n", encoding="utf-8")
    (s / "1.ans").write_text("210\n", encoding="utf-8")
    (s / "2.in").write_text("1\n100 10 1\n", encoding="utf-8")
    (s / "2.ans").write_text("100\n", encoding="utf-8")
    (s / "3.in").write_text("7\n6 7 8\n8 8 3\n2 5 2\n7 8 6\n4 6 8\n2 3 4\n7 5 1\n", encoding="utf-8")
    (s / "3.ans").write_text("46\n", encoding="utf-8")
    acc = p1d / "submissions" / "accepted"
    acc.mkdir(parents=True, exist_ok=True)
    (acc / "solution.py").write_text("""import sys
lines = sys.stdin.read().split()
if lines:
    n = int(lines[0])
    a = b = c = 0
    p = 1
    for _ in range(n):
        x, y, z = int(lines[p]), int(lines[p+1]), int(lines[p+2])
        p += 3
        a, b, c = x + max(b, c), y + max(a, c), z + max(a, b)
    print(max(a, b, c))
""", encoding="utf-8")

    parse_contest_dir(c_dir, tpl, "10sep-contest")
    print("[PASS] Scaffolding 10sep-contest complete.")

def setup_17sep():
    c_dir = ws / "17sep-contest"
    c_dir.mkdir(parents=True, exist_ok=True)

    # 2A: Alternating Sequences (SPOJ ALTSEQ)
    p2a = c_dir / "A-alternating-sequences"
    p2a.mkdir(parents=True, exist_ok=True)
    (p2a / "domjudge-problem.ini").write_text('short-name = A\nname = "Alternating Sequences"\ntimelimit = 1\ncolor = "#38A169"\n', encoding="utf-8")
    (p2a / "problem.yaml").write_text("name: Alternating Sequences\nlimits:\n  memory: 1024\n", encoding="utf-8")
    (p2a / "statement.html").write_text("""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:1.5rem;background:#161720;color:#e2e8f0;line-height:1.6;">
<h2>Problem A — Alternating Sequences (SPOJ ALTSEQ)</h2>
<p><strong>Time limit:</strong> 1.0s &bull; <strong>Memory limit:</strong> 1024 MB</p>
<p>Given an array $A$ of $N$ non-zero integers, find the length of the longest subsequence $b_1, b_2, \\dots, b_k$ such that $|b_1| < |b_2| < \\dots < |b_k|$ and signs alternate between adjacent elements.</p>
<div style="background:#12131a;border:1px solid #242634;border-radius:6px;padding:10px 14px;margin-top:14px;">
  <strong>Key Idea (LIS with Alternating Signs):</strong> Fenwick tree or DP maintaining max alternating length.
</div>
</body></html>""", encoding="utf-8")
    s = p2a / "data" / "sample"
    s.mkdir(parents=True, exist_ok=True)
    (s / "1.in").write_text("8\n1 2 -2 -3 5 -7 -8 10\n", encoding="utf-8")
    (s / "1.ans").write_text("5\n", encoding="utf-8")
    acc = p2a / "submissions" / "accepted"
    acc.mkdir(parents=True, exist_ok=True)
    (acc / "solution.py").write_text("""import sys
data = list(map(int, sys.stdin.read().split()))
if data:
    n = data[0]
    a = data[1:1+n]
    dp = [1] * n
    for i in range(n):
        for j in range(i):
            if abs(a[j]) < abs(a[i]) and ((a[j] > 0 and a[i] < 0) or (a[j] < 0 and a[i] > 0)):
                dp[i] = max(dp[i], dp[j] + 1)
    print(max(dp))
""", encoding="utf-8")

    # 2B: Philosophers Stone (SPOJ BYTESM2)
    p2b = c_dir / "B-philosophers-stone"
    p2b.mkdir(parents=True, exist_ok=True)
    (p2b / "domjudge-problem.ini").write_text('short-name = B\nname = "Philosophers Stone"\ntimelimit = 1\ncolor = "#319795"\n', encoding="utf-8")
    (p2b / "problem.yaml").write_text("name: Philosophers Stone\nlimits:\n  memory: 1024\n", encoding="utf-8")
    (p2b / "statement.html").write_text("""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:1.5rem;background:#161720;color:#e2e8f0;line-height:1.6;">
<h2>Problem B — Philosophers Stone (SPOJ BYTESM2)</h2>
<p><strong>Time limit:</strong> 1.0s &bull; <strong>Memory limit:</strong> 1024 MB</p>
<p>A chamber has $h \\times w$ tiles. Harry starts at any tile in the first row and moves to the last row. From $(r, c)$, he can move to $(r+1, c-1)$, $(r+1, c)$, or $(r+1, c+1)$. Find the maximum stones he can collect.</p>
<div style="background:#12131a;border:1px solid #242634;border-radius:6px;padding:10px 14px;margin-top:14px;">
  <strong>Key Idea (Grid DP):</strong> <code>dp = [row[j] + max(dp[max(j-1,0):j+2]) for j in range(w)]</code>
</div>
</body></html>""", encoding="utf-8")
    s = p2b / "data" / "sample"
    s.mkdir(parents=True, exist_ok=True)
    (s / "1.in").write_text("1\n6 5\n3 1 7 4 2\n2 1 3 1 1\n1 2 2 1 8\n2 2 1 5 3\n2 1 4 4 4\n5 2 7 5 1\n", encoding="utf-8")
    (s / "1.ans").write_text("32\n", encoding="utf-8")
    acc = p2b / "submissions" / "accepted"
    acc.mkdir(parents=True, exist_ok=True)
    (acc / "solution.py").write_text("""import sys
data = list(map(int, sys.stdin.read().split()))
if data:
    t, p = data[0], 1
    for _ in range(t):
        h, w = data[p], data[p + 1]; p += 2
        dp = data[p:p + w]; p += w
        for _ in range(h - 1):
            row = data[p:p + w]; p += w
            dp = [row[j] + max(dp[max(j-1, 0):j+2]) for j in range(w)]
        print(max(dp))
""", encoding="utf-8")

    # 2C: Alphacode (SPOJ ACODE)
    p2c = c_dir / "C-alphacode"
    p2c.mkdir(parents=True, exist_ok=True)
    (p2c / "domjudge-problem.ini").write_text('short-name = C\nname = "Alphacode"\ntimelimit = 1\ncolor = "#00A3C4"\n', encoding="utf-8")
    (p2c / "problem.yaml").write_text("name: Alphacode\nlimits:\n  memory: 1024\n", encoding="utf-8")
    (p2c / "statement.html").write_text("""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:1.5rem;background:#161720;color:#e2e8f0;line-height:1.6;">
<h2>Problem C — Alphacode (SPOJ ACODE)</h2>
<p><strong>Time limit:</strong> 1.0s &bull; <strong>Memory limit:</strong> 1024 MB</p>
<p>Alice and Bob encode messages using 'A'=1, ..., 'Z'=26. Given a string of digits, output the number of possible decodings. Input ends with '0'.</p>
<div style="background:#12131a;border:1px solid #242634;border-radius:6px;padding:10px 14px;margin-top:14px;">
  <strong>Key Idea (Fibonacci-like Counting DP):</strong> Single digit if $\\ne 0$, plus two-digit if in $[10, 26]$.
</div>
</body></html>""", encoding="utf-8")
    s = p2c / "data" / "sample"
    s.mkdir(parents=True, exist_ok=True)
    (s / "1.in").write_text("25114\n1111111111\n3333333333\n0\n", encoding="utf-8")
    (s / "1.ans").write_text("6\n89\n1\n", encoding="utf-8")
    acc = p2c / "submissions" / "accepted"
    acc.mkdir(parents=True, exist_ok=True)
    (acc / "solution.py").write_text("""import sys
for s in sys.stdin.read().split():
    if s == '0':
        break
    a, b = 1, 1
    for i in range(1, len(s)):
        c = 0
        if s[i] != '0':
            c += b
        if s[i-1] == '1' or (s[i-1] == '2' and s[i] <= '6'):
            c += a
        a, b = b, c
    print(b)
""", encoding="utf-8")

    # 2D: Aibohphobia (SPOJ AIBOHP)
    p2d = c_dir / "D-aibohphobia"
    p2d.mkdir(parents=True, exist_ok=True)
    (p2d / "domjudge-problem.ini").write_text('short-name = D\nname = "Aibohphobia"\ntimelimit = 2\ncolor = "#E53E3E"\n', encoding="utf-8")
    (p2d / "problem.yaml").write_text("name: Aibohphobia\nlimits:\n  memory: 1024\n", encoding="utf-8")
    (p2d / "statement.html").write_text("""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:1.5rem;background:#161720;color:#e2e8f0;line-height:1.6;">
<h2>Problem D — Aibohphobia (SPOJ AIBOHP)</h2>
<p><strong>Time limit:</strong> 2.0s &bull; <strong>Memory limit:</strong> 1024 MB</p>
<p>Given a string $S$ (up to 6100 characters), find the minimum number of characters that must be inserted anywhere in $S$ to make it a palindrome.</p>
<div style="background:#12131a;border:1px solid #242634;border-radius:6px;padding:10px 14px;margin-top:14px;">
  <strong>Key Idea (LCS DP):</strong> <code>min_insertions = len(s) - LCS(s, reverse(s))</code>
</div>
</body></html>""", encoding="utf-8")
    s = p2d / "data" / "sample"
    s.mkdir(parents=True, exist_ok=True)
    (s / "1.in").write_text("1\nfft\n", encoding="utf-8")
    (s / "1.ans").write_text("1\n", encoding="utf-8")
    acc = p2d / "submissions" / "accepted"
    acc.mkdir(parents=True, exist_ok=True)
    (acc / "solution.py").write_text("""import sys
def min_insertions(s):
    n = len(s)
    mask = {}
    for i, ch in enumerate(s):
        mask[ch] = mask.get(ch, 0) | (1 << i)
    full = (1 << n) - 1
    v = full
    for ch in reversed(s):
        u = v & mask.get(ch, 0)
        v = ((v + u) | (v - u)) & full
    lcs = n - bin(v).count('1')
    return n - lcs

data = sys.stdin.read().split()
if data:
    t = int(data[0])
    for s in data[1:1+t]:
        print(min_insertions(s))
""", encoding="utf-8")

    parse_contest_dir(c_dir, tpl, "17sep-contest")
    print("[PASS] Scaffolding 17sep-contest complete.")

if __name__ == "__main__":
    setup_10sep()
    setup_17sep()

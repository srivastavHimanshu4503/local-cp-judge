"""Populate structured HTML & Markdown statements for 15oct-contest on fresh clones."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_ROOT = ROOT / "local-cp-judge"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.parser import parse_contest_dir  # noqa: E402


STATEMENTS_15OCT: dict[str, tuple[str, str]] = {
    "A-anagram-check": (
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Problem A — Anagram Check</title>
</head>
<body>
<main>
<h1>Problem A — Anagram Check</h1>
<p class="subtitle">Time limit: 2 seconds (Java), 6 seconds (Python) &middot; Memory limit: 1024 MB</p>
<p>You are given two strings <code>s</code> and <code>t</code>. Decide whether <code>t</code> is an anagram of <code>s</code>.</p>
<h2>What is an anagram</h2>
<p>A string <code>t</code> is an anagram of a string <code>s</code> if <code>t</code> can be formed by rearranging the letters of <code>s</code>, using every letter of <code>s</code> exactly once. Equivalently, every letter appears the same number of times in <code>s</code> as in <code>t</code>.</p>
<ul>
  <li>Two anagrams always have the same length.</li>
  <li>A string is an anagram of itself.</li>
  <li>If <code>t</code> is an anagram of <code>s</code>, then <code>s</code> is also an anagram of <code>t</code>.</li>
</ul>
<table>
  <thead><tr><th>s</th><th>t</th><th>Anagram?</th><th>Why</th></tr></thead>
  <tbody>
    <tr><td><code>listen</code></td><td><code>silent</code></td><td>yes</td><td>both contain e, i, l, n, s, t once each</td></tr>
    <tr><td><code>aab</code></td><td><code>aba</code></td><td>yes</td><td>both contain two a&rsquo;s and one b</td></tr>
    <tr><td><code>aab</code></td><td><code>abb</code></td><td>no</td><td>s has two a&rsquo;s but t has only one</td></tr>
    <tr><td><code>abc</code></td><td><code>abcd</code></td><td>no</td><td>t has an extra d</td></tr>
    <tr><td><code>abc</code></td><td><code>abd</code></td><td>no</td><td>s has a c, t has a d instead</td></tr>
  </tbody>
</table>
<h2>Input format</h2>
<ul>
  <li>The first line contains the string <code>s</code>.</li>
  <li>The second line contains the string <code>t</code>.</li>
</ul>
<h2>Output format</h2>
<p>One line: <code>YES</code> if <code>t</code> is an anagram of <code>s</code>, otherwise <code>NO</code>.</p>
<h2>Constraints</h2>
<ul>
  <li>1 &le; length of s &le; 1 000 000</li>
  <li>1 &le; length of t &le; 1 000 000</li>
  <li><code>s</code> and <code>t</code> contain only lowercase English letters <code>a</code> to <code>z</code>.</li>
  <li>The two lengths may be different.</li>
</ul>
<h2>Sample 1</h2>
<p><strong>Input</strong></p>
<pre><code>listen
silent</code></pre>
<p><strong>Output</strong></p>
<pre><code>YES</code></pre>
<p><strong>Explanation:</strong> Both strings contain the letters <code>e</code>, <code>i</code>, <code>l</code>, <code>n</code>, <code>s</code> and <code>t</code> exactly once each.</p>
<h2>Sample 2</h2>
<p><strong>Input</strong></p>
<pre><code>aab
abb</code></pre>
<p><strong>Output</strong></p>
<pre><code>NO</code></pre>
<p><strong>Explanation:</strong> Both strings use only the letters <code>a</code> and <code>b</code>, but <code>s</code> has two <code>a</code>&rsquo;s and one <code>b</code> while <code>t</code> has one <code>a</code> and two <code>b</code>&rsquo;s.</p>

</main>
</body>
</html>
""",
        """# Problem A — Anagram Check

**Time limit:** 2 seconds (Java), 6 seconds (Python) · **Memory limit:** 1024 MB

You are given two strings `s` and `t`. Decide whether `t` is an anagram of `s`.

## What is an anagram

A string `t` is an anagram of a string `s` if `t` can be formed by rearranging the letters of `s`, using every letter of `s` exactly once. Equivalently, every letter appears the same number of times in `s` as in `t`.

From this definition:
- Two anagrams always have the same length.
- A string is an anagram of itself.
- If `t` is an anagram of `s`, then `s` is also an anagram of `t`.

| `s` | `t` | Anagram? | Why |
|---|---|---|---|
| `listen` | `silent` | YES | both contain `e, i, l, n, s, t` once each |
| `aab` | `aba` | YES | both contain two `a`'s and one `b` |
| `aab` | `abb` | NO | `s` has two `a`'s but `t` has only one |
| `abc` | `abcd` | NO | `t` has an extra `d` |
| `abc` | `abd` | NO | `s` has a `c`, `t` has a `d` instead |

## Input format

- The first line contains the string `s`.
- The second line contains the string `t`.

## Output format

One line: `YES` if `t` is an anagram of `s`, otherwise `NO`.

## Constraints

- `1 ≤ length of s ≤ 1 000 000`
- `1 ≤ length of t ≤ 1 000 000`
- `s` and `t` contain only lowercase English letters `a` to `z`.
- The two lengths may be different.

## Sample 1

**Input**
```text
listen
silent
```

**Output**
```text
YES
```

**Explanation:** Both strings contain the letters `e`, `i`, `l`, `n`, `s` and `t` exactly once each.

## Sample 2

**Input**
```text
aab
abb
```

**Output**
```text
NO
```

**Explanation:** Both strings use only the letters `a` and `b`, but `s` has two `a`'s and one `b` while `t` has one `a` and two `b`'s.
""",
    ),
    "B-floor-index": (
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Problem B — Floor Index</title>
</head>
<body>
<main>
<h1>Problem B — Floor Index</h1>
<p class="subtitle">Time limit: 2 seconds (Java), 6 seconds (Python) &middot; Memory limit: 1024 MB</p>
<p>You are given an array <code>arr</code> of <code>n</code> integers, sorted in non-decreasing order: <code>arr[0] &le; arr[1] &le; &hellip; &le; arr[n &minus; 1]</code>. The same value may appear several times. Indexes start at <code>0</code>.</p>
<p>You are also given <code>q</code> keys. For each key, find the largest index <code>i</code> such that <code>arr[i] &le; key</code>. If every element of the array is greater than the key, the answer is <code>-1</code>.</p>
<h2>When values repeat</h2>
<p>Because you must return the largest such index, a repeated value is always answered with the index of its last copy. For example, with <code>arr = [2, 4, 4, 4, 7, 10]</code>:</p>
<table>
  <thead><tr><th>key</th><th>answer</th><th>why</th></tr></thead>
  <tbody>
    <tr><td><code>4</code></td><td><code>3</code></td><td>the elements &le; 4 are at indexes 0, 1, 2, 3; largest is 3</td></tr>
    <tr><td><code>5</code></td><td><code>3</code></td><td>no element equals 5; largest element &le; 5 is 4 at index 3</td></tr>
    <tr><td><code>1</code></td><td><code>-1</code></td><td>every element is greater than 1</td></tr>
  </tbody>
</table>
<h2>Input format</h2>
<ul>
  <li>The first line contains two integers <code>n</code> and <code>q</code>.</li>
  <li>The second line contains <code>n</code> integers separated by single spaces: the array, in non-decreasing order.</li>
  <li>Each of the next <code>q</code> lines contains one integer: a key.</li>
</ul>
<h2>Output format</h2>
<p><code>q</code> lines. Line <code>j</code> contains the answer for the <code>j</code>-th key.</p>
<h2>Constraints</h2>
<ul>
  <li>1 &le; n &le; 200 000</li>
  <li>1 &le; q &le; 200 000</li>
  <li>&minus;1 000 000 000 &le; arr[i] &le; 1 000 000 000, non-decreasing</li>
  <li>&minus;1 000 000 000 &le; key &le; 1 000 000 000</li>
</ul>
<h2>Sample 1</h2>
<p><strong>Input</strong></p>
<pre><code>6 5
2 4 4 4 7 10
4
5
1
10
3</code></pre>
<p><strong>Output</strong></p>
<pre><code>3
3
-1
5
0</code></pre>
<p><strong>Explanation:</strong></p>
<ul>
  <li>Key <code>4</code>: appears at indexes 1, 2 and 3; largest is <code>3</code>.</li>
  <li>Key <code>5</code>: largest element &le; 5 is the last 4, at index <code>3</code>.</li>
  <li>Key <code>1</code>: all elements are &gt; 1, so <code>-1</code>.</li>
  <li>Key <code>10</code>: all elements are &le; 10, so last index <code>5</code>.</li>
  <li>Key <code>3</code>: only 2 at index 0 is &le; 3, so <code>0</code>.</li>
</ul>

</main>
</body>
</html>
""",
        """# Problem B — Floor Index

**Time limit:** 2 seconds (Java), 6 seconds (Python) · **Memory limit:** 1024 MB

You are given an array `arr` of `n` integers, sorted in non-decreasing order:

`arr[0] ≤ arr[1] ≤ … ≤ arr[n − 1]`

The same value may appear several times. Indexes start at `0`.

You are also given `q` keys. For each key, find the **largest index** `i` such that `arr[i] ≤ key`. If every element of the array is greater than the key, the answer is `-1`.

## When values repeat

Because you must return the largest such index, a repeated value is always answered with the index of its last copy.

For example, with `arr = [2, 4, 4, 4, 7, 10]`:

| key | answer | why |
|---|---|---|
| `4` | `3` | elements `≤ 4` are at indexes `0, 1, 2, 3`; largest is `3` |
| `5` | `3` | no element equals `5`; largest element `≤ 5` is `4` at index `3` |
| `1` | `-1` | every element is greater than `1` |

## Input format

- The first line contains two integers `n` and `q`.
- The second line contains `n` integers separated by single spaces: the array, in non-decreasing order.
- Each of the next `q` lines contains one integer: a key.

## Output format

`q` lines. Line `j` contains the answer for the `j`-th key.

## Constraints

- `1 ≤ n ≤ 200 000`
- `1 ≤ q ≤ 200 000`
- `-1 000 000 000 ≤ arr[i] ≤ 1 000 000 000`, sorted in non-decreasing order
- `-1 000 000 000 ≤ key ≤ 1 000 000 000`

## Sample 1

**Input**
```text
6 5
2 4 4 4 7 10
4
5
1
10
3
```

**Output**
```text
3
3
-1
5
0
```

**Explanation:**
- Key `4`: value `4` appears at indexes `1, 2, 3`; largest is `3`.
- Key `5`: largest element `≤ 5` is `4` at index `3`.
- Key `1`: every element is greater than `1`, so `-1`.
- Key `10`: every element is `≤ 10`, so last index `5`.
- Key `3`: only `2` at index `0` is `≤ 3`, so `0`.
""",
    ),
    "C-campus-network": (
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Problem C — Campus Network</title>
</head>
<body>
<main>
<h1>Problem C — Campus Network</h1>
<p class="subtitle">Time limit: 3 seconds (Java), 9 seconds (Python) &middot; Memory limit: 1024 MB</p>
<p>The campus has <code>n</code> buildings, numbered <code>0</code> to <code>n &minus; 1</code>, and <code>m</code> network cables. Each cable joins two buildings.</p>
<ul>
  <li>A cable works in both directions: if a cable joins <code>a</code> and <code>b</code>, data can go from <code>a</code> to <code>b</code> and from <code>b</code> to <code>a</code>.</li>
  <li>Data can travel along a chain of cables, passing through other buildings on the way.</li>
  <li>A building can always send data to itself, even if it has no cables.</li>
</ul>
<p>You are given <code>q</code> questions. Each question names two buildings <code>u</code> and <code>v</code> and asks: can building <code>u</code> send data to building <code>v</code>?</p>
<h2>Input format</h2>
<ul>
  <li>The first line contains three integers <code>n</code>, <code>m</code> and <code>q</code>.</li>
  <li>Each of the next <code>m</code> lines contains two integers <code>a</code> and <code>b</code>: a cable.</li>
  <li>Each of the next <code>q</code> lines contains two integers <code>u</code> and <code>v</code>: a question.</li>
</ul>
<p>If <code>m = 0</code>, there are no cable lines: the questions start right after the first line.</p>
<h2>Output format</h2>
<p><code>q</code> lines. Line <code>i</code> contains <code>YES</code> or <code>NO</code>: the answer to the <code>i</code>-th question.</p>
<h2>Constraints</h2>
<ul>
  <li>1 &le; n &le; 200 000</li>
  <li>0 &le; m &le; 200 000</li>
  <li>1 &le; q &le; 200 000</li>
  <li>0 &le; a, b &le; n &minus; 1 and a &ne; b</li>
  <li>0 &le; u, v &le; n &minus; 1 (u and v may be equal)</li>
</ul>
<h2>Sample 1</h2>
<p><strong>Input</strong></p>
<pre><code>6 3 5
0 1
1 2
3 4
0 2
0 3
3 4
5 5
2 5</code></pre>
<p><strong>Output</strong></p>
<pre><code>YES
NO
YES
YES
NO</code></pre>
<p><strong>Explanation:</strong> Connected components are <code>{0, 1, 2}</code>, <code>{3, 4}</code> and <code>{5}</code>.</p>
<ul>
  <li><code>0 &rarr; 2</code>: goes <code>0 &rarr; 1 &rarr; 2</code>, so <code>YES</code>.</li>
  <li><code>0 &rarr; 3</code>: different groups, so <code>NO</code>.</li>
  <li><code>3 &rarr; 4</code>: direct cable, so <code>YES</code>.</li>
  <li><code>5 &rarr; 5</code>: building reaches itself, so <code>YES</code>.</li>
  <li><code>2 &rarr; 5</code>: building 5 has no cables, so <code>NO</code>.</li>
</ul>
<h2>Sample 2</h2>
<p><strong>Input</strong></p>
<pre><code>3 0 2
1 1
0 2</code></pre>
<p><strong>Output</strong></p>
<pre><code>YES
NO</code></pre>
<p><strong>Explanation:</strong> There are no cables (<code>m = 0</code>), so questions start on the second line.</p>

</main>
</body>
</html>
""",
        """# Problem C — Campus Network

**Time limit:** 3 seconds (Java), 9 seconds (Python) · **Memory limit:** 1024 MB

The campus has `n` buildings, numbered `0` to `n - 1`, and `m` network cables. Each cable joins two buildings.

- A cable works in both directions: if a cable joins `a` and `b`, data can go from `a` to `b` and from `b` to `a`.
- Data can travel along a chain of cables, passing through other buildings on the way.
- A building can always send data to itself, even if it has no cables.

You are given `q` questions. Each question names two buildings `u` and `v` and asks: can building `u` send data to building `v`?

## Input format

- The first line contains three integers `n`, `m` and `q`.
- Each of the next `m` lines contains two integers `a` and `b`: a cable.
- Each of the next `q` lines contains two integers `u` and `v`: a question.

If `m = 0`, there are no cable lines: the questions start right after the first line.

## Output format

`q` lines. Line `i` contains `YES` or `NO`: the answer to the `i`-th question.

## Constraints

- `1 ≤ n ≤ 200 000`
- `0 ≤ m ≤ 200 000`
- `1 ≤ q ≤ 200 000`
- `0 ≤ a, b ≤ n - 1` and `a ≠ b`
- `0 ≤ u, v ≤ n - 1` (`u` and `v` may be equal)

## Sample 1

**Input**
```text
6 3 5
0 1
1 2
3 4
0 2
0 3
3 4
5 5
2 5
```

**Output**
```text
YES
NO
YES
YES
NO
```

**Explanation:** Connected buildings form three groups: `{0, 1, 2}`, `{3, 4}`, `{5}`.
- `0 → 2`: `0 → 1 → 2` → `YES`
- `0 → 3`: different groups → `NO`
- `3 → 4`: direct cable → `YES`
- `5 → 5`: building reaches itself → `YES`
- `2 → 5`: building 5 has no cables → `NO`

## Sample 2

**Input**
```text
3 0 2
1 1
0 2
```

**Output**
```text
YES
NO
```
""",
    ),
    "D-cashback-routes": (
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Problem D — Cashback Routes</title>
</head>
<body>
<main>
<h1>Problem D — Cashback Routes</h1>
<p class="subtitle">Time limit: 2 seconds (Java), 6 seconds (Python) &middot; Memory limit: 1024 MB</p>
<p>A city has <code>n</code> bus stops, numbered <code>0</code> to <code>n &minus; 1</code>, and <code>m</code> one-way bus routes. A route <code>u v w</code> takes you from stop <code>u</code> to stop <code>v</code> and costs <code>w</code> coins. Some routes pay cashback (<code>w &lt; 0</code>).</p>
<p>You start at stop <code>s</code>.</p>
<ul>
  <li>A journey may use the same stop or route any number of times; no routes from <code>s</code> to <code>s</code> costs <code>0</code>.</li>
  <li>A negative cycle is a journey starting and ending at the same stop with negative total cost.</li>
</ul>
<p>If you can reach a negative cycle from <code>s</code>, print <code>NEGATIVE CYCLE</code>. A negative cycle unreachable from <code>s</code> does not matter. Otherwise, print the minimum cost to reach each stop <code>0..n-1</code>, or <code>INF</code> if unreachable.</p>
<h2>Input format</h2>
<ul>
  <li>The first line contains three integers <code>n</code>, <code>m</code> and <code>s</code>.</li>
  <li>Each of the next <code>m</code> lines contains three integers <code>u</code>, <code>v</code> and <code>w</code>: a one-way route from stop <code>u</code> to stop <code>v</code> with cost <code>w</code>.</li>
</ul>
<h2>Output format</h2>
<ul>
  <li>If a negative cycle can be reached from <code>s</code>: one line, <code>NEGATIVE CYCLE</code>.</li>
  <li>Otherwise: <code>n</code> lines. Line <code>i</code> contains the minimum cost from <code>s</code> to stop <code>i</code>, or <code>INF</code>.</li>
</ul>
<h2>Constraints</h2>
<ul>
  <li>1 &le; n &le; 2 500</li>
  <li>0 &le; m &le; 5 000</li>
  <li>0 &le; s &le; n &minus; 1</li>
  <li>0 &le; u, v &le; n &minus; 1</li>
  <li>&minus;1 000 000 000 &le; w &le; 1 000 000 000</li>
  <li>Parallel edges and self-loops (<code>u = v</code>) may exist.</li>
</ul>
<h2>Sample 1</h2>
<p><strong>Input</strong></p>
<pre><code>5 4 0
0 1 1
0 2 5
2 1 -10
1 3 1</code></pre>
<p><strong>Output</strong></p>
<pre><code>0
-5
5
-4
INF</code></pre>
<p><strong>Explanation:</strong></p>
<ul>
  <li>Stop 0: start, cost <code>0</code>.</li>
  <li>Stop 1: <code>0 &rarr; 2 &rarr; 1</code> costs <code>5 + (&minus;10) = &minus;5</code>.</li>
  <li>Stop 2: <code>0 &rarr; 2</code> costs <code>5</code>.</li>
  <li>Stop 3: <code>0 &rarr; 2 &rarr; 1 &rarr; 3</code> costs <code>&minus;4</code>.</li>
  <li>Stop 4: unreachable, so <code>INF</code>.</li>
</ul>
<h2>Sample 2</h2>
<p><strong>Input</strong></p>
<pre><code>3 3 0
0 1 2
1 2 -1
2 1 -2</code></pre>
<p><strong>Output</strong></p>
<pre><code>NEGATIVE CYCLE</code></pre>
<p><strong>Explanation:</strong> Cycle <code>1 &rarr; 2 &rarr; 1</code> has total cost <code>&minus;3</code> and is reachable from <code>0</code>.</p>

</main>
</body>
</html>
""",
        """# Problem D — Cashback Routes

**Time limit:** 2 seconds (Java), 6 seconds (Python) · **Memory limit:** 1024 MB

A city has `n` bus stops, numbered `0` to `n - 1`, and `m` one-way bus routes. A route `u v w` takes you from stop `u` to stop `v` and costs `w` coins. Some routes run a promotion and pay you cashback: their cost `w` is negative, and riding them gives you `|w|` coins.

You start at stop `s`.

- A journey is a sequence of routes in which each route starts at the stop where the previous one ended. A journey may use the same stop or the same route any number of times.
- The cost of a journey is the sum of the costs of its routes. The journey with no routes, from `s` to `s` itself, costs `0`.
- A negative cycle is a journey that starts and ends at the same stop and has a negative total cost.

If you can reach a negative cycle from `s`, report `NEGATIVE CYCLE`. A negative cycle that cannot be reached from `s` does not matter.

Otherwise, for every stop, find the minimum cost of a journey from `s` to that stop. If no journey from `s` reaches a stop, its answer is `INF`.

## Input format

- The first line contains three integers `n`, `m` and `s`.
- Each of the next `m` lines contains three integers `u`, `v` and `w`: a one-way route from stop `u` to stop `v` with cost `w`.

## Output format

- If a negative cycle can be reached from `s`: one line, `NEGATIVE CYCLE`.
- Otherwise: `n` lines. Line `i` (counting from `0`) contains the minimum cost from `s` to stop `i`, or `INF`.

## Constraints

- `1 ≤ n ≤ 2 500`
- `0 ≤ m ≤ 5 000`
- `0 ≤ s ≤ n - 1`
- `0 ≤ u, v ≤ n - 1`
- `-1 000 000 000 ≤ w ≤ 1 000 000 000`
- Several routes may join the same two stops, and a route may start and end at the same stop (`u = v`).

## Sample 1

**Input**
```text
5 4 0
0 1 1
0 2 5
2 1 -10
1 3 1
```

**Output**
```text
0
-5
5
-4
INF
```

**Explanation:**
- Stop 0 is the start (`0`).
- Stop 1: `0 → 2 → 1` costs `5 + (-10) = -5`.
- Stop 2: `0 → 2` costs `5`.
- Stop 3: `0 → 2 → 1 → 3` costs `-4`.
- Stop 4: unreachable (`INF`).

## Sample 2

**Input**
```text
3 3 0
0 1 2
1 2 -1
2 1 -2
```

**Output**
```text
NEGATIVE CYCLE
```
""",
    ),
}


def populate_15oct_statements(workspaces_root: Path | None = None) -> int:
    """Writes statement.html & problem.md into 15oct-contest problems and refreshes metadata."""
    ws = workspaces_root or (APP_ROOT / "workspaces")
    templates_dir = ws.parent / "templates"
    contest_dir = ws / "15oct-contest"
    if not contest_dir.exists():
        return 0

    updated = 0
    for prob_id, (html_text, md_text) in STATEMENTS_15OCT.items():
        prob_dir = contest_dir / prob_id
        if not prob_dir.is_dir():
            continue
        html_path = prob_dir / "statement.html"
        md_path = prob_dir / "problem.md"
        if not html_path.exists():
            html_path.write_text(html_text, encoding="utf-8")
            updated += 1
        if not md_path.exists():
            md_path.write_text(md_text, encoding="utf-8")

    parse_contest_dir(contest_dir, templates_dir, contest_id="15oct-contest")
    return updated


if __name__ == "__main__":
    count = populate_15oct_statements()
    print(f"Populated {count} missing HTML statement(s) for 15oct-contest.")

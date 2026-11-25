import os
from pathlib import Path

BASE_DIR = Path("local-cp-judge/workspaces")

CSS = """
<style>
  /* obsidian-statement-theme */
  :root {
    --bg-app: #09090B;
    --bg-panel: #111115;
    --bg-surface-subtle: #18181B;
    --bg-surface-hover: #1F1F24;
    --border-subtle: #27272A;
    --border-strong: #3F3F46;
    --text-primary: #FAFAFA;
    --text-secondary: #A1A1AA;
    --text-muted: #71717A;
    --accent-ac: #10B981;
  }
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    scrollbar-width: thin;
    scrollbar-color: #27272A transparent;
  }
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #27272A; border-radius: 9999px; }
  ::-webkit-scrollbar-thumb:hover { background: #3F3F46; }

  body {
    background: var(--bg-app);
    color: var(--text-secondary);
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
    line-height: 1.65;
    padding: 24px 28px 36px;
    -webkit-font-smoothing: antialiased;
  }
  .statement-container {
    max-width: 72ch;
  }
  a { color: var(--text-muted); text-decoration: none; }
  a:hover { color: var(--text-primary); }

  /* Metadata Strip: Uniform Muted Monochrome Chips */
  .meta-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 14px;
  }
  .meta-chip {
    display: inline-flex;
    align-items: center;
    padding: 2px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    background: var(--bg-surface-subtle);
    border: 1px solid var(--border-subtle);
    color: var(--text-secondary);
  }

  /* Title Row */
  .title-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-subtle);
  }
  .title-row h1 {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-primary);
    line-height: 1.25;
  }
  .source-link {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-muted);
    transition: color 0.15s ease;
    white-space: nowrap;
  }
  .source-link:hover {
    color: var(--text-primary);
    text-decoration: none;
  }

  .section-block {
    margin-bottom: 24px;
  }
  h2 {
    font-size: 13px;
    font-weight: 600;
    color: #E4E4E7;
    margin-bottom: 10px;
    letter-spacing: -0.01em;
  }
  h3 {
    font-size: 13.5px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 8px 0;
  }
  p { margin-bottom: 10px; max-width: 68ch; }
  ul, ol { margin-left: 18px; margin-bottom: 12px; max-width: 68ch; }
  li { margin-bottom: 4px; }
  strong { color: #E4E4E7; font-weight: 600; }

  code {
    font-family: "JetBrains Mono", Consolas, Menlo, monospace;
    font-size: 12.5px;
    background: var(--bg-surface-subtle);
    border: 1px solid var(--border-subtle);
    border-radius: 4px;
    padding: 1px 5px;
    color: #E4E4E7;
  }
  pre {
    font-family: "JetBrains Mono", Consolas, Menlo, monospace;
    font-size: 13px;
    background: var(--bg-panel);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 10px 12px;
    overflow-x: auto;
    color: var(--text-primary);
    line-height: 1.55;
    margin-bottom: 10px;
  }

  /* Side-by-Side Example Cards */
  .example-wrapper {
    margin-bottom: 16px;
  }
  .example-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 8px;
  }
  @media (max-width: 600px) {
    .example-grid { grid-template-columns: 1fr; }
  }
  .io-card {
    background: var(--bg-panel);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .io-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(39, 39, 42, 0.6);
  }
  .io-card-title {
    font-size: 12px;
    font-weight: 600;
    color: #E4E4E7;
  }
  .btn-copy-sample {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-family: "Inter", sans-serif;
    font-size: 11.5px;
    font-weight: 500;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 5px;
    transition: color 0.15s ease, background-color 0.15s ease;
  }
  .btn-copy-sample:hover {
    color: var(--text-primary);
    background: var(--bg-surface-hover);
  }
  .btn-copy-sample.copied {
    color: var(--accent-ac);
  }
  .io-card pre {
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
    font-size: 13px;
    line-height: 1.55;
    color: var(--text-primary);
  }
  .example-explanation {
    background: var(--bg-panel);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
    line-height: 1.6;
    color: var(--text-secondary);
  }

  .dp-analysis-card {
    background: var(--bg-panel);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 14px 16px;
    margin-top: 24px;
  }
  .dp-analysis-card pre {
    background: var(--bg-app);
  }
</style>
"""

PROBLEMS = {
    "10sep-contest/A-rabbit-frog-1": {
        "title": "Problem A — Rabbit / Frog 1",
        "platform": "AtCoder Educational DP Contest · Task A (dp_a)",
        "source_url": "https://atcoder.jp/contests/dp/tasks/dp_a",
        "time_limit": "2.0s",
        "memory_limit": "1024 MB",
        "category": "1D Dynamic Programming",
        "description": """
<p>There are <em>N</em> stones numbered 1, 2, ..., <em>N</em>. For each <em>i</em> (1 &le; <em>i</em> &le; <em>N</em>), the height of Stone <em>i</em> is <em>h<sub>i</sub></em>.</p>
<p>A frog is initially on Stone 1. It will repeat the following action some number of times to reach Stone <em>N</em>:</p>
<ul>
  <li>If the frog is currently on Stone <em>i</em>, jump to Stone <em>i + 1</em> or Stone <em>i + 2</em>. Here, a cost of |<em>h<sub>i</sub></em> &minus; <em>h<sub>j</sub></em>| is incurred, where <em>j</em> is the stone to land on.</li>
</ul>
<p>Find the minimum possible total cost incurred before the frog reaches Stone <em>N</em>.</p>
""",
        "input_format": """
<p>The input is given from Standard Input in the following format:</p>
<pre>N
h_1 h_2 ... h_N</pre>
""",
        "output_format": """
<p>Print the minimum possible total cost incurred.</p>
""",
        "constraints": """
<ul>
  <li>2 &le; <em>N</em> &le; 10<sup>5</sup></li>
  <li>1 &le; <em>h<sub>i</sub></em> &le; 10<sup>4</sup></li>
  <li>All values in input are integers.</li>
</ul>
""",
        "examples": [
            {
                "num": 1,
                "input": "4\n10 30 40 20",
                "output": "30",
                "explanation": "Follow the path: <strong>Stone 1 &rarr; Stone 2 &rarr; Stone 4</strong>.<br>• Jump 1 &rarr; 2: cost = |10 &minus; 30| = 20.<br>• Jump 2 &rarr; 4: cost = |30 &minus; 20| = 10.<br>• Total cost = 20 + 10 = <strong>30</strong>.<br>(Taking 1 &rarr; 3 &rarr; 4 would cost |10 &minus; 40| + |40 &minus; 20| = 30 + 20 = 50)."
            },
            {
                "num": 2,
                "input": "2\n10 10",
                "output": "0",
                "explanation": "With only 2 stones, the frog must jump directly 1 &rarr; 2.<br>Cost = |10 &minus; 10| = <strong>0</strong>."
            },
            {
                "num": 3,
                "input": "6\n30 10 60 10 60 50",
                "output": "40",
                "explanation": "Optimal path: <strong>Stone 1 &rarr; Stone 3 &rarr; Stone 5 &rarr; Stone 6</strong>.<br>• 1 &rarr; 3: |30 &minus; 60| = 30.<br>• 3 &rarr; 5: |60 &minus; 60| = 0.<br>• 5 &rarr; 6: |60 &minus; 50| = 10.<br>• Total cost = 30 + 0 + 10 = <strong>40</strong>."
            }
        ],
        "dp_guide": """
<h3>Dynamic Programming Breakdown</h3>
<p><strong>State Definition:</strong> Let <code>dp[i]</code> be the minimum cost to reach Stone <em>i</em> (0-indexed: <code>0 &le; i < N</code>).</p>
<p><strong>Base Cases:</strong></p>
<ul>
  <li><code>dp[0] = 0</code> (starting at Stone 0 has 0 cost)</li>
  <li><code>dp[1] = abs(h[1] - h[0])</code> (can only reach Stone 1 from Stone 0)</li>
</ul>
<p><strong>Recurrence Relation:</strong> For any stone <code>i &ge; 2</code>, we can only arrive from stone <code>i - 1</code> or stone <code>i - 2</code>:</p>
<pre>dp[i] = min(
    dp[i - 1] + abs(h[i] - h[i - 1]),
    dp[i - 2] + abs(h[i] - h[i - 2])
)</pre>
<p><strong>Complexity:</strong> Time: O(N) &bull; Space: O(N) or O(1) by storing only the last two values.</p>
"""
    },

    "10sep-contest/B-is-subsequence": {
        "title": "Problem B — Is Subsequence",
        "platform": "LeetCode 392 · Is Subsequence",
        "source_url": "https://leetcode.com/problems/is-subsequence/",
        "time_limit": "2.0s",
        "memory_limit": "1024 MB",
        "category": "Two Pointers / DP Preprocessing",
        "description": """
<p>Given two strings <code>s</code> and <code>t</code>, return <code>true</code> if <code>s</code> is a subsequence of <code>t</code>, or <code>false</code> otherwise.</p>
<p>A <strong>subsequence</strong> of a string is a new string that is formed from the original string by deleting some (can be none) of the characters without disturbing the relative positions of the remaining characters. (i.e., <code>"ace"</code> is a subsequence of <code>"abcde"</code> while <code>"aec"</code> is not).</p>
""",
        "input_format": """
<p>The input consists of two lines:</p>
<pre>s
t</pre>
""",
        "output_format": """
<p>Print <code>true</code> or <code>false</code>.</p>
""",
        "constraints": """
<ul>
  <li>0 &le; |<em>s</em>| &le; 100</li>
  <li>0 &le; |<em>t</em>| &le; 10<sup>4</sup></li>
  <li><code>s</code> and <code>t</code> consist only of lowercase English letters.</li>
</ul>
""",
        "examples": [
            {
                "num": 1,
                "input": "abc\nahbgdc",
                "output": "true",
                "explanation": "Characters 'a', 'b', and 'c' appear in order inside <strong>a</strong>h<strong>b</strong>gd<strong>c</strong> at indices 0, 2, and 5."
            },
            {
                "num": 2,
                "input": "axc\nahbgdc",
                "output": "false",
                "explanation": "'a' is found at index 0, but the next required character 'x' is not present anywhere in <code>t</code>. Result is <code>false</code>."
            }
        ],
        "dp_guide": """
<h3>Algorithmic Insights & Follow-up</h3>
<p><strong>Two-Pointer Greedy Approach:</strong></p>
<p>Maintain two pointers: <code>i</code> for <code>s</code> and <code>j</code> for <code>t</code>. Whenever <code>s[i] == t[j]</code>, advance <code>i</code>. Always advance <code>j</code>. If <code>i == len(s)</code>, every character of <code>s</code> was matched in order.</p>
<p>Time Complexity: O(|t|) &bull; Space Complexity: O(1).</p>
<p><strong>Follow-up (Subsequence DP for 10<sup>9</sup> queries):</strong></p>
<p>If there are many incoming strings <em>s<sub>1</sub>, s<sub>2</sub>, ...</em> tested against the same fixed <em>t</em>, precompute a next-occurrence jump table: <code>nxt[pos][ch]</code> storing the first index &ge; <code>pos</code> where character <code>ch</code> appears. This allows checking any <em>s</em> in O(|s|) time without rescanning <em>t</em>.</p>
"""
    },

    "10sep-contest/C-minimum-path-sum": {
        "title": "Problem C — Minimum Path Sum",
        "platform": "LeetCode 64 · Minimum Path Sum",
        "source_url": "https://leetcode.com/problems/minimum-path-sum/",
        "time_limit": "2.0s",
        "memory_limit": "1024 MB",
        "category": "2D Grid Dynamic Programming",
        "description": """
<p>Given an <em>m</em> &times; <em>n</em> grid filled with non-negative numbers, find a path from top-left (0, 0) to bottom-right (<em>m</em> &minus; 1, <em>n</em> &minus; 1), which minimizes the sum of all numbers along its path.</p>
<p><strong>Note:</strong> You can only move either down or right at any point in time.</p>
""",
        "input_format": """
<p>The input is given from Standard Input in the following format:</p>
<pre>m n
grid[0][0] grid[0][1] ... grid[0][n-1]
...
grid[m-1][0] grid[m-1][1] ... grid[m-1][n-1]</pre>
""",
        "output_format": """
<p>Print a single integer: the minimum path sum from (0, 0) to (m - 1, n - 1).</p>
""",
        "constraints": """
<ul>
  <li>1 &le; <em>m</em>, <em>n</em> &le; 200</li>
  <li>0 &le; <em>grid[i][j]</em> &le; 200</li>
</ul>
""",
        "examples": [
            {
                "num": 1,
                "input": "3 3\n1 3 1\n1 5 1\n4 2 1",
                "output": "7",
                "explanation": "Grid visualization:<br><strong>[1]</strong> &rarr; <strong>[3]</strong> &rarr; <strong>[1]</strong><br>&nbsp;1 &nbsp;&nbsp;&nbsp;&nbsp; 5 &nbsp;&nbsp;&nbsp;&nbsp; &darr;<br>&nbsp;4 &nbsp;&nbsp;&nbsp;&nbsp; 2 &nbsp;&nbsp;&nbsp;&nbsp; <strong>[1]</strong> &rarr; <strong>[1]</strong><br>Optimal Path: 1 &rarr; 3 &rarr; 1 &rarr; 1 &rarr; 1 = <strong>7</strong>."
            },
            {
                "num": 2,
                "input": "2 3\n1 2 3\n4 5 6",
                "output": "12",
                "explanation": "Optimal Path: (0,0) &rarr; (0,1) &rarr; (0,2) &rarr; (1,2) with values 1 + 2 + 3 + 6 = <strong>12</strong>."
            }
        ],
        "dp_guide": """
<h3>Dynamic Programming Breakdown</h3>
<p><strong>State Definition:</strong> Let <code>dp[r][c]</code> be the minimum path sum to reach cell <code>(r, c)</code>.</p>
<p><strong>Base Cases:</strong></p>
<ul>
  <li><code>dp[0][0] = grid[0][0]</code></li>
  <li>Top row (can only move right): <code>dp[0][c] = dp[0][c - 1] + grid[0][c]</code></li>
  <li>Left column (can only move down): <code>dp[r][0] = dp[r - 1][0] + grid[r][0]</code></li>
</ul>
<p><strong>Recurrence Relation:</strong> For any cell <code>(r, c)</code> where <code>r &gt; 0</code> and <code>c &gt; 0</code>:</p>
<pre>dp[r][c] = grid[r][c] + min(dp[r - 1][c], dp[r][c - 1])</pre>
<p><strong>Complexity:</strong> Time: O(m &times; n) &bull; Space: O(n) using a single 1D rolling row array.</p>
"""
    },

    "10sep-contest/D-vacation": {
        "title": "Problem D — Vacation",
        "platform": "AtCoder Educational DP Contest · Task C (dp_c)",
        "source_url": "https://atcoder.jp/contests/dp/tasks/dp_c",
        "time_limit": "2.0s",
        "memory_limit": "1024 MB",
        "category": "Multi-State Dynamic Programming",
        "description": """
<p>Taro's summer vacation starts tomorrow, and he decided to make plans for it now.</p>
<p>The vacation consists of <em>N</em> days. For each <em>i</em> (1 &le; <em>i</em> &le; <em>N</em>), on the <em>i</em>-th day, Taro will choose one of the following activities and do it:</p>
<ul>
  <li><strong>A:</strong> Swim in the sea. Gain <em>a<sub>i</sub></em> points of happiness.</li>
  <li><strong>B:</strong> Catch bugs in the mountains. Gain <em>b<sub>i</sub></em> points of happiness.</li>
  <li><strong>C:</strong> Do homework at home. Gain <em>c<sub>i</sub></em> points of happiness.</li>
</ul>
<p>As Taro gets bored easily, <strong>he cannot do the same activity on two or more consecutive days</strong>.</p>
<p>Find the maximum possible total points of happiness that Taro gains.</p>
""",
        "input_format": """
<p>The input is given from Standard Input in the following format:</p>
<pre>N
a_1 b_1 c_1
a_2 b_2 c_2
...
a_N b_N c_N</pre>
""",
        "output_format": """
<p>Print the maximum possible total points of happiness that Taro can gain.</p>
""",
        "constraints": """
<ul>
  <li>1 &le; <em>N</em> &le; 10<sup>5</sup></li>
  <li>1 &le; <em>a<sub>i</sub></em>, <em>b<sub>i</sub></em>, <em>c<sub>i</sub></em> &le; 10<sup>4</sup></li>
  <li>All values in input are integers.</li>
</ul>
""",
        "examples": [
            {
                "num": 1,
                "input": "3\n10 40 70\n20 50 80\n30 60 90",
                "output": "210",
                "explanation": "• Day 1: Choose C (happiness 70)<br>• Day 2: Choose B (happiness 50) &mdash; cannot repeat C<br>• Day 3: Choose C (happiness 90) &mdash; cannot repeat B<br>Total = 70 + 50 + 90 = <strong>210</strong>."
            },
            {
                "num": 2,
                "input": "1\n100 10 1",
                "output": "100",
                "explanation": "Only 1 day. Taro chooses activity A to gain <strong>100</strong> points."
            },
            {
                "num": 3,
                "input": "7\n6 7 8\n8 8 3\n2 5 2\n7 8 6\n4 6 8\n2 3 4\n7 5 1",
                "output": "46",
                "explanation": "Optimal schedule across 7 days: C (8) &rarr; A (8) &rarr; B (5) &rarr; A (7) &rarr; C (8) &rarr; B (3) &rarr; A (7) = <strong>46</strong>."
            }
        ],
        "dp_guide": """
<h3>Dynamic Programming Breakdown</h3>
<p><strong>State Definition:</strong> Let <code>dp[i][0]</code>, <code>dp[i][1]</code>, <code>dp[i][2]</code> represent the maximum happiness up to day <code>i</code> ending with activity A, B, and C respectively.</p>
<p><strong>Transitions:</strong> Since consecutive activities cannot be identical:</p>
<pre>dp[i][0] = a[i] + max(dp[i - 1][1], dp[i - 1][2])
dp[i][1] = b[i] + max(dp[i - 1][0], dp[i - 1][2])
dp[i][2] = c[i] + max(dp[i - 1][0], dp[i - 1][1])</pre>
<p><strong>Answer:</strong> <code>max(dp[N - 1][0], dp[N - 1][1], dp[N - 1][2])</code></p>
<p><strong>Space Optimization:</strong> We only need the 3 values from the previous day, reducing space to O(1).</p>
<p><strong>Complexity:</strong> Time: O(N) &bull; Space: O(1).</p>
"""
    },

    "17sep-contest/A-alternating-sequences": {
        "title": "Problem A — Alternating Sequences",
        "platform": "SPOJ ALTSEQ · Alternating Sequences",
        "source_url": "https://www.spoj.com/problems/ALTSEQ/",
        "time_limit": "2.0s",
        "memory_limit": "1024 MB",
        "category": "Dynamic Programming (Modified LIS)",
        "description": """
<p>Given an array <em>a</em> of <em>N</em> non-zero integers (<em>a</em><sub>1</sub>, <em>a</em><sub>2</sub>, ..., <em>a<sub>N</sub></em>), find the length of the longest alternating subsequence.</p>
<p>An alternating sequence <em>b</em><sub>1</sub>, <em>b</em><sub>2</sub>, ..., <em>b<sub>k</sub></em> (<em>k</em> &ge; 1) must satisfy two conditions:</p>
<ol>
  <li><strong>Strictly increasing absolute values:</strong> |<em>b</em><sub>1</sub>| &lt; |<em>b</em><sub>2</sub>| &lt; |<em>b</em><sub>3</sub>| &lt; ... &lt; |<em>b<sub>k</sub></em>|</li>
  <li><strong>Strictly alternating signs:</strong> Adjacent elements must have opposite signs. That is, if <em>b</em><sub>1</sub> &gt; 0, then <em>b</em><sub>2</sub> &lt; 0, <em>b</em><sub>3</sub> &gt; 0, and so on (or vice versa).</li>
</ol>
""",
        "input_format": """
<p>The first line contains a single integer <em>N</em>. The second line contains <em>N</em> space-separated integers <em>a</em><sub>1</sub>, <em>a</em><sub>2</sub>, ..., <em>a<sub>N</sub></em>.</p>
<pre>N
a_1 a_2 ... a_N</pre>
""",
        "output_format": """
<p>Print a single integer: the length of the longest alternating subsequence.</p>
""",
        "constraints": """
<ul>
  <li>1 &le; <em>N</em> &le; 5000</li>
  <li>|<em>a<sub>i</sub></em>| &le; 10<sup>9</sup></li>
  <li><em>a<sub>i</sub></em> &ne; 0</li>
</ul>
""",
        "examples": [
            {
                "num": 1,
                "input": "8\n1 2 -2 -3 5 -7 -8 10",
                "output": "5",
                "explanation": "Consider the subsequence <code>[1, -2, 5, -7, 10]</code>:<br>• Magnitudes: |1| = 1 &lt; |-2| = 2 &lt; |5| = 5 &lt; |-7| = 7 &lt; |10| = 10 (strictly increasing).<br>• Signs: +1, -2, +5, -7, +10 (alternates: positive, negative, positive, negative, positive).<br>Length = <strong>5</strong>. (Another valid candidate of length 5 is <code>[2, -3, 5, -7, 10]</code>)."
            }
        ],
        "dp_guide": """
<h3>Dynamic Programming Breakdown</h3>
<p>This problem is a variant of the classic <strong>Longest Increasing Subsequence (LIS)</strong> problem:</p>
<p><strong>State Definition:</strong> Let <code>dp[i]</code> be the length of the longest alternating subsequence ending at index <code>i</code>.</p>
<p><strong>Base Case:</strong> Initialize <code>dp[i] = 1</code> for all <code>i</code> (each individual element forms a valid sequence of length 1).</p>
<p><strong>Transitions:</strong> For each index <code>i</code> from 0 to <code>N - 1</code>, examine every preceding index <code>j &lt; i</code>:</p>
<pre>if abs(a[j]) < abs(a[i]) and ((a[j] > 0 and a[i] < 0) or (a[j] < 0 and a[i] > 0)):
    dp[i] = max(dp[i], dp[j] + 1)</pre>
<p><strong>Complexity:</strong> Time: O(N<sup>2</sup>) &bull; Space: O(N). With N = 5000, 2.5 &times; 10<sup>7</sup> iterations comfortably executes within the 2.0s limit.</p>
"""
    },

    "17sep-contest/B-philosophers-stone": {
        "title": "Problem B — Philosophers Stone",
        "platform": "SPOJ BYTESM2 · Philosophers Stone",
        "source_url": "https://www.spoj.com/problems/BYTESM2/",
        "time_limit": "2.0s",
        "memory_limit": "1024 MB",
        "category": "Grid Dynamic Programming (Max Path)",
        "description": """
<p>One of the secret chambers in Hogwarts is filled with philosopher's stones. The chamber floor is represented as a grid of size <em>h</em> &times; <em>w</em> (<em>h</em> rows and <em>w</em> columns). Each tile contains a specific number of stones.</p>
<p>Harry Potter starts at <strong>any tile on the first row</strong> (row 0). From a tile (<em>r</em>, <em>c</em>), he can only move to one of three tiles in the row directly below:</p>
<ul>
  <li>Directly below: (<em>r</em> + 1, <em>c</em>)</li>
  <li>Diagonally down-left: (<em>r</em> + 1, <em>c</em> &minus; 1) [if <em>c</em> &gt; 0]</li>
  <li>Diagonally down-right: (<em>r</em> + 1, <em>c</em> + 1) [if <em>c</em> &lt; <em>w</em> &minus; 1]</li>
</ul>
<p>Find the maximum total number of stones Harry can collect by the time he reaches the last row (row <em>h</em> &minus; 1).</p>
""",
        "input_format": """
<p>The first line contains the number of test cases <em>T</em>. For each test case, the first line contains two integers <em>h</em> and <em>w</em>. Then <em>h</em> &times; <em>w</em> integers follow representing the stone counts row by row.</p>
<pre>T
h w
row 0 values...
...
row h-1 values...</pre>
""",
        "output_format": """
<p>For each test case, print the maximum number of stones Harry can collect on a new line.</p>
""",
        "constraints": """
<ul>
  <li>1 &le; <em>T</em> &le; 100</li>
  <li>1 &le; <em>h</em>, <em>w</em> &le; 100</li>
  <li>Tile stone values: 1 &le; <em>val</em> &le; 100</li>
</ul>
""",
        "examples": [
            {
                "num": 1,
                "input": "1\n6 5\n3 1 7 4 2\n2 1 3 1 1\n1 2 2 1 8\n2 2 1 5 3\n2 1 4 4 4\n5 2 7 5 1",
                "output": "32",
                "explanation": "Grid with optimal path highlighted:<br>Row 0: 3 &nbsp; 1 &nbsp; <strong>[7]</strong> &nbsp; 4 &nbsp; 2 &rarr; pick 7<br>Row 1: 2 &nbsp; 1 &nbsp; 3 &nbsp; <strong>[1]</strong> &nbsp; 1 &rarr; pick 1 (Sum = 8)<br>Row 2: 1 &nbsp; 2 &nbsp; 2 &nbsp; 1 &nbsp; <strong>[8]</strong> &rarr; pick 8 (Sum = 16)<br>Row 3: 2 &nbsp; 2 &nbsp; 1 &nbsp; <strong>[5]</strong> &nbsp; 3 &rarr; pick 5 (Sum = 21)<br>Row 4: 2 &nbsp; 1 &nbsp; <strong>[4]</strong> &nbsp; 4 &nbsp; 4 &rarr; pick 4 (Sum = 25)<br>Row 5: 5 &nbsp; 2 &nbsp; <strong>[7]</strong> &nbsp; 5 &nbsp; 1 &rarr; pick 7 (Sum = <strong>32</strong>)."
            }
        ],
        "dp_guide": """
<h3>Dynamic Programming Breakdown</h3>
<p><strong>State Definition:</strong> Let <code>dp[r][c]</code> be the maximum stones collected upon reaching tile <code>(r, c)</code>.</p>
<p><strong>Base Case:</strong> For row 0: <code>dp[0][c] = grid[0][c]</code> for all <code>0 &le; c &lt; w</code>.</p>
<p><strong>Transitions:</strong> For each row <code>r &ge; 1</code> and column <code>c</code>:</p>
<pre>max_prev = dp[r - 1][c]
if c > 0:
    max_prev = max(max_prev, dp[r - 1][c - 1])
if c < w - 1:
    max_prev = max(max_prev, dp[r - 1][c + 1])
dp[r][c] = grid[r][c] + max_prev</pre>
<p><strong>Answer:</strong> <code>max(dp[h - 1][c])</code> across all columns <code>0 &le; c &lt; w</code>.</p>
<p><strong>Complexity:</strong> Time: O(T &times; h &times; w) &bull; Space: O(w) using a rolling row array.</p>
"""
    },

    "17sep-contest/C-alphacode": {
        "title": "Problem C — Alphacode",
        "platform": "SPOJ ACODE · Alphacode",
        "source_url": "https://www.spoj.com/problems/ACODE/",
        "time_limit": "2.0s",
        "memory_limit": "1024 MB",
        "category": "Dynamic Programming (Counting / Decodings)",
        "description": """
<p>Alice and Bob communicate using a numerical cipher where the letters of the English alphabet 'A' through 'Z' are encoded as numbers 1 through 26:</p>
<p>'A' &rarr; 1, 'B' &rarr; 2, ..., 'I' &rarr; 9, 'J' &rarr; 10, ..., 'Z' &rarr; 26.</p>
<p>Given an encoded string of digits, calculate the total number of possible original messages that could have produced this encoding.</p>
<p>The input consists of multiple test cases. The input is terminated by a single line containing <code>0</code>.</p>
""",
        "input_format": """
<p>Each test case is given on a separate line containing a non-empty string of digits of length up to 5000. The last line of the input contains <code>0</code>, which should not be processed.</p>
<pre>25114
1111111111
3333333333
0</pre>
""",
        "output_format": """
<p>For each test case, output the number of possible decodings on a new line.</p>
""",
        "constraints": """
<ul>
  <li>String length up to 5000 digits.</li>
  <li>Answer fits within a 64-bit integer.</li>
  <li>Input is terminated by <code>0</code>.</li>
</ul>
""",
        "examples": [
            {
                "num": 1,
                "input": "25114\n1111111111\n3333333333\n0",
                "output": "6\n89\n1",
                "explanation": "• For <code>25114</code>, the 6 valid decodings are:<br>&nbsp;&nbsp;1. <strong>2 5 1 1 4</strong> &rarr; BEAAD<br>&nbsp;&nbsp;2. <strong>2 5 1 14</strong> &rarr; BEAN<br>&nbsp;&nbsp;3. <strong>2 5 11 4</strong> &rarr; BEKD<br>&nbsp;&nbsp;4. <strong>25 1 1 4</strong> &rarr; YAAD<br>&nbsp;&nbsp;5. <strong>25 1 14</strong> &rarr; YAN<br>&nbsp;&nbsp;6. <strong>25 11 4</strong> &rarr; YKD<br>• For <code>1111111111</code> (ten 1's): Decodings correspond to Fibonacci F<sub>11</sub> = <strong>89</strong>.<br>• For <code>3333333333</code>: No double-digit '33' is &le; 26, so only 1 decoding (CCCCCCCCCC) is possible = <strong>1</strong>."
            }
        ],
        "dp_guide": """
<h3>Dynamic Programming Breakdown</h3>
<p><strong>State Definition:</strong> Let <code>dp[i]</code> be the number of decodings for the prefix of length <code>i</code>.</p>
<p><strong>Base Cases:</strong> <code>dp[0] = 1</code>, and <code>dp[1] = 1</code> (assuming <code>s[0] &ne; '0'</code>).</p>
<p><strong>Transitions:</strong> For each position <code>i &ge; 2</code>:</p>
<ul>
  <li><strong>Single digit:</strong> If <code>s[i - 1] &ne; '0'</code>, the digit forms a valid letter: <code>dp[i] += dp[i - 1]</code></li>
  <li><strong>Two digits:</strong> If the two-digit number <code>val = int(s[i-2:i])</code> satisfies <code>10 &le; val &le; 26</code>: <code>dp[i] += dp[i - 2]</code></li>
</ul>
<p><strong>Zero Handling:</strong> Note that '10' and '20' are valid double digits, but a standalone '0' cannot be parsed. If both single and double digit transitions are invalid, <code>dp[i]</code> remains 0.</p>
<p><strong>Complexity:</strong> Time: O(|S|) &bull; Space: O(1) keeping only the last two DP states.</p>
"""
    },

    "17sep-contest/D-aibohphobia": {
        "title": "Problem D — Aibohphobia",
        "platform": "SPOJ AIBOHP · Aibohphobia",
        "source_url": "https://www.spoj.com/problems/AIBOHP/",
        "time_limit": "2.0s",
        "memory_limit": "1024 MB",
        "category": "Dynamic Programming (LCS / Palindromic Subsequence)",
        "description": """
<p>BuggyD suffers from a severe psychological condition called <strong>aibohphobia</strong> &mdash; the irrational fear of palindromes (words that read the same backwards and forwards). Notice that the name 'aibohphobia' itself is a palindrome!</p>
<p>To help overcome this fear, he wants to transform any given word into a palindrome by inserting characters. You can insert characters at any position (at the beginning, middle, or end).</p>
<p>Given a string <em>S</em>, find the <strong>minimum number of character insertions</strong> required to make it a palindrome.</p>
""",
        "input_format": """
<p>The first line contains an integer <em>T</em>, the number of test cases. Each of the next <em>T</em> lines contains a single string <em>S</em>.</p>
<pre>T
S_1
...
S_T</pre>
""",
        "output_format": """
<p>For each test case, print the minimum number of insertions on a new line.</p>
""",
        "constraints": """
<ul>
  <li>1 &le; <em>T</em> &le; 100</li>
  <li>1 &le; |<em>S</em>| &le; 6100</li>
  <li><em>S</em> consists of lowercase English letters.</li>
</ul>
""",
        "examples": [
            {
                "num": 1,
                "input": "1\nfft",
                "output": "1",
                "explanation": "Given string: <code>\"fft\"</code>.<br>• Insert 't' at the beginning &rarr; <code>\"tfft\"</code> (a palindrome with <strong>1</strong> insertion).<br>• Alternatively, insert 't' after the first 'f' &rarr; <code>\"fttf\"</code> (also 1 insertion).<br>No 0-insertion solution exists since 'fft' is not a palindrome. Minimum insertions = <strong>1</strong>."
            }
        ],
        "dp_guide": """
<h3>Dynamic Programming Breakdown</h3>
<p><strong>Fundamental Relationship:</strong></p>
<p>The minimum number of insertions to make <em>S</em> a palindrome is equal to:</p>
<pre>Min Insertions = |S| - LPS(S)</pre>
<p>Where <code>LPS(S)</code> is the <strong>Longest Palindromic Subsequence</strong> of <em>S</em>. Furthermore, <code>LPS(S)</code> is identical to the <strong>Longest Common Subsequence (LCS)</strong> between <em>S</em> and its reverse <em>S<sup>rev</sup></em>:</p>
<pre>LPS(S) = LCS(S, S[::-1])</pre>
<p><strong>Space Optimization:</strong> Since |S| &le; 6100, allocating a full 6100 &times; 6100 integer matrix requires ~150 MB and risks Memory Limit Exceeded (MLE). By maintaining only two rows (current and previous) of length |S|, memory drops to under 50 KB.</p>
<p><strong>Complexity:</strong> Time: O(|S|<sup>2</sup>) &bull; Space: O(|S|).</p>
"""
    }
}

def generate_html(pdata):
    copy_svg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>'
    examples_html = ""
    for ex in pdata["examples"]:
        examples_html += f"""
<div class="example-wrapper">
  <div class="example-grid">
    <div class="io-card">
      <div class="io-card-header">
        <span class="io-card-title">Example {ex['num']} Input</span>
        <button type="button" class="btn-copy-sample" onclick="copyPre(this)">{copy_svg}<span>Copy</span></button>
      </div>
      <pre>{ex['input']}</pre>
    </div>
    <div class="io-card">
      <div class="io-card-header">
        <span class="io-card-title">Example {ex['num']} Output</span>
        <button type="button" class="btn-copy-sample" onclick="copyPre(this)">{copy_svg}<span>Copy</span></button>
      </div>
      <pre>{ex['output']}</pre>
    </div>
  </div>
  <div class="example-explanation">
    <strong>Explanation:</strong> {ex['explanation']}
  </div>
</div>
"""

    platform_short = pdata["platform"].split()[0]
    category_short = pdata["category"].replace("Dynamic Programming", "DP")
    mem_compact = pdata["memory_limit"].replace(" ", "")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <title>{pdata['title']}</title>
  {CSS}
</head>
<body>
  <div class="statement-container">
    <div class="meta-chips">
      <span class="meta-chip">{platform_short}</span>
      <span class="meta-chip">{category_short}</span>
      <span class="meta-chip">{pdata['time_limit']}</span>
      <span class="meta-chip">{mem_compact}</span>
    </div>

    <div class="title-row">
      <h1>{pdata['title']}</h1>
      <a class="source-link" href="{pdata['source_url']}" target="_blank" rel="noopener noreferrer">
        <span>View on {platform_short}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
      </a>
    </div>

    <div class="section-block">
      <h2>Problem Statement</h2>
      {pdata['description']}
    </div>

    <div class="section-block">
      <h2>Input Format</h2>
      {pdata['input_format']}
    </div>

    <div class="section-block">
      <h2>Output Format</h2>
      {pdata['output_format']}
    </div>

    <div class="section-block">
      <h2>Constraints</h2>
      {pdata['constraints']}
    </div>

    <div class="section-block">
      <h2>Examples</h2>
      {examples_html}
    </div>

    <div class="dp-analysis-card">
      {pdata['dp_guide']}
    </div>
  </div>
  <script>
    function copyPre(btn) {{
      var card = btn.closest('.io-card');
      var pre = card ? card.querySelector('pre') : null;
      if (!pre || !navigator.clipboard) return;
      navigator.clipboard.writeText(pre.textContent).then(function() {{
        var label = btn.querySelector('span');
        if (label) label.textContent = 'Copied';
        btn.classList.add('copied');
        setTimeout(function() {{
          if (label) label.textContent = 'Copy';
          btn.classList.remove('copied');
        }}, 1400);
      }});
    }}
  </script>
</body>
</html>
"""
    return html

def generate_markdown(pdata):
    md = f"""# {pdata['title']}

**Platform / Source:** [{pdata['platform']}]({pdata['source_url']})  
**Time Limit:** {pdata['time_limit']} • **Memory Limit:** {pdata['memory_limit']}  
**Category:** {pdata['category']}

---

## Problem Statement

{pdata['description'].replace('<p>', '').replace('</p>', '\n\n').replace('<em>', '*').replace('</em>', '*').replace('<strong>', '**').replace('</strong>', '**').replace('&le;', '<=').replace('&ge;', '>=').replace('&minus;', '-').replace('<ul>', '').replace('</ul>', '').replace('<li>', '- ').replace('</li>', '')}

## Input Format

{pdata['input_format'].replace('<p>', '').replace('</p>', '\n\n').replace('<pre>', '```\n').replace('</pre>', '\n```')}

## Output Format

{pdata['output_format'].replace('<p>', '').replace('</p>', '\n\n').replace('<code>', '`').replace('</code>', '`')}

## Constraints

{pdata['constraints'].replace('<ul>', '').replace('</ul>', '').replace('<li>', '- ').replace('</li>', '').replace('&le;', '<=').replace('<em>', '').replace('</em>', '').replace('<sup>', '^').replace('</sup>', '')}

## Examples & Step-by-Step Explanations

"""
    for ex in pdata["examples"]:
        clean_exp = ex['explanation'].replace('<br>', '\n').replace('<strong>', '**').replace('</strong>', '**').replace('&rarr;', '->').replace('&minus;', '-').replace('&nbsp;', ' ')
        md += f"""### Example {ex['num']}

**Input:**
```
{ex['input']}
```

**Output:**
```
{ex['output']}
```

**Explanation:**  
{clean_exp}

---
"""

    md += f"""## Dynamic Programming Analysis

{pdata['dp_guide'].replace('<h3>', '### ').replace('</h3>', '\n').replace('<p>', '').replace('</p>', '\n\n').replace('<code>', '`').replace('</code>', '`').replace('<pre>', '```\n').replace('</pre>', '\n```').replace('<em>', '*').replace('</em>', '*').replace('&ge;', '>=').replace('&lt;', '<').replace('&times;', 'x').replace('<ul>', '').replace('</ul>', '').replace('<li>', '- ').replace('</li>', '')}
"""
    return md

for rel_path, data in PROBLEMS.items():
    prob_dir = BASE_DIR / rel_path
    prob_dir.mkdir(parents=True, exist_ok=True)
    
    html_content = generate_html(data)
    md_content = generate_markdown(data)
    
    html_file = prob_dir / "statement.html"
    md_file = prob_dir / "problem.md"
    
    html_file.write_text(html_content, encoding="utf-8")
    md_file.write_text(md_content, encoding="utf-8")
    print(f"Generated {html_file} and {md_file} ({len(html_content)} bytes)")

print("All 8 problem statements successfully populated!")

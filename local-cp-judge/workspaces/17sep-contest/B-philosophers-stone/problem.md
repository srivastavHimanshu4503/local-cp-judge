# Problem B — Philosophers Stone

**Platform / Source:** [SPOJ BYTESM2 · Philosophers Stone](https://www.spoj.com/problems/BYTESM2/)  
**Time Limit:** 2.0s • **Memory Limit:** 1024 MB  
**Category:** Grid Dynamic Programming (Max Path)

---

## Problem Statement


One of the secret chambers in Hogwarts is filled with philosopher's stones. The chamber floor is represented as a grid of size *h* &times; *w* (*h* rows and *w* columns). Each tile contains a specific number of stones.


Harry Potter starts at **any tile on the first row** (row 0). From a tile (*r*, *c*), he can only move to one of three tiles in the row directly below:



  - Directly below: (*r* + 1, *c*)
  - Diagonally down-left: (*r* + 1, *c* - 1) [if *c* &gt; 0]
  - Diagonally down-right: (*r* + 1, *c* + 1) [if *c* &lt; *w* - 1]

Find the maximum total number of stones Harry can collect by the time he reaches the last row (row *h* - 1).




## Input Format


The first line contains the number of test cases <em>T</em>. For each test case, the first line contains two integers <em>h</em> and <em>w</em>. Then <em>h</em> &times; <em>w</em> integers follow representing the stone counts row by row.


```
T
h w
row 0 values...
...
row h-1 values...
```


## Output Format


For each test case, print the maximum number of stones Harry can collect on a new line.




## Constraints



  - 1 <= T <= 100
  - 1 <= h, w <= 100
  - Tile stone values: 1 <= val <= 100



## Examples & Step-by-Step Explanations

### Example 1

**Input:**
```
1
6 5
3 1 7 4 2
2 1 3 1 1
1 2 2 1 8
2 2 1 5 3
2 1 4 4 4
5 2 7 5 1
```

**Output:**
```
32
```

**Explanation:**  
Grid with optimal path highlighted:
Row 0: 3   1   **[7]**   4   2 -> pick 7
Row 1: 2   1   3   **[1]**   1 -> pick 1 (Sum = 8)
Row 2: 1   2   2   1   **[8]** -> pick 8 (Sum = 16)
Row 3: 2   2   1   **[5]**   3 -> pick 5 (Sum = 21)
Row 4: 2   1   **[4]**   4   4 -> pick 4 (Sum = 25)
Row 5: 5   2   **[7]**   5   1 -> pick 7 (Sum = **32**).

---
## Dynamic Programming Analysis


### Dynamic Programming Breakdown

<strong>State Definition:</strong> Let `dp[r][c]` be the maximum stones collected upon reaching tile `(r, c)`.


<strong>Base Case:</strong> For row 0: `dp[0][c] = grid[0][c]` for all `0 &le; c < w`.


<strong>Transitions:</strong> For each row `r >= 1` and column `c`:


```
max_prev = dp[r - 1][c]
if c > 0:
    max_prev = max(max_prev, dp[r - 1][c - 1])
if c < w - 1:
    max_prev = max(max_prev, dp[r - 1][c + 1])
dp[r][c] = grid[r][c] + max_prev
```
<strong>Answer:</strong> `max(dp[h - 1][c])` across all columns `0 &le; c < w`.


<strong>Complexity:</strong> Time: O(T x h x w) &bull; Space: O(w) using a rolling row array.




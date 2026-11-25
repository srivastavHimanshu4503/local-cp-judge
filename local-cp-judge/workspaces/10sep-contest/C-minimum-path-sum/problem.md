# Problem C — Minimum Path Sum

**Platform / Source:** [LeetCode 64 · Minimum Path Sum](https://leetcode.com/problems/minimum-path-sum/)  
**Time Limit:** 2.0s • **Memory Limit:** 1024 MB  
**Category:** 2D Grid Dynamic Programming

---

## Problem Statement


Given an *m* &times; *n* grid filled with non-negative numbers, find a path from top-left (0, 0) to bottom-right (*m* - 1, *n* - 1), which minimizes the sum of all numbers along its path.


**Note:** You can only move either down or right at any point in time.




## Input Format


The input is given from Standard Input in the following format:


```
m n
grid[0][0] grid[0][1] ... grid[0][n-1]
...
grid[m-1][0] grid[m-1][1] ... grid[m-1][n-1]
```


## Output Format


Print a single integer: the minimum path sum from (0, 0) to (m - 1, n - 1).




## Constraints



  - 1 <= m, n <= 200
  - 0 <= grid[i][j] <= 200



## Examples & Step-by-Step Explanations

### Example 1

**Input:**
```
3 3
1 3 1
1 5 1
4 2 1
```

**Output:**
```
7
```

**Explanation:**  
Grid visualization:
**[1]** -> **[3]** -> **[1]**
 1      5      &darr;
 4      2      **[1]** -> **[1]**
Optimal Path: 1 -> 3 -> 1 -> 1 -> 1 = **7**.

---
### Example 2

**Input:**
```
2 3
1 2 3
4 5 6
```

**Output:**
```
12
```

**Explanation:**  
Optimal Path: (0,0) -> (0,1) -> (0,2) -> (1,2) with values 1 + 2 + 3 + 6 = **12**.

---
## Dynamic Programming Analysis


### Dynamic Programming Breakdown

<strong>State Definition:</strong> Let `dp[r][c]` be the minimum path sum to reach cell `(r, c)`.


<strong>Base Cases:</strong>



  - `dp[0][0] = grid[0][0]`
  - Top row (can only move right): `dp[0][c] = dp[0][c - 1] + grid[0][c]`
  - Left column (can only move down): `dp[r][0] = dp[r - 1][0] + grid[r][0]`

<strong>Recurrence Relation:</strong> For any cell `(r, c)` where `r &gt; 0` and `c &gt; 0`:


```
dp[r][c] = grid[r][c] + min(dp[r - 1][c], dp[r][c - 1])
```
<strong>Complexity:</strong> Time: O(m x n) &bull; Space: O(n) using a single 1D rolling row array.




# Problem A — Rabbit / Frog 1

**Platform / Source:** [AtCoder Educational DP Contest · Task A (dp_a)](https://atcoder.jp/contests/dp/tasks/dp_a)  
**Time Limit:** 2.0s • **Memory Limit:** 1024 MB  
**Category:** 1D Dynamic Programming

---

## Problem Statement


There are *N* stones numbered 1, 2, ..., *N*. For each *i* (1 <= *i* <= *N*), the height of Stone *i* is *h<sub>i</sub>*.


A frog is initially on Stone 1. It will repeat the following action some number of times to reach Stone *N*:



  - If the frog is currently on Stone *i*, jump to Stone *i + 1* or Stone *i + 2*. Here, a cost of |*h<sub>i</sub>* - *h<sub>j</sub>*| is incurred, where *j* is the stone to land on.

Find the minimum possible total cost incurred before the frog reaches Stone *N*.




## Input Format


The input is given from Standard Input in the following format:


```
N
h_1 h_2 ... h_N
```


## Output Format


Print the minimum possible total cost incurred.




## Constraints



  - 2 <= N <= 10^5
  - 1 <= h<sub>i</sub> <= 10^4
  - All values in input are integers.



## Examples & Step-by-Step Explanations

### Example 1

**Input:**
```
4
10 30 40 20
```

**Output:**
```
30
```

**Explanation:**  
Follow the path: **Stone 1 -> Stone 2 -> Stone 4**.
• Jump 1 -> 2: cost = |10 - 30| = 20.
• Jump 2 -> 4: cost = |30 - 20| = 10.
• Total cost = 20 + 10 = **30**.
(Taking 1 -> 3 -> 4 would cost |10 - 40| + |40 - 20| = 30 + 20 = 50).

---
### Example 2

**Input:**
```
2
10 10
```

**Output:**
```
0
```

**Explanation:**  
With only 2 stones, the frog must jump directly 1 -> 2.
Cost = |10 - 10| = **0**.

---
### Example 3

**Input:**
```
6
30 10 60 10 60 50
```

**Output:**
```
40
```

**Explanation:**  
Optimal path: **Stone 1 -> Stone 3 -> Stone 5 -> Stone 6**.
• 1 -> 3: |30 - 60| = 30.
• 3 -> 5: |60 - 60| = 0.
• 5 -> 6: |60 - 50| = 10.
• Total cost = 30 + 0 + 10 = **40**.

---
## Dynamic Programming Analysis


### Dynamic Programming Breakdown

<strong>State Definition:</strong> Let `dp[i]` be the minimum cost to reach Stone *i* (0-indexed: `0 &le; i < N`).


<strong>Base Cases:</strong>



  - `dp[0] = 0` (starting at Stone 0 has 0 cost)
  - `dp[1] = abs(h[1] - h[0])` (can only reach Stone 1 from Stone 0)

<strong>Recurrence Relation:</strong> For any stone `i >= 2`, we can only arrive from stone `i - 1` or stone `i - 2`:


```
dp[i] = min(
    dp[i - 1] + abs(h[i] - h[i - 1]),
    dp[i - 2] + abs(h[i] - h[i - 2])
)
```
<strong>Complexity:</strong> Time: O(N) &bull; Space: O(N) or O(1) by storing only the last two values.




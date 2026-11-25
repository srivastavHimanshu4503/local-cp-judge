# Problem D — Vacation

**Platform / Source:** [AtCoder Educational DP Contest · Task C (dp_c)](https://atcoder.jp/contests/dp/tasks/dp_c)  
**Time Limit:** 2.0s • **Memory Limit:** 1024 MB  
**Category:** Multi-State Dynamic Programming

---

## Problem Statement


Taro's summer vacation starts tomorrow, and he decided to make plans for it now.


The vacation consists of *N* days. For each *i* (1 <= *i* <= *N*), on the *i*-th day, Taro will choose one of the following activities and do it:



  - **A:** Swim in the sea. Gain *a<sub>i</sub>* points of happiness.
  - **B:** Catch bugs in the mountains. Gain *b<sub>i</sub>* points of happiness.
  - **C:** Do homework at home. Gain *c<sub>i</sub>* points of happiness.

As Taro gets bored easily, **he cannot do the same activity on two or more consecutive days**.


Find the maximum possible total points of happiness that Taro gains.




## Input Format


The input is given from Standard Input in the following format:


```
N
a_1 b_1 c_1
a_2 b_2 c_2
...
a_N b_N c_N
```


## Output Format


Print the maximum possible total points of happiness that Taro can gain.




## Constraints



  - 1 <= N <= 10^5
  - 1 <= a<sub>i</sub>, b<sub>i</sub>, c<sub>i</sub> <= 10^4
  - All values in input are integers.



## Examples & Step-by-Step Explanations

### Example 1

**Input:**
```
3
10 40 70
20 50 80
30 60 90
```

**Output:**
```
210
```

**Explanation:**  
• Day 1: Choose C (happiness 70)
• Day 2: Choose B (happiness 50) &mdash; cannot repeat C
• Day 3: Choose C (happiness 90) &mdash; cannot repeat B
Total = 70 + 50 + 90 = **210**.

---
### Example 2

**Input:**
```
1
100 10 1
```

**Output:**
```
100
```

**Explanation:**  
Only 1 day. Taro chooses activity A to gain **100** points.

---
### Example 3

**Input:**
```
7
6 7 8
8 8 3
2 5 2
7 8 6
4 6 8
2 3 4
7 5 1
```

**Output:**
```
46
```

**Explanation:**  
Optimal schedule across 7 days: C (8) -> A (8) -> B (5) -> A (7) -> C (8) -> B (3) -> A (7) = **46**.

---
## Dynamic Programming Analysis


### Dynamic Programming Breakdown

<strong>State Definition:</strong> Let `dp[i][0]`, `dp[i][1]`, `dp[i][2]` represent the maximum happiness up to day `i` ending with activity A, B, and C respectively.


<strong>Transitions:</strong> Since consecutive activities cannot be identical:


```
dp[i][0] = a[i] + max(dp[i - 1][1], dp[i - 1][2])
dp[i][1] = b[i] + max(dp[i - 1][0], dp[i - 1][2])
dp[i][2] = c[i] + max(dp[i - 1][0], dp[i - 1][1])
```
<strong>Answer:</strong> `max(dp[N - 1][0], dp[N - 1][1], dp[N - 1][2])`


<strong>Space Optimization:</strong> We only need the 3 values from the previous day, reducing space to O(1).


<strong>Complexity:</strong> Time: O(N) &bull; Space: O(1).




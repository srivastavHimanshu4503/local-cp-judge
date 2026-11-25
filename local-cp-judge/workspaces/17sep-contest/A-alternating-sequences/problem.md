# Problem A — Alternating Sequences

**Platform / Source:** [SPOJ ALTSEQ · Alternating Sequences](https://www.spoj.com/problems/ALTSEQ/)  
**Time Limit:** 2.0s • **Memory Limit:** 1024 MB  
**Category:** Dynamic Programming (Modified LIS)

---

## Problem Statement


Given an array *a* of *N* non-zero integers (*a*<sub>1</sub>, *a*<sub>2</sub>, ..., *a<sub>N</sub>*), find the length of the longest alternating subsequence.


An alternating sequence *b*<sub>1</sub>, *b*<sub>2</sub>, ..., *b<sub>k</sub>* (*k* >= 1) must satisfy two conditions:


<ol>
  - **Strictly increasing absolute values:** |*b*<sub>1</sub>| &lt; |*b*<sub>2</sub>| &lt; |*b*<sub>3</sub>| &lt; ... &lt; |*b<sub>k</sub>*|
  - **Strictly alternating signs:** Adjacent elements must have opposite signs. That is, if *b*<sub>1</sub> &gt; 0, then *b*<sub>2</sub> &lt; 0, *b*<sub>3</sub> &gt; 0, and so on (or vice versa).
</ol>


## Input Format


The first line contains a single integer <em>N</em>. The second line contains <em>N</em> space-separated integers <em>a</em><sub>1</sub>, <em>a</em><sub>2</sub>, ..., <em>a<sub>N</sub></em>.


```
N
a_1 a_2 ... a_N
```


## Output Format


Print a single integer: the length of the longest alternating subsequence.




## Constraints



  - 1 <= N <= 5000
  - |a<sub>i</sub>| <= 10^9
  - a<sub>i</sub> &ne; 0



## Examples & Step-by-Step Explanations

### Example 1

**Input:**
```
8
1 2 -2 -3 5 -7 -8 10
```

**Output:**
```
5
```

**Explanation:**  
Consider the subsequence <code>[1, -2, 5, -7, 10]</code>:
• Magnitudes: |1| = 1 &lt; |-2| = 2 &lt; |5| = 5 &lt; |-7| = 7 &lt; |10| = 10 (strictly increasing).
• Signs: +1, -2, +5, -7, +10 (alternates: positive, negative, positive, negative, positive).
Length = **5**. (Another valid candidate of length 5 is <code>[2, -3, 5, -7, 10]</code>).

---
## Dynamic Programming Analysis


### Dynamic Programming Breakdown

This problem is a variant of the classic <strong>Longest Increasing Subsequence (LIS)</strong> problem:


<strong>State Definition:</strong> Let `dp[i]` be the length of the longest alternating subsequence ending at index `i`.


<strong>Base Case:</strong> Initialize `dp[i] = 1` for all `i` (each individual element forms a valid sequence of length 1).


<strong>Transitions:</strong> For each index `i` from 0 to `N - 1`, examine every preceding index `j < i`:


```
if abs(a[j]) < abs(a[i]) and ((a[j] > 0 and a[i] < 0) or (a[j] < 0 and a[i] > 0)):
    dp[i] = max(dp[i], dp[j] + 1)
```
<strong>Complexity:</strong> Time: O(N<sup>2</sup>) &bull; Space: O(N). With N = 5000, 2.5 x 10<sup>7</sup> iterations comfortably executes within the 2.0s limit.




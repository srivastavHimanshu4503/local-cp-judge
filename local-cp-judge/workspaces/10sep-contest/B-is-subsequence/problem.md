# Problem B — Is Subsequence

**Platform / Source:** [LeetCode 392 · Is Subsequence](https://leetcode.com/problems/is-subsequence/)  
**Time Limit:** 2.0s • **Memory Limit:** 1024 MB  
**Category:** Two Pointers / DP Preprocessing

---

## Problem Statement


Given two strings <code>s</code> and <code>t</code>, return <code>true</code> if <code>s</code> is a subsequence of <code>t</code>, or <code>false</code> otherwise.


A **subsequence** of a string is a new string that is formed from the original string by deleting some (can be none) of the characters without disturbing the relative positions of the remaining characters. (i.e., <code>"ace"</code> is a subsequence of <code>"abcde"</code> while <code>"aec"</code> is not).




## Input Format


The input consists of two lines:


```
s
t
```


## Output Format


Print `true` or `false`.




## Constraints



  - 0 <= |s| <= 100
  - 0 <= |t| <= 10^4
  - <code>s</code> and <code>t</code> consist only of lowercase English letters.



## Examples & Step-by-Step Explanations

### Example 1

**Input:**
```
abc
ahbgdc
```

**Output:**
```
true
```

**Explanation:**  
Characters 'a', 'b', and 'c' appear in order inside **a**h**b**gd**c** at indices 0, 2, and 5.

---
### Example 2

**Input:**
```
axc
ahbgdc
```

**Output:**
```
false
```

**Explanation:**  
'a' is found at index 0, but the next required character 'x' is not present anywhere in <code>t</code>. Result is <code>false</code>.

---
## Dynamic Programming Analysis


### Algorithmic Insights & Follow-up

<strong>Two-Pointer Greedy Approach:</strong>


Maintain two pointers: `i` for `s` and `j` for `t`. Whenever `s[i] == t[j]`, advance `i`. Always advance `j`. If `i == len(s)`, every character of `s` was matched in order.


Time Complexity: O(|t|) &bull; Space Complexity: O(1).


<strong>Follow-up (Subsequence DP for 10<sup>9</sup> queries):</strong>


If there are many incoming strings *s<sub>1</sub>, s<sub>2</sub>, ...* tested against the same fixed *t*, precompute a next-occurrence jump table: `nxt[pos][ch]` storing the first index >= `pos` where character `ch` appears. This allows checking any *s* in O(|s|) time without rescanning *t*.




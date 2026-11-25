# Problem D — Aibohphobia

**Platform / Source:** [SPOJ AIBOHP · Aibohphobia](https://www.spoj.com/problems/AIBOHP/)  
**Time Limit:** 2.0s • **Memory Limit:** 1024 MB  
**Category:** Dynamic Programming (LCS / Palindromic Subsequence)

---

## Problem Statement


BuggyD suffers from a severe psychological condition called **aibohphobia** &mdash; the irrational fear of palindromes (words that read the same backwards and forwards). Notice that the name 'aibohphobia' itself is a palindrome!


To help overcome this fear, he wants to transform any given word into a palindrome by inserting characters. You can insert characters at any position (at the beginning, middle, or end).


Given a string *S*, find the **minimum number of character insertions** required to make it a palindrome.




## Input Format


The first line contains an integer <em>T</em>, the number of test cases. Each of the next <em>T</em> lines contains a single string <em>S</em>.


```
T
S_1
...
S_T
```


## Output Format


For each test case, print the minimum number of insertions on a new line.




## Constraints



  - 1 <= T <= 100
  - 1 <= |S| <= 6100
  - S consists of lowercase English letters.



## Examples & Step-by-Step Explanations

### Example 1

**Input:**
```
1
fft
```

**Output:**
```
1
```

**Explanation:**  
Given string: <code>"fft"</code>.
• Insert 't' at the beginning -> <code>"tfft"</code> (a palindrome with **1** insertion).
• Alternatively, insert 't' after the first 'f' -> <code>"fttf"</code> (also 1 insertion).
No 0-insertion solution exists since 'fft' is not a palindrome. Minimum insertions = **1**.

---
## Dynamic Programming Analysis


### Dynamic Programming Breakdown

<strong>Fundamental Relationship:</strong>


The minimum number of insertions to make *S* a palindrome is equal to:


```
Min Insertions = |S| - LPS(S)
```
Where `LPS(S)` is the <strong>Longest Palindromic Subsequence</strong> of *S*. Furthermore, `LPS(S)` is identical to the <strong>Longest Common Subsequence (LCS)</strong> between *S* and its reverse *S<sup>rev</sup>*:


```
LPS(S) = LCS(S, S[::-1])
```
<strong>Space Optimization:</strong> Since |S| &le; 6100, allocating a full 6100 x 6100 integer matrix requires ~150 MB and risks Memory Limit Exceeded (MLE). By maintaining only two rows (current and previous) of length |S|, memory drops to under 50 KB.


<strong>Complexity:</strong> Time: O(|S|<sup>2</sup>) &bull; Space: O(|S|).




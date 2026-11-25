# Problem C — Alphacode

**Platform / Source:** [SPOJ ACODE · Alphacode](https://www.spoj.com/problems/ACODE/)  
**Time Limit:** 2.0s • **Memory Limit:** 1024 MB  
**Category:** Dynamic Programming (Counting / Decodings)

---

## Problem Statement


Alice and Bob communicate using a numerical cipher where the letters of the English alphabet 'A' through 'Z' are encoded as numbers 1 through 26:


'A' &rarr; 1, 'B' &rarr; 2, ..., 'I' &rarr; 9, 'J' &rarr; 10, ..., 'Z' &rarr; 26.


Given an encoded string of digits, calculate the total number of possible original messages that could have produced this encoding.


The input consists of multiple test cases. The input is terminated by a single line containing <code>0</code>.




## Input Format


Each test case is given on a separate line containing a non-empty string of digits of length up to 5000. The last line of the input contains <code>0</code>, which should not be processed.


```
25114
1111111111
3333333333
0
```


## Output Format


For each test case, output the number of possible decodings on a new line.




## Constraints



  - String length up to 5000 digits.
  - Answer fits within a 64-bit integer.
  - Input is terminated by <code>0</code>.



## Examples & Step-by-Step Explanations

### Example 1

**Input:**
```
25114
1111111111
3333333333
0
```

**Output:**
```
6
89
1
```

**Explanation:**  
• For <code>25114</code>, the 6 valid decodings are:
  1. **2 5 1 1 4** -> BEAAD
  2. **2 5 1 14** -> BEAN
  3. **2 5 11 4** -> BEKD
  4. **25 1 1 4** -> YAAD
  5. **25 1 14** -> YAN
  6. **25 11 4** -> YKD
• For <code>1111111111</code> (ten 1's): Decodings correspond to Fibonacci F<sub>11</sub> = **89**.
• For <code>3333333333</code>: No double-digit '33' is &le; 26, so only 1 decoding (CCCCCCCCCC) is possible = **1**.

---
## Dynamic Programming Analysis


### Dynamic Programming Breakdown

<strong>State Definition:</strong> Let `dp[i]` be the number of decodings for the prefix of length `i`.


<strong>Base Cases:</strong> `dp[0] = 1`, and `dp[1] = 1` (assuming `s[0] &ne; '0'`).


<strong>Transitions:</strong> For each position `i >= 2`:



  - <strong>Single digit:</strong> If `s[i - 1] &ne; '0'`, the digit forms a valid letter: `dp[i] += dp[i - 1]`
  - <strong>Two digits:</strong> If the two-digit number `val = int(s[i-2:i])` satisfies `10 &le; val &le; 26`: `dp[i] += dp[i - 2]`

<strong>Zero Handling:</strong> Note that '10' and '20' are valid double digits, but a standalone '0' cannot be parsed. If both single and double digit transitions are invalid, `dp[i]` remains 0.


<strong>Complexity:</strong> Time: O(|S|) &bull; Space: O(1) keeping only the last two DP states.




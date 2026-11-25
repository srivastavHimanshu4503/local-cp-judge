import sys
data = list(map(int, sys.stdin.read().split()))
if data:
    t, p = data[0], 1
    for _ in range(t):
        h, w = data[p], data[p + 1]; p += 2
        dp = data[p:p + w]; p += w
        for _ in range(h - 1):
            row = data[p:p + w]; p += w
            dp = [row[j] + max(dp[max(j-1, 0):j+2]) for j in range(w)]
        print(max(dp))

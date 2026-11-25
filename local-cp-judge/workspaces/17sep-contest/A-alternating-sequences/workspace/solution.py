import sys
data = list(map(int, sys.stdin.read().split()))
if data:
    n = data[0]
    a = data[1:1+n]
    dp = [1] * n
    for i in range(n):
        for j in range(i):
            if abs(a[j]) < abs(a[i]) and ((a[j] > 0 and a[i] < 0) or (a[j] < 0 and a[i] > 0)):
                dp[i] = max(dp[i], dp[j] + 1)
    print(max(dp))

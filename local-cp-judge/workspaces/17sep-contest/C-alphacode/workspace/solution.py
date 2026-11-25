import sys
for s in sys.stdin.read().split():
    if s == '0':
        break
    a, b = 1, 1
    for i in range(1, len(s)):
        c = 0
        if s[i] != '0':
            c += b
        if s[i-1] == '1' or (s[i-1] == '2' and s[i] <= '6'):
            c += a
        a, b = b, c
    print(b)

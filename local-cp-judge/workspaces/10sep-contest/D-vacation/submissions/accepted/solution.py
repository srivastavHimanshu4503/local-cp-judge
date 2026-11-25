import sys
lines = sys.stdin.read().split()
if lines:
    n = int(lines[0])
    a = b = c = 0
    p = 1
    for _ in range(n):
        x, y, z = int(lines[p]), int(lines[p+1]), int(lines[p+2])
        p += 3
        a, b, c = x + max(b, c), y + max(a, c), z + max(a, b)
    print(max(a, b, c))

import sys
data = list(map(int, sys.stdin.read().split()))
if data:
    m, n = data[0], data[1]
    grid = []
    p = 2
    for _ in range(m):
        grid.append(data[p:p+n])
        p += n
    for i in range(m):
        for j in range(n):
            if i == 0 and j == 0:
                continue
            up = grid[i-1][j] if i > 0 else float('inf')
            left = grid[i][j-1] if j > 0 else float('inf')
            grid[i][j] += min(up, left)
    print(grid[-1][-1])

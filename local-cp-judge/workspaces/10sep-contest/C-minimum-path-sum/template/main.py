import sys


# ---------------- your code starts here ----------------
def solve(m, n, grid):
    # grid is an m x n matrix of non-negative integers
    # return the minimum path sum from (0, 0) to (m - 1, n - 1)
    return 0
# ----------------- your code ends here -----------------


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    m, n = int(data[0]), int(data[1])
    grid = []
    pos = 2
    for _ in range(m):
        grid.append([int(x) for x in data[pos:pos + n]])
        pos += n
    sys.stdout.write(f"{solve(m, n, grid)}\n")


if __name__ == "__main__":
    main()

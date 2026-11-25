import sys


# ---------------- your code starts here ----------------
def solve(h, w, grid):
    # grid is an h x w chamber grid of stone counts
    # return the maximum stones collected reaching the bottom row
    return 0
# ----------------- your code ends here -----------------


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    t = int(data[0])
    pos = 1
    out = []
    for _ in range(t):
        h, w = int(data[pos]), int(data[pos + 1])
        pos += 2
        grid = []
        for _ in range(h):
            grid.append([int(x) for x in data[pos:pos + w]])
            pos += w
        out.append(str(solve(h, w, grid)))
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()

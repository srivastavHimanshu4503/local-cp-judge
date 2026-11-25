import sys


# ---------------- your code starts here ----------------
def solve(n, h):
    # h[0..n-1]: heights of the N stones
    # return the minimum total cost to reach stone n - 1
    return 0
# ----------------- your code ends here -----------------


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    n = int(data[0])
    h = [int(x) for x in data[1:1 + n]]
    sys.stdout.write(f"{solve(n, h)}\n")


if __name__ == "__main__":
    main()

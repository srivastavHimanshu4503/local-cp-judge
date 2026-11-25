import sys


# ---------------- your code starts here ----------------
def solve(n, a):
    # a[0..n-1]: array of N non-zero integers
    # return the length of the longest alternating subsequence
    return 0
# ----------------- your code ends here -----------------


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    n = int(data[0])
    a = [int(x) for x in data[1:1 + n]]
    sys.stdout.write(f"{solve(n, a)}\n")


if __name__ == "__main__":
    main()

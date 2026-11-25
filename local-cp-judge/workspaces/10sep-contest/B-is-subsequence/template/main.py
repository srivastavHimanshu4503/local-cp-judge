import sys


# ---------------- your code starts here ----------------
def solve(s, t):
    # return True if s is a subsequence of t, else False
    return False
# ----------------- your code ends here -----------------


def main():
    lines = sys.stdin.read().splitlines()
    s = lines[0].strip() if len(lines) >= 1 else ""
    t = lines[1].strip() if len(lines) >= 2 else ""
    sys.stdout.write(("true" if solve(s, t) else "false") + "\n")


if __name__ == "__main__":
    main()

import sys


# ---------------- your code starts here ----------------
def solve(s):
    # s: input lowercase string
    # return minimum number of character insertions to make s a palindrome
    return 0
# ----------------- your code ends here -----------------


def main():
    data = sys.stdin.read().split()
    if not data:
        return
    t = int(data[0])
    out = [str(solve(s)) for s in data[1:1 + t]]
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()

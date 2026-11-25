import sys


# ---------------- your code starts here ----------------
def solve(s):
    # s: encoded string of digits
    # return total number of valid decodings (1..26 -> A..Z)
    return 0
# ----------------- your code ends here -----------------


def main():
    tokens = sys.stdin.read().split()
    out = []
    for s in tokens:
        if s == "0":
            break
        out.append(str(solve(s)))
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()

import sys


# ---------------- your code starts here ----------------
def solve(n, activities):
    # activities[i] = [a_i, b_i, c_i] happiness for day i
    # return maximum total happiness without choosing the same activity on consecutive days
    return 0
# ----------------- your code ends here -----------------


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    n = int(data[0])
    activities = []
    pos = 1
    for _ in range(n):
        activities.append([int(data[pos]), int(data[pos + 1]), int(data[pos + 2])])
        pos += 3
    sys.stdout.write(f"{solve(n, activities)}\n")


if __name__ == "__main__":
    main()

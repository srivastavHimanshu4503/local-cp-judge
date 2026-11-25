"""
Python 3 Competitive Programming Starter Template
Local CP Judge
"""

import sys

# Increase maximum recursion depth for deep recursive algorithms / DFS
sys.setrecursionlimit(200000)

# Fast I/O: read lines directly from standard input buffer
input = sys.stdin.readline


def solve() -> None:
    # Read input and implement problem logic here
    line = input()
    if not line:
        return
    # Example tokenization:
    # tokens = line.strip().split()


def main() -> None:
    # Set to True if problem begins with a test case count
    multi_test = False
    if multi_test:
        raw_header = input().strip()
        if raw_header:
            test_cases = int(raw_header)
            for _ in range(test_cases):
                solve()
    else:
        solve()


if __name__ == "__main__":
    main()

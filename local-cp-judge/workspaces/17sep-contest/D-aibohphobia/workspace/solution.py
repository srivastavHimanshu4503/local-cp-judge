import sys
def min_insertions(s):
    n = len(s)
    mask = {}
    for i, ch in enumerate(s):
        mask[ch] = mask.get(ch, 0) | (1 << i)
    full = (1 << n) - 1
    v = full
    for ch in reversed(s):
        u = v & mask.get(ch, 0)
        v = ((v + u) | (v - u)) & full
    lcs = n - bin(v).count('1')
    return n - lcs

data = sys.stdin.read().split()
if data:
    t = int(data[0])
    for s in data[1:1+t]:
        print(min_insertions(s))

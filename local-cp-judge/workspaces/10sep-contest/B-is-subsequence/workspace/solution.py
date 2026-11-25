s = input()
t = input()

def solve(s, t):
    if len(s) > len(t): return False
    i = j = 0
    while i < len(s):
        while j < len(t) and t[j] != s[i]: j += 1
        if j == len(t): return False
        i += 1
        j += 1
    return True
 

if solve(s, t):
    print("true")
else:
    print("false")
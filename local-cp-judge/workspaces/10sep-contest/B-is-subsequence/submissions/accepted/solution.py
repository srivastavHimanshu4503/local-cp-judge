import sys
parts = sys.stdin.read().split()
if len(parts) >= 2:
    s, t = parts[0], parts[1]
elif len(parts) == 1:
    s, t = parts[0], ""
else:
    s, t = "", ""
i = 0
for ch in t:
    if i < len(s) and s[i] == ch:
        i += 1
print("true" if i == len(s) else "false")

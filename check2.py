
lines = open("backend/services/audit_runner.py", encoding="utf-8").read().splitlines()
idx = -1
for i, l in enumerate(lines):
    if "elif step" in l and "done" in l:
        idx = i
        break
print("\n".join(lines[idx:idx+45]))


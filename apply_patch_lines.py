
lines = open("backend/services/audit_runner.py", encoding="utf-8").read().splitlines()
s=[i for i,x in enumerate(lines) if "step ==" in x and "done" in x][0]
e=[i for i,x in enumerate(lines) if "step ==" in x and "error" in x][0]
new_lines = open("patched_block.txt", encoding="utf-8").read().splitlines()
patched = "\n".join(lines[:s] + new_lines + lines[e:])
open("backend/services/audit_runner.py", "w", encoding="utf-8").write(patched)
print("Replaced by lines.")


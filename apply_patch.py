
import io
original = open("backend/services/audit_runner.py", encoding="utf-8").read()
old_block = open("block_to_replace.txt", encoding="utf-8").read()
new_block = open("patched_block.txt", encoding="utf-8").read()
patched = original.replace(old_block, new_block)
open("backend/services/audit_runner.py", "w", encoding="utf-8").write(patched)
print("Replaced:", old_block in original, len(original), "->", len(patched))


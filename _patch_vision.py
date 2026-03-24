import re

with open('veritas/agents/vision.py', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = '# Handle single-finding response formats'
end_marker = 'return findings\n\n    def _findings_from_text'

start_idx = text.find(start_marker)
end_idx = text.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_text = text[:start_idx] + end_marker + text[end_idx + len(end_marker):]
    with open('veritas/agents/vision.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("vision.py patched successfully.")
else:
    print("Markers not found.")

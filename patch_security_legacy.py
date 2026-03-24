import re
import sys

def process_file():
    with open('veritas/agents/security_agent.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update _analyze_legacy_mode signature
    content = content.replace(
        'async def _analyze_legacy_mode(\n        self,\n        url: str,\n        page,\n    ) -> SecurityResult:',
        'async def _analyze_legacy_mode(\n        self,\n        url: str,\n        page,\n        progress_emitter=None,\n    ) -> SecurityResult:'
    )

    # 2. Add progress to legacy start
    target_legacy_start = r'(logger\.info\(f"Executing legacy function-based security analysis for \{url\}"\))'
    replacement_legacy_start = r'\1\n        if progress_emitter:\n            await progress_emitter.emit_progress("Security", "legacy_start", 20, "Starting legacy security analysis...")'
    content = re.sub(target_legacy_start, replacement_legacy_start, content, count=1)

    # 3. Add to DEEP tier and tier end because they didn't patch?
    # Let me check git diff again if they patched. Wait, I'll just write it manually if missing.
    with open('veritas/agents/security_agent.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Legacy Patch applied")

if __name__ == '__main__':
    process_file()

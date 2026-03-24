import re
import sys

def process_file():
    with open('veritas/agents/security_agent.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add progress_emitter to analyze
    target_analyze = r'(use_tier_execution: Optional\[bool\] = None,\n\s+\) -> SecurityResult:)'
    replacement_analyze = r'use_tier_execution: Optional[bool] = None,\n        progress_emitter=None,\n    ) -> SecurityResult:'
    content = re.sub(target_analyze, replacement_analyze, content, count=1)

    # 2. Add progress_emitter passing to tier_mode
    target_call1 = r'(if tier_mode:\n\s+result = await self\._analyze_tier_mode\(url, page_content, headers, dom_meta\))'
    replacement_call1 = r'if tier_mode:\n            result = await self._analyze_tier_mode(url, page_content, headers, dom_meta, progress_emitter)'
    content = re.sub(target_call1, replacement_call1, content, count=1)

    # 3. Add progress_emitter passing to legacy_mode
    target_call2 = r'(else:\n\s+result = await self\._analyze_legacy_mode\(url, page\))'
    replacement_call2 = r'else:\n            result = await self._analyze_legacy_mode(url, page, progress_emitter)'
    content = re.sub(target_call2, replacement_call2, content, count=1)

    # 4. Add progress_emitter param to _analyze_tier_mode
    target_def1 = r'(dom_meta: Optional\[dict\],\n\s+\) -> SecurityResult:)'
    replacement_def1 = r'dom_meta: Optional[dict],\n        progress_emitter=None,\n    ) -> SecurityResult:'
    content = re.sub(target_def1, replacement_def1, content, count=1)

    # 5. Inject progress events in FAST tier
    target_fast = r'(logger\.info\(f"Executing FAST tier.*?\)\n\s+try:)'
    replacement_fast = r'\1\n            if progress_emitter:\n                await progress_emitter.emit_progress("Security", "fast_tier", 20, "Executing FAST security modules...")'
    content = re.sub(target_fast, replacement_fast, content, count=1)

    # 5b. Find MEDIUM tier
    target_medium = r'(logger\.info\(f"Executing MEDIUM tier.*?\)\n\s+try:)'
    replacement_medium = r'\1\n            if progress_emitter:\n                await progress_emitter.emit_progress("Security", "medium_tier", 50, "Running deep pattern analysis...")'
    content = re.sub(target_medium, replacement_medium, content, count=1)

    # 5c. Find DEEP tier
    target_deep = r'(logger\.info\(f"Executing DEEP tier.*?\)\n\s+try:)'
    replacement_deep = r'\1\n            if progress_emitter:\n                await progress_emitter.emit_progress("Security", "deep_tier", 80, "Performing strict compliance scanning...")'
    content = re.sub(target_deep, replacement_deep, content, count=1)
    
    # 6. End of tier mode
    target_tier_end = r'(logger\.info\(f"Tier-based analysis complete: \{len\(findings\)\} findings"\))'
    replacement_tier_end = r'\1\n        if progress_emitter:\n            await progress_emitter.emit_progress("Security", "complete", 100, f"Analysis complete: {len(findings)} findings")'
    content = re.sub(target_tier_end, replacement_tier_end, content, count=1)

    # 7. Add progress_emitter param to _analyze_legacy_mode
    target_def2 = r'(_analyze_legacy_mode\(\n\s+self,\n\s+url: str,\n\s+page=None,\n\s+\) -> SecurityResult:)'
    replacement_def2 = r'_analyze_legacy_mode(\n        self,\n        url: str,\n        page=None,\n        progress_emitter=None,\n    ) -> SecurityResult:'
    content = re.sub(target_def2, replacement_def2, content, count=1)

    # 8. Start of legacy mode
    target_legacy_start = r'(logger\.info\(f"Executing legacy function-based security analysis for \{url\}"\))'
    replacement_legacy_start = r'\1\n        if progress_emitter:\n            await progress_emitter.emit_progress("Security", "legacy_start", 20, "Starting legacy security analysis...")'
    content = re.sub(target_legacy_start, replacement_legacy_start, content, count=1)

    with open('veritas/agents/security_agent.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Agent Patch applied")

if __name__ == '__main__':
    process_file()

import re
import sys

def patch_file():
    with open('veritas/core/orchestrator.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Patch Security "running"
    sec_run_target = r'(# 1b\. Security modules\s+self\._emit\("security", "scanning", 27, "Running security analysis modules\.\.\.", iteration=state\["iteration"\]\))'
    sec_run_replacement = r'\1\n                if self.use_progress_streaming and self._progress_emitter:\n                    await self._progress_emitter.emit_agent_status("Security", "running", "Performing deep security analysis...")'
    content = re.sub(sec_run_target, sec_run_replacement, content, count=1)

    # 2. Patch Security "completed"
    sec_comp_target = r'(self\._emit\("security", "done", 30, f"Security modules: \{\', \'\.join\(sec_modules\)\} \(mode=\{security_mode\}\)\{degr_str\}", modules=sec_modules, security_mode=security_mode, security_results=state\.get\("security_results", \{\}\)\))'
    sec_comp_replacement = r'\1\n                    if self.use_progress_streaming and self._progress_emitter:\n                        await self._progress_emitter.emit_agent_status("Security", "completed")\n                        await self._progress_emitter.emit_progress("Overall", "Security", 30, f"Security complete: {len(sec_modules)} modules")'
    content = re.sub(sec_comp_target, sec_comp_replacement, content, count=1)
    
    # 3. Patch Security "error"
    sec_err_target = r'(self\._emit\("security", "error", 30, str\(e\)\))'
    sec_err_replacement = r'\1\n                    if self.use_progress_streaming and self._progress_emitter:\n                        await self._progress_emitter.emit_error("security_error", str(e), "Security", recoverable=True)\n                        await self._progress_emitter.emit_agent_status("Security", "failed", str(e))'
    content = re.sub(sec_err_target, sec_err_replacement, content, count=1)
    
    # 4. Patch Graph "running"
    graph_run_target = r'(# 3\. Graph\s+self\._emit\("graph".*?iteration=state\["iteration"\]\))'
    graph_run_replacement = r'\1\n                if self.use_progress_streaming and self._progress_emitter:\n                    await self._progress_emitter.emit_agent_status("Graph", "running", "Graph agent discovering entities...")'
    content = re.sub(graph_run_target, graph_run_replacement, content, count=1)
    
    # 5. Patch Judge "running"
    judge_run_target = r'(# 4\. Judge\s+self\._emit\("judge".*?iteration=state\["iteration"\]\))'
    judge_run_replacement = r'\1\n                if self.use_progress_streaming and self._progress_emitter:\n                    await self._progress_emitter.emit_agent_status("Judge", "running", "Judge agent deliberating evidence...")'
    content = re.sub(judge_run_target, judge_run_replacement, content, count=1)

    # 6. Inject _progress_emitter into state_with_complexity
    state_target = r'("_degraded_agents": \[\],  # List of degraded agent names\n\s+\})'
    state_replacement = r'"_degraded_agents": [],  # List of degraded agent names\n              "_progress_emitter": getattr(self, "_progress_emitter", None) if getattr(self, "use_progress_streaming", False) else None,\n          }'
    content = re.sub(state_target, state_replacement, content, count=1)

    with open('veritas/core/orchestrator.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Patch applied")

if __name__ == '__main__':
    patch_file()

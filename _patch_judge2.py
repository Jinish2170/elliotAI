with open('veritas/agents/judge.py', 'r') as f:
    c = f.read()
c = c.replace(
    'logger.warning(f"----- JUDGE EMITTER PRESENT? {emitter is not None} -----")',
    'logger.warning(f"----- JUDGE EMITTER PRESENT? {emitter is not None} -----")\n                open("judge_debug.txt", "w").write(f"Emitter: {emitter is not None} CVSS: {bool(dual_verdict.technical.cvss_metrics)}")'
)
with open('veritas/agents/judge.py', 'w') as f:
    f.write(c)

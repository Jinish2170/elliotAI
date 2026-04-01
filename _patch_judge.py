with open('veritas/agents/judge.py', 'r') as f:
    c = f.read()
c = c.replace(
    'logger.info(f"Dual-tier verdict generated for {evidence.url}")',
    'logger.info(f"Dual-tier verdict generated for {evidence.url}")\n                logger.warning(f"----- JUDGE EMITTER PRESENT? {emitter is not None} -----")\n                logger.warning(f"----- CVSS DICT PRESENT? {bool(dual_verdict.technical.cvss_metrics)} -----")'
)
with open('veritas/agents/judge.py', 'w') as f:
    f.write(c)

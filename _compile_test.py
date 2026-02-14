import py_compile
import sys

files = [
    'veritas/config/site_types.py',
    'veritas/config/settings.py',
    'veritas/config/trust_weights.py',
    'veritas/analysis/security_headers.py',
    'veritas/analysis/phishing_checker.py',
    'veritas/analysis/redirect_analyzer.py',
    'veritas/analysis/form_validator.py',
    'veritas/analysis/js_analyzer.py',
    'veritas/core/tor_client.py',
    'veritas/agents/scout.py',
    'veritas/agents/vision.py',
    'veritas/agents/graph_investigator.py',
    'veritas/agents/judge.py',
    'veritas/core/orchestrator.py',
    'veritas/__main__.py',
    'veritas/ui/app.py',
]
ok, fail = 0, 0
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f'  OK  {f}')
        ok += 1
    except py_compile.PyCompileError as e:
        print(f'  FAIL {f}: {e}')
        fail += 1
print(f'\n{ok} passed, {fail} failed')
sys.exit(fail)

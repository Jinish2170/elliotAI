import re

def patch_trust_weights():
    with open('veritas/config/trust_weights.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix domain rules
    content = content.replace('domain_age_days is not None and domain_age_days < 7', 'domain_age_days is not None and 0 <= domain_age_days < 7')
    content = content.replace('domain_age_days is not None and domain_age_days < 30', 'domain_age_days is not None and 0 <= domain_age_days < 30')
    content = content.replace('domain_age_days is not None and domain_age_days < 90', 'domain_age_days is not None and 0 <= domain_age_days < 90')

    with open('veritas/config/trust_weights.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
def patch_graph_node():
    with open('veritas/core/nodes/graph.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix fallback ssl and age
    target = r'("domain_age_days": -1,\n\s+"has_ssl": False,)'
    replacement = r'"domain_age_days": -1,\n                "has_ssl": url.lower().startswith("https"),'
    content = re.sub(target, replacement, content, count=1)

    with open('veritas/core/nodes/graph.py', 'w', encoding='utf-8') as f:
        f.write(content)

def patch_orchestrator():
    with open('veritas/core/orchestrator.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix fallback ssl
    target = r'("domain_age_days": -1,\n\s+"has_ssl": False,)'
    # We don't have url right there easily, we can just omit or set None... actually url is passed? No, graph_fallback takes kwargs, it might not have url. 
    # Wait, kwargs has url.
    replacement = r'"domain_age_days": -1,\n                  "has_ssl": kwargs.get("url", "").lower().startswith("https"),'
    content = re.sub(target, replacement, content, count=1)

    with open('veritas/core/orchestrator.py', 'w', encoding='utf-8') as f:
        f.write(content)

patch_trust_weights()
patch_graph_node()
patch_orchestrator()
print("Graph Fallbacks Patched.")

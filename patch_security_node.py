import re
import sys

def patch_node():
    with open('veritas/core/nodes/security.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Pass progress emitter to agent.analyze!
    target = r'(result = await agent\.analyze\(\n\s+url=url,\n\s+page_content=page_content,\n\s+headers=headers,\n\s+dom_meta=dom_meta,\n\s+use_tier_execution=use_tier_execution\n\s+\))'
    replacement = r'result = await agent.analyze(\n                url=url,\n                page_content=page_content,\n                headers=headers,\n                dom_meta=dom_meta,\n                use_tier_execution=use_tier_execution,\n                progress_emitter=state.get("_progress_emitter")\n            )'
    
    content = re.sub(target, replacement, content, count=1)

    with open('veritas/core/nodes/security.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Node Patch applied!")

if __name__ == '__main__':
    patch_node()

import re

content = open('backend/services/audit_runner.py', encoding='utf-8').read()

# Mitre replacement
content = re.sub(
    r'cti = summary_data\.get\("cti_techniques", \[\]\)\s+if not cti:\s+cti = \["T1589\.001 - Gather Victim Identity Information"\]',
    r'cti = summary_data.get("cti_techniques", [])',
    content
)

# Vision replacement
content = re.sub(
    r'elif phase == "vision":\s+await send\(\{"type": "vision_pass_start", "pass_num": 1, "pass_name": "Full Scan"\}\)\s+await send\(\{"type": "vision_pass_complete", "pass_num": 1, "pass_name": "Full Scan", "findings_count": 0, "confidence": 0.99, "model_used": "llama-3.2"\}\)',
    r'''elif phase == "vision":
                vision_res = summary_data.get("vision_result", {})
                f_count = len(vision_res.get("findings", [])) if isinstance(vision_res.get("findings"), list) else 0
                m_used = vision_res.get("model", "meta/llama-3.2-90b-vision-instruct")
                await send({"type": "vision_pass_start", "pass_num": 1, "pass_name": "Visual Analysis"})
                await send({"type": "vision_pass_complete", "pass_num": 1, "pass_name": "Visual Analysis", "findings_count": f_count, "confidence": 0.95, "model_used": m_used})''',
    content
)
open('backend/services/audit_runner.py', 'w', encoding='utf-8').write(content)
print("Regex Patch Applied")


import re
content = open('backend/services/audit_runner.py', encoding='utf-8').read()

# Fix scout placeholder logic
content = re.sub(
    r'scout_results = \[\{"url": "https://target", "screenshots": \["dummy"\], "navigation_time_ms": 1500\}\]',
    r'scout_results = [{"url": summary_data.get("url", self.url), "screenshots": [], "navigation_time_ms": 0}]',
    content
)

# Fix screenshot fallback dummy
content = re.sub(
    r'if not screenshot_list:\s+screenshot_list = \["dummy"\]',
    r'if not screenshot_list:\n                        screenshot_list = []',
    content
)

open('backend/services/audit_runner.py', 'w', encoding='utf-8').write(content)
print("Scout Patch Applied")

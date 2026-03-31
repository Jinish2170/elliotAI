import re
file_path = 'veritas/core/web_searcher.py'
content = open(file_path, encoding='utf-8').read()

old_block = '''    for r in results:
        url = r.get("url", "")
        if not url or not url.startswith("http"):
            enriched.append(r)
            continue

        try:
            page = await context.new_page()'''

new_block = '''    for r in results:
        url = r.get("url", "")
        if not url or not url.startswith("http"):
            enriched.append(r)
            continue
            
        # Social media and major platforms often block headless browsers explicitly
        # and throw CAPTCHAs, rendering the underlying search scrape useless.
        fragile_domains = ['linkedin.com', 'facebook.com', 'twitter.com', 'x.com', 'instagram.com', 'glassdoor.com']
        if any(d in url.lower() for d in fragile_domains):
            # Skip playwright enrichment, rely on the search engine snippet
            enriched.append(r)
            continue

        try:
            page = await context.new_page()'''

if old_block in content:
    content = content.replace(old_block, new_block)
    open(file_path, 'w', encoding='utf-8').write(content)
    print("Patched web searcher against CAPTCHA traps.")
else:
    print("Could not find web searcher block")

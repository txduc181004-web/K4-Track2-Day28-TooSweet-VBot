"""Print readable text snippets around dollar amounts in a pricing page (decoded embedded JSON)."""
import re, sys, html
raw = open(sys.argv[1], encoding='utf-8', errors='ignore').read()
kw = sys.argv[2].lower() if len(sys.argv) > 2 else None
s = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), raw)
s = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', s, flags=re.S) if False else s
s = re.sub(r'<[^>]+>', ' ', s)
s = html.unescape(s).replace('\\n', ' ').replace('\\"', "'")
s = re.sub(r'null|\[|\]|,\d+,|"', ' ', s)
s = re.sub(r'\s+', ' ', s)
seen = set()
for m in re.finditer(r'\$\d[\d,.]*', s):
    snip = s[max(0, m.start() - 160): m.end() + 60]
    if kw and kw not in snip.lower():
        continue
    key = snip[100:240]
    if key in seen:
        continue
    seen.add(key)
    print('…' + snip)

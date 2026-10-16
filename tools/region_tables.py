"""Extract per-region pricing tables embedded as JSON in Google Cloud pricing pages.

usage: python3 region_tables.py PAGE.html "Singapore (asia-southeast1)" [filter-substring]
Each table is printed as rows of cells; the trailing [n] after the region label is the
unit selector of the page (1 = hourly, 2 = monthly ... as rendered on the page).
"""
import re, sys, html

raw = open(sys.argv[1], encoding='utf-8', errors='ignore').read()
region = sys.argv[2]
flt = sys.argv[3].lower() if len(sys.argv) > 3 else None
s = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), raw)
s = s.replace('\\n', '\n').replace('\\"', "'")
label_re = re.compile(r'"([^"\[\]]{3,60}\([a-z]+-[a-z]+\d*\)|[^"\[\]]{3,40}\((?:global|multi-region|[a-z]+)\))",\[(\d+)\]')
marks = list(label_re.finditer(s))
prev_end = 0
for m in marks:
    block = s[prev_end:m.start()]
    prev_end = m.end()
    if m.group(1) != region:
        continue
    # rows separated by ']]],[[[' patterns; cells are quoted strings
    cells = [html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in re.findall(r'"((?:[^"\\]|\\.)*)"', block)]
    cells = [c for c in cells if c and not re.fullmatch(r'[A-Za-z0-9_\-]{20,}', c) and len(c) < 300]
    text = ' | '.join(cells)
    if flt and flt not in text.lower():
        continue
    print(f'--- [{m.group(2)}] ' + text[:3000])

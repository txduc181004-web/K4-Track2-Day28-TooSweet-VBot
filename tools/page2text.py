"""Turn a Google Cloud pricing page (HTML with JSON-embedded content) into plain text."""
import sys, re, html, codecs

def to_text(s):
    # decode < style escapes found in embedded JSON
    s = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), s)
    s = s.replace('\\n', '\n').replace('\\"', '"').replace('\\/', '/')
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.S) if '<html' in s[:2000].lower() and False else s
    s = re.sub(r'</(td|th)>', ' | ', s)
    s = re.sub(r'<(br|/tr|/p|/h\d|/li|/div|/table)[^>]*>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    t = html.unescape(s)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n\s*\n+', '\n', t)
    return t

src, dst = sys.argv[1], sys.argv[2]
open(dst, 'w').write(to_text(open(src, encoding='utf-8', errors='ignore').read()))

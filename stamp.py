#!/usr/bin/env python3
"""
Stamps each data file's <script> tag in index.html with a fingerprint of the
file's contents:  data/verses.js?v=3f9a1c2e

The fingerprint changes exactly when the file changes, so after a publish a
browser fetches new data instead of reusing an old cached copy — and keeps
using its cache when nothing changed. Run it after the build scripts:

    python3 stamp.py
"""
import hashlib, os, re

HERE  = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.html")

html = open(INDEX, encoding="utf-8").read()

def stamp(m):
    path = os.path.join(HERE, m.group(1))
    if not os.path.exists(path):
        return m.group(0)
    digest = hashlib.sha1(open(path, "rb").read()).hexdigest()[:8]
    return f'src="{m.group(1)}?v={digest}"'

new = re.sub(r'src="(data/[\w.-]+\.js)\?v=[\w-]*"', stamp, html)
if new != html:
    open(INDEX, "w", encoding="utf-8").write(new)
for tag in re.findall(r'src="data/[\w.-]+\.js\?v=[\w-]*"', new):
    print(" ", tag)

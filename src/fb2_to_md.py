#!/usr/bin/env python3
"""Unpack an FB2 (may be zip) to markdown paragraphs with chapter headings.
Usage: python3 fb2_to_md.py <file.fb2> <out.txt>"""
import re, sys, zipfile, io, html
raw = open(sys.argv[1], "rb").read()
if raw[:2] == b"PK":
    z = zipfile.ZipFile(io.BytesIO(raw)); raw = z.read(z.namelist()[0])
enc = re.search(rb'encoding="([^"]+)"', raw[:200]); enc = enc.group(1).decode() if enc else "utf-8"
s = raw.decode(enc, "ignore")
ti = re.search(r'<book-title>(.*?)</book-title>', s, re.S)
au = re.findall(r'<author>.*?</author>', s, re.S)
au = " ".join(re.sub(r'<[^>]+>', " ", a) for a in au[:1]); au = " ".join(au.split())
lang = re.search(r'<lang>(.*?)</lang>', s)
print("TITLE:", ti.group(1) if ti else None, "| AUTHOR:", au, "| lang:", lang.group(1) if lang else None, "| enc:", enc)
body = re.search(r'<body>(.*?)</body>', s, re.S).group(1)
body = re.sub(r'<title>(.*?)</title>', lambda m: "\n\n## " + " ".join(re.sub(r'<[^>]+>', " ", m.group(1)).split()) + "\n\n", body, flags=re.S)
body = re.sub(r'<empty-line\s*/>', "\n\n", body)
body = re.sub(r'</p>', "\n\n", body); body = re.sub(r'<[^>]+>', "", body)
t = html.unescape(body)
ps = [" ".join(p.split()) for p in re.split(r'\n\s*\n', t) if p.strip()]
open(sys.argv[2], "w").write("\n\n".join(ps) + "\n")
print(len(ps), "paras,", len(" ".join(ps).split()), "words, chars", len(" ".join(ps)))

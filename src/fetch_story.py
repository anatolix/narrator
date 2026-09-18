#!/usr/bin/env python3
"""Download a story (Literotica multi-page, samlib.ru cp1251, or generic HTML) to a clean markdown file.
Usage: python3 fetch_story.py <url> <out.md>   (needs network_mode: proxied)"""
import re, html, sys, subprocess, urllib.parse
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"
def get(url):
    r = subprocess.run(["curl", "-sL", "-A", UA, url], capture_output=True)
    raw = r.stdout
    if "samlib.ru" in url or "zhurnal.lib.ru" in url:
        return raw.decode("cp1251", "ignore")
    return raw.decode("utf-8", "ignore")
def clean(fragment):
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"</p>\s*", "\n\n", fragment, flags=re.I)
    fragment = re.sub(r"<!--.*?-->", "", fragment, flags=re.S)
    fragment = re.sub(r"<script.*?</script>|<style.*?</style>", "", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    txt = html.unescape(fragment)
    ps = [p.strip() for p in re.split(r"\n\s*\n", txt) if p.strip()]
    return ps
def literotica(url):
    base = url.split("?")[0]
    s = get(base)
    title = re.search(r'og:title" content="(.*?)"', s)
    title = title.group(1).split(" - ")[0] if title else "Story"
    n = max([int(x) for x in re.findall(r"\?page=(\d+)", s)] + [1])
    paras = []
    for p in range(1, n + 1):
        page = s if p == 1 else get(f"{base}?page={p}")
        i = page.find('itemprop="articleBody"'); j = page.find("</article>", i)
        ps = clean(page[i:j]) if i >= 0 else []
        if ps and ps[0].startswith('itemprop="articleBody">'): ps[0] = ps[0].split(">", 1)[1].strip()
        while ps and re.search(r"Report|Go to page|Page 1|Stories|Followers|Updated:|Created:", ps[-1]): ps.pop()
        paras += ps
    return title, paras
def samlib(url):
    s = get(url)
    title = re.search(r"<title>(.*?)</title>", s, re.S)
    title = title.group(1).strip() if title else "Рассказ"
    m = re.search(r"<!-{2,}-+ Блок статьи -+>(.*?)<!-{2,}-+ Блок окончания", s, re.S) or re.search(r"<dd>(.*)</dd>", s, re.S)
    body = m.group(1) if m else s
    return title, clean(body)
def generic(url):
    s = get(url)
    title = re.search(r"<title>(.*?)</title>", s, re.S)
    title = title.group(1).strip() if title else "Story"
    m = re.search(r"<article.*?</article>", s, re.S) or re.search(r"<body.*?</body>", s, re.S)
    return title, clean(m.group(0) if m else s)
url, out = sys.argv[1], sys.argv[2]
host = urllib.parse.urlparse(url).netloc
title, paras = literotica(url) if "literotica.com" in host else samlib(url) if "samlib" in host or "zhurnal.lib" in host else generic(url)
open(out, "w").write(f"# {title}\n\n" + "\n\n".join(paras) + "\n")
print(f"{title!r}: {len(paras)} paragraphs, {len(' '.join(paras).split())} words -> {out}")

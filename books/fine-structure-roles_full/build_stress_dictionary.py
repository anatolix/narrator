import re, glob, collections, json

# 1. словарь: слово (lower, без '+') -> Counter паттернов (lower, с '+')
dic = collections.defaultdict(collections.Counter)
for fn in sorted(glob.glob('roles_full-ch*.md')):
    for m in re.finditer(r"[А-Яа-яЁё+]+", open(fn).read()):
        tok = m.group(0)
        low = tok.lower()
        plain = low.replace('+','')
        if plain:
            dic[plain][low] += 1

print(f"словарь: {len(dic)} слов, ударение варьируется у {sum(1 for v in dic.values() if len(v)>1)}")

# 2. exceptions.txt: LHS (ошибочные формы)
exc_bad, exc_good = {}, {}
for line in open('exceptions.txt'):
    line = line.split('#')[0].strip()
    m = re.match(r'^(\S+)\s*->\s*(\S+)', line)
    if m:
        bad, good = m.group(1).lower(), m.group(2).lower()
        exc_bad.setdefault(bad.replace('+',''), []).append(bad)
        exc_good.setdefault(good.replace('+',''), []).append(good)

print(f"exceptions: {sum(len(v) for v in exc_bad.values())} ошибочных форм")
print("\n== ОШИБОЧНЫЕ формы из exceptions, всё ещё ЖИВЫЕ в скриптах ==")
alive = 0
for plain, bads in sorted(exc_bad.items()):
    for bad in bads:
        n = dic.get(plain, {}).get(bad, 0)
        if n:
            print(f"  ЖИВО: {bad} ×{n}   (варианты слова: {dict(dic[plain])})")
            alive += 1
if not alive: print("  — ноль, все ошибочные формы вычищены —")

print("\n== слова из exceptions: текущее состояние в словаре ==")
for plain in sorted(set(exc_bad) | set(exc_good)):
    if plain in dic:
        print(f"  {plain}: {dict(dic[plain])}")

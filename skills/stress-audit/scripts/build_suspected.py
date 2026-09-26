import re, glob, collections
from pylem import MorphanHolder, MorphLanguage
W='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace'
D=W+'/narrator/books/fine-structure-roles_full'
OUT=W+'/narrator/reports/fine-structure-forms/suspected_forms.md'
h=MorphanHolder(MorphLanguage.Russian)
TOK=re.compile(r"[А-Яа-яЁё+]+(?:-[А-Яа-яЁё+]+)*")
ROLE=re.compile(r"^([A-ZА-ЯЁ0-9_ ]+):\s*(.*)$")
VOW=set('аеёиоуыэюя')
norm=lambda s: s.replace('ё','е')
def yo_ok(s):  # если в форме есть ё, ударение обязано стоять на ней
    return 'ё' not in s.replace('+','') or '+ё' in s
tok=collections.Counter()
for f in sorted(glob.glob(D+'/roles_full-ch*.md')):
    for line in open(f,encoding='utf-8'):
        line=line.strip()
        if not line or line[0] in '@#': continue
        m=ROLE.match(line); text=m.group(2) if m else line
        for t in TOK.findall(text):
            t=t.lower().strip('-')
            if re.search('[а-яё]',t): tok[t]+=1
F=collections.defaultdict(collections.Counter)
for st,n in tok.items(): F[st.replace('+','')][st]+=n
rows=[]; dropped_yo=0
for form,tv in F.items():
    if not (sum(c in VOW for c in form)>=2 or 'е' in form or 'ё' in form): continue
    py={}
    for p in h.accent(form):
        for fo in p['forms']:
            s=fo['stressed'].lower()
            if '+' not in s: continue
            lab=f"{fo['pos']}({p['lemma'].lower()})"
            py.setdefault(s,[])
            if lab not in py[s]: py[s].append(lab)
    # pylem ставит ударение не на ё — заведомый брак, отбрасываем
    bad=[s for s in py if not yo_ok(s.replace('е','ё') if 'ё' in form and 'ё' not in s else s) and 'ё' in form]
    for s in list(py):
        cand=s
        if 'ё' in form and 'ё' not in s:  # pylem пишет без ё — восстановим ё из формы
            cand=''.join(('ё' if c=='е' and form[i- s[:j].count('+')] =='ё' else c) for j,(i,c) in enumerate(zip(range(len(s)),s)))
        if 'ё' in form and not yo_ok(cand): py.pop(s); dropped_yo+=1
    ts={norm(s) for s in tv if '+' in s}
    ps={norm(s) for s in py}
    allv=ts|ps
    if len(allv)<2: continue
    why=[]
    if len(ts)>1: why.append('в тексте разные')
    if len(ps)>1: why.append('pylem: омограф')
    if ts and ps and ts!=ps: why.append('текст ≠ pylem')
    rows.append((sum(tv.values()),form,tv,py,why))
rows.sort(key=lambda r:(-r[0],r[1]))
c=collections.Counter(w for r in rows for w in r[4])
with open(OUT,'w',encoding='utf-8') as o:
    o.write('# Fine Structure — подозрительные формы (несколько возможных ударений)\n\n')
    o.write(f'Форм: {len(rows)} из {len(F)}. Критерий: по тексту и pylem вместе у формы больше одного варианта ударения (е/ё не различаются, безударные вхождения не считаются). Варианты pylem с ударением не на ё отброшены как брак ({dropped_yo}). Отброшены формы с одной гласной без е/ё.\n\n')
    o.write('Причины: ' + ', '.join(f'{k} — {v}' for k,v in c.most_common()) + '\n\n')
    o.write('| N | форма | ударения в тексте | ударения pylem | части речи pylem | почему |\n|---:|---|---|---|---|---|\n')
    for n,form,tv,py,why in rows:
        t=', '.join(f'{s} ({k})' for s,k in tv.most_common())
        ps='; '.join(py) or '—'; pp='; '.join(', '.join(l) for l in py.values()) or '—'
        o.write(f'| {n} | {form} | {t} | {ps} | {pp} | {"; ".join(why)} |\n')
print('rows',len(rows),dict(c),'dropped_yo',dropped_yo)

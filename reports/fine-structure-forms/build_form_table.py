import re, glob, collections
from pylem import MorphanHolder, MorphLanguage
W='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace'
D=W+'/narrator/books/fine-structure-roles_full'
OUT=W+'/scratch/fine-structure-forms.md'
h=MorphanHolder(MorphLanguage.Russian)
TOK=re.compile(r"[А-Яа-яЁё+]+(?:-[А-Яа-яЁё+]+)*")
ROLE=re.compile(r"^([A-ZА-ЯЁ0-9_ ]+):\s*(.*)$")
norm=lambda s: s.replace('ё','е')
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
VOW=set('аеёиоуыэюя')
keep=lambda w: sum(c in VOW for c in w)>=2 or 'е' in w or 'ё' in w
rows=[]
for form,tv in F.items():
    if not keep(form): continue
    py={}
    for p in h.accent(form):
        for fo in p['forms']:
            s=fo['stressed'].lower(); lab=f"{fo['pos']}({p['lemma'].lower()})"
            py.setdefault(s,[])
            if lab not in py[s]: py[s].append(lab)
    ps={norm(s) for s in py if '+' in s}
    bad=sorted(st for st in tv if '+' in st and ps and norm(st) not in ps)
    rows.append((sum(tv.values()),form,tv,py,bad))
rows.sort(key=lambda r:(-r[0],r[1]))
with open(OUT,'w',encoding='utf-8') as o:
    o.write('# Fine Structure — словарь форм (roles_full, 42 главы)\n\n')
    o.write(f'Словоупотреблений: {sum(tok.values())}, уникальных форм: {len(rows)}, форм с ⚠: {sum(1 for r in rows if r[4])}.\n\n')
    o.write('Отброшены формы с одной гласной и меньше, кроме содержащих е/ё.\n\nКолонки: частота · форма (lowercase, без ударений) · ударения в тексте (сколько раз) · ударения pylem · части речи pylem (лемма) — в том же порядке, что ударения, через « ; » · ⚠ = ударение в тексте, которого pylem для этой формы не допускает.\n\n')
    o.write('| N | форма | ударения в тексте | ударения pylem | части речи pylem | ⚠ |\n|---:|---|---|---|---|---|\n')
    for n,form,tv,py,bad in rows:
        t=', '.join(f'{s} ({k})' for s,k in tv.most_common())
        ps='; '.join(py) or '—'
        pp='; '.join(', '.join(l) for l in py.values()) or '—'
        o.write(f'| {n} | {form} | {t} | {ps} | {pp} | {", ".join(bad)} |\n')
print('forms',len(rows),'flagged',sum(1 for r in rows if r[4]),'unknown',sum(1 for r in rows if not r[3]))

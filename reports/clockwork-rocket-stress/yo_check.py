# Find places where compare (ruaccent/pylem) offered a ё-form but resolved text has е. Grouped list with context.
import re,glob,collections
N=lambda s:s.replace('+','').lower().replace('ё','е')
BR=re.compile(r'\[[^\[\]]+\]')
RT=re.compile(r'\[[^\[\]]+\]|[А-Яа-яЁё+][А-Яа-яЁё+\-]*')
g=collections.defaultdict(list); skip=0; lines=0
for f in sorted(glob.glob('resolved/ch[0-9][0-9].md')):
    ch=f[-5:-3]; R=open(f,encoding='utf-8').read().split('\n'); C=open(f'ch{ch}.md',encoding='utf-8').read().split('\n')
    for i,(r,c) in enumerate(zip(R,C),1):
        ROLE=re.compile(r'^[А-ЯЁA-Z0-9_ ]{1,30}:\s*'); r=ROLE.sub('',r); c=ROLE.sub('',c)
        cb=BR.findall(c)
        if not cb: continue
        rt=RT.findall(r)
        if len(rt)!=len(cb): skip+=1; continue
        lines+=1
        plain=re.sub(r'\[([^,\]]+)(?:, [^\]]+)*\]',r'\1',r).replace('+','')
        for b,t in zip(cb,rt):
            pieces=[p.split(':')[0].strip() for p in re.split(r'[,;]',b.strip('[]'))]
            yo=sorted({p for p in pieces if 'ё' in p.lower() and N(p)==N(pieces[0])})
            if not yo or 'ё' in t.lower(): continue
            surf=t.strip('[]').split(', ')[0].replace('+','')
            k=plain.lower().find(surf.lower())
            g[N(surf)].append((ch,i,t,yo,plain[max(0,k-70):k+70]))
A={'ее','свое','твое','нее','своем','желтого','зеленого','придется','распределенных','искаженной'}
B={'небо','неба','небу','небе','самое','левой','лет','далеко','недалеко','шлем','семена','тешу','афера','афере'}
sec=[('А. ё обязательна — предлагаю заменить на ё',A),('Б. ruaccent/pylem лепят ё зря — оставить е',B),('В. решать по контексту',None)]
out=['# Заводная ракета — где ruaccent/pylem давали ё, а в тексте е','',f'Мест {sum(map(len,g.values()))}, слов {len(g)}. Строк не выровнено: {skip}.','']
for title,S in sec:
    ws=[w for w in g if (w in S if S is not None else w not in A|B)]
    out.append(f'# {title} — {sum(len(g[w]) for w in ws)} мест'); out.append('')
    for w in sorted(ws,key=lambda w:-len(g[w])):
        its=g[w]; out.append(f'## {w} — {len(its)}  (варианты с ё: {", ".join(sorted({y for it in its for y in it[3]}))})')
        for ch,i,t,yo,ctx in its: out.append(f'- **ch{ch}:{i}** сейчас {t}\n  > …{ctx}…')
        out.append('')
open('yo-check.md','w',encoding='utf-8').write('\n'.join(out))
for title,S in sec:
    ws=[w for w in g if (w in S if S is not None else w not in A|B)]
    print(title, sum(len(g[w]) for w in ws), [(w,len(g[w])) for w in sorted(ws,key=lambda w:-len(g[w]))])

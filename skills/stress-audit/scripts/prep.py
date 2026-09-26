import re, glob, collections, json
from pylem import MorphanHolder, MorphLanguage
W='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace'
D=W+'/narrator/books/fine-structure-roles_full'
S=W+'/narrator/reports/fine-structure-forms/suspected_forms.md'
OUT=W+'/scratch/suspect'
h=MorphanHolder(MorphLanguage.Russian)
forms=[]
for l in open(S,encoding='utf-8'):
    if l.startswith('| ') and not l.startswith('| N ') and not l.startswith('|--'):
        c=[x.strip() for x in l.strip().strip('|').split('|')]
        if c[0].isdigit(): forms.append(c[1])
fs=set(forms)
TOK=re.compile(r"[А-Яа-яЁё+]+(?:-[А-Яа-яЁё+]+)*")
ROLE=re.compile(r"^([A-ZА-ЯЁ0-9_ ]+):\s*(.*)$")
occ=collections.defaultdict(lambda: collections.defaultdict(list))
for f in sorted(glob.glob(D+'/roles_full-ch*.md')):
    ch=re.search(r'ch(\d+)',f).group(1)
    for ln,line in enumerate(open(f,encoding='utf-8'),1):
        s=line.strip()
        if not s or s[0] in '@#': continue
        m=ROLE.match(s); text=m.group(2) if m else s
        toks=list(TOK.finditer(text))
        for k,mt in enumerate(toks):
            t=mt.group(0).strip('-'); form=t.lower().replace('+','')
            if form not in fs: continue
            a=max(0,k-8); b=min(len(toks),k+9)
            ctx=text[toks[a].start():mt.start()]+'[['+mt.group(0)+']]'+text[mt.end():toks[b-1].end()]
            occ[form][t.lower()].append(f'ch{ch}:{ln} '+ctx.replace('+',''))
# контекст без плюсов, чтобы помощник судил по смыслу; ударение показываем только у целевого слова
items=[]
for form in forms:
    py={}
    for p in h.accent(form):
        for fo in p['forms']:
            s=fo['stressed'].lower()
            if '+' in s: py.setdefault(s,set()).add(f"{fo['pos']}({p['lemma'].lower()}) {fo['grammems']}")
    variants={v:{'count':len(L),'examples':L[:12]} for v,L in occ[form].items()}
    items.append({'form':form,'pylem':{k:sorted(v) for k,v in py.items()},'text_variants':variants})
# fix ctx: вернуть ударение в целевое слово
for it in items:
    for v,d in it['text_variants'].items():
        d['examples']=[re.sub(r'\[\[[^\]]*\]\]','[['+v+']]',e,count=1) for e in d['examples']]
N=8
size=[0]*N; buckets=[[] for _ in range(N)]
for it in sorted(items,key=lambda x:-sum(d['count'] for d in x['text_variants'].values())):
    w=sum(min(d['count'],12) for d in it['text_variants'].values())+1
    i=size.index(min(size)); buckets[i].append(it); size[i]+=w
for i,bk in enumerate(buckets,1):
    json.dump(bk,open(f'{OUT}/batch{i}.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('forms',len(items),'batches',[len(b) for b in buckets],'weights',size)
print(json.dumps(items[5],ensure_ascii=False)[:900])

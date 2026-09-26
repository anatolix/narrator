import re, glob, collections, json, os
from pylem import MorphanHolder, MorphLanguage
W='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace'
D=W+'/narrator/books/fine-structure-roles_full'
h=MorphanHolder(MorphLanguage.Russian)
TOK=re.compile(r"[А-Яа-яЁё+]+(?:-[А-Яа-яЁё+]+)*")
ROLE=re.compile(r"^([A-ZА-ЯЁ0-9_ ]+):\s*(.*)$")
VOW=set('аеёиоуыэюя')
norm=lambda s: s.replace('ё','е')
cache={}
def py(form):
    if form not in cache:
        v={}
        for p in h.accent(form):
            for fo in p['forms']:
                s=fo['stressed'].lower()
                if '+' in s: v.setdefault(s,[]).append(f"{fo['pos']}({p['lemma'].lower()})")
        cache[form]=v
    return cache[form]
def apply_case(orig,target):
    plain=orig.replace('+',''); t=target.replace('+','')
    if norm(plain.lower())!=norm(t): return None
    out=''; j=0
    for ch in target:
        if ch=='+': out+='+'
        else: out+=plain[j]; j+=1
    return out
occ=[]
for f in sorted(glob.glob(D+'/roles_full-ch*.md')):
    ch=re.search(r'ch(\d+)',f).group(1)
    for ln,line in enumerate(open(f,encoding='utf-8'),1):
        s=line.strip()
        if not s or s[0] in '@#': continue
        m=ROLE.match(s); text=m.group(2) if m else s
        toks=list(TOK.finditer(text))
        for k,mt in enumerate(toks):
            t=mt.group(0).strip('-'); tl=t.lower(); form=tl.replace('+','')
            if '+' not in tl: continue
            if not (sum(c in VOW for c in form)>=2 or 'е' in form or 'ё' in form): continue
            v=py(form)
            if not v or norm(tl) in {norm(x) for x in v}: continue
            a=max(0,k-7); b=min(len(toks),k+8)
            ctx=text[toks[a].start():mt.start()]+'**'+mt.group(0)+'**'+text[mt.end():toks[b-1].end()]
            ctx=('…' if a>0 else '')+ctx.replace('|','/')+('…' if b<len(toks) else '')
            occ.append(dict(ch=ch,ln=ln,orig=t,low=tl,opts=list(v.keys()),pos=v,ctx=ctx))
g=collections.OrderedDict()
for o in occ: g.setdefault(o['low'],[]).append(o)
json.dump(occ,open('/tmp/flag_occ.json','w'),ensure_ascii=False)
print('occurrences',len(occ),'groups',len(g))
for low,L in sorted(g.items(),key=lambda kv:-len(kv[1])):
    print(len(L),low,'->',' / '.join(f"{s} {','.join(p)}" for s,p in L[0]['pos'].items()),'|',L[0]['ctx'][:90])

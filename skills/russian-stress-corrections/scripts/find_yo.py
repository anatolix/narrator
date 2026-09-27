import re, glob, json
from collections import defaultdict
B='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace/narrator/books/fine-structure-roles_full'
def load(fn):
    d=defaultdict(set)
    for ln in open(fn,encoding='utf-8'):
        ln=ln.split('#')[0].strip().lstrip('_')
        if not ln: continue
        m=re.match(r'^([^(]*)\(([^)]*)\)(.*)$',ln)
        forms=[m.group(1)+e+m.group(3) for e in m.group(2).split('|')] if m else [ln]
        for f in forms:
            f=f.lower()
            if 'ё' in f: d[f.replace('ё','е')].add(f)
    return d
S=load('safe.txt'); U=load('not_safe.txt')
tok=re.compile(r'[А-Яа-яЁё+]+(?:-[А-Яа-яЁё+]+)*')
hits=defaultdict(list)
for f in sorted(glob.glob(B+'/roles_full-ch*.md')):
    ch=re.search(r'ch(\d+)',f).group(1)
    for n,line in enumerate(open(f,encoding='utf-8'),1):
        if line.startswith('@') or line.startswith('#'): continue
        body=line.split(':',1)[1] if re.match(r'^[А-ЯЁA-Z ]+:',line) else line
        off=len(line)-len(body)
        for m in tok.finditer(body):
            raw=m.group(0); w=raw.replace('+','').lower()
            if 'е' not in w: continue
            for kind,D in (('safe',S),('unsafe',U)):
                for cand in D.get(w,()):
                    # stress: index of vowel after '+'
                    st=None;c=0
                    for i,chh in enumerate(raw):
                        if chh=='+': st=c
                        else: c+=1
                    yo=cand.index('ё')
                    s=off+m.start()
                    ctx=line[max(0,s-70):s+len(raw)+50].replace('+','').replace('\n','')
                    hits[(kind,w,cand)].append(dict(ch=ch,ln=n,raw=raw,st_yo=(st==yo),st_none=(st is None),ctx=ctx))
out=[dict(kind=k,e=w,yo=c,n=len(L),occ=L) for (k,w,c),L in hits.items()]
out.sort(key=lambda o:(o['kind'],-o['n']))
json.dump(out,open('yo_candidates.json','w'),ensure_ascii=False,indent=1)
for k in ('safe','unsafe'):
    O=[o for o in out if o['kind']==k]
    print(k,'types',len(O),'occ',sum(o['n'] for o in O))
print('--- SAFE')
for o in out:
    if o['kind']=='safe': print(o['n'],sum(x['st_yo'] for x in o['occ']),o['e'],'->',o['yo'],'|',o['occ'][0]['ch']+':'+str(o['occ'][0]['ln']))
print('--- UNSAFE')
for o in out:
    if o['kind']=='unsafe': print(o['n'],sum(x['st_yo'] for x in o['occ']),o['e'],'->',o['yo'])

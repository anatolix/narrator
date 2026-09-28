# Merge 3 resolve runs: unanimous -> resolved; 2:1 on one form -> majority (listed); else -> brackets + review
import json,sys,os,re,collections
sys.argv=['x',sys.argv[1] if len(sys.argv)>1 else '01']
exec(open('resolve.py').read().split("if os.environ.get('DRY')")[0])
T={t['id']:t for t in toks}
def load(f):
    a={}
    if os.path.exists(f):
        for v in json.load(open(f)).values(): a.update(v)
    return a
runs=[load(f'{ST}/resolve-ch{CH}.cache.json'),load(f'{ST}/resolve2-ch{CH}.cache.json'),load(f'{ST}/resolve3-ch{CH}.cache.json')]
def snip(line,s):
    m=re.search(r'(?<![А-Яа-яЁё])'+re.escape(s)+r'(?![А-Яа-яЁё])',line); p=m.start() if m else 0
    return '…'+line[max(0,p-90):p+len(s)+90]+'…'
A=[];B=[];st=collections.Counter()
for i in amb:
    t=T[i]; order=[c['form'] for c in t['cands']]; forms=set(order); ks=[];whys=[]
    for r in runs:
        a=r.get(str(i))
        if not a: ks.append(None); continue
        k=tuple(sorted(set(norm(x) for x in a.get('keep',[]) if norm(x) in forms)))
        ks.append(k or None); whys.append(a.get('why',''))
    good=[k for k in ks if k]; cnt=collections.Counter(good)
    sh=lambda k:', '.join(apply(f,t['s']) for f in k) if k else '—'
    votes='; '.join(f'прогон {n+1}: {sh(k)}' for n,k in enumerate(ks))
    why=next((w for w in whys if w),'')
    ctx=snip(S[t['line']-1],t['s'])
    if not good: t['res']=order; st['noanswer']+=1; A.append((t,votes,'нет ответа',ctx)); continue
    top,c=cnt.most_common(1)[0]
    if len(cnt)==1 and len(top)==1: t['res']=list(top); st['unanimous']+=1
    elif len(cnt)==1: t['res']=[f for f in order if f in top]; st['all_keep_multi']+=1; A.append((t,votes,why,ctx))
    elif c>=2 and len(top)==1: t['res']=list(top); st['majority']+=1; B.append((t,votes,why,ctx))
    else:
        u=set().union(*good); t['res']=[f for f in order if f in u]; st['diverged']+=1; A.append((t,votes,why,ctx))
rev=[f'# Глава {CH} — ударения на проверку\n',f'Три прогона Sonnet (1-й со старым промптом «выбери один», 2-й и 3-й с «оставь все допустимые»).\n',f'## Нужно решить: {len(A)}\nВ тексте главы эти слова стоят в скобках со всеми вариантами.\n']
for t,v,w,ctx in A: rev.append(f"- **L{t['line']}** «{t['s']}» → [{', '.join(apply(f,t['s']) for f in t['res'])}]\n  - {v}" + (f"\n  - почему: {w}" if w else '') + f"\n  > {ctx}")
rev.append(f'\n## Решено большинством 2:1: {len(B)}\nВ тексте стоит вариант большинства. Глянь, согласен ли.\n')
for t,v,w,ctx in B: rev.append(f"- **L{t['line']}** «{t['s']}» → {apply(t['res'][0],t['s'])}\n  - {v}\n  > {ctx}")
res=[]
for l in lines:
    if 'raw' in l: res.append(l['raw']); continue
    o=l['pre']
    for p in l['parts']:
        if isinstance(p,int):
            t=T[p]; fs=[apply(f,t['s']) for f in t['res']]
            o+=fs[0] if len(fs)==1 else '['+', '.join(fs)+']'
        else: o+=p
    res.append(o)
txt='\n'.join(res)+'\n'
chk=re.sub(r'\[([^\],\]]+)(?:, [^\]]+)?\]',r'\1',txt)
nz=lambda x:x.replace('+','').replace('ё','е').replace('Ё','Е')
st['verbatim']=nz(chk).rstrip()==nz('\n'.join(S[:len(M)])+'\n').rstrip()
uns=[(t['line'],t['s']) for t in toks if len(t['res'])==1 and nv(t['s'])>1 and '+' not in t['res'][0]]
st['auto']=len(toks)-len(amb); st['amb']=len(amb); st['unstressed']=len(uns)
open(f'{OUT}/ch{CH}.md','w',encoding='utf-8').write(txt)
open(f'{OUT}/ch{CH}-review.md','w',encoding='utf-8').write('\n'.join(rev)+'\n')
print('VOTE',dict(st)); print('UNSTRESSED',uns[:40])

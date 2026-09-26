import json,re,glob,collections
W='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace'
S=W+'/scratch/suspect'; D=W+'/narrator/books/fine-structure-roles_full'
res=json.load(open(S+'/verdicts.json'))
SKIP_REF={('утр+а','ch16:59')}  # откат Анатолия
def recase(orig,t):
    p=orig.replace('+',''); out='';j=0
    for ch in t:
        if ch=='+': out+='+'
        else: out+=(p[j] if j<len(p) and p[j].lower()==ch.lower() else (ch.upper() if j<len(p) and p[j].isupper() else ch)); j+=1
    return out
WRONG={r['variant']:r['fix'] for r in res if r['verdict']=='wrong' and r.get('fix')}
MIX=collections.defaultdict(dict)
for r in res:
    if r['verdict']=='mixed' and r.get('fix'):
        for ref in r.get('bad') or []:
            if (r['variant'],ref) in SKIP_REF: continue
            MIX[ref][r['variant']]=r['fix']
B=r'(?<![А-Яа-яЁё+\-])'; A=r'(?![А-Яа-яЁё+\-])'
def rx(m): return re.compile(B+'('+'|'.join(re.escape(k) for k in sorted(m,key=len,reverse=True))+')'+A, re.I)
RW=rx(WRONG)
cnt=collections.Counter(); mixhit=collections.Counter(); multi=[]; chs=set()
for f in sorted(glob.glob(D+'/roles_full-ch*.md')):
    ch='ch'+re.search(r'ch(\d+)',f).group(1); L=open(f,encoding='utf-8').read().split('\n'); ch_changed=False
    for i,l in enumerate(L):
        s=l.strip()
        if not s or s[0] in '@#': continue
        ref=f'{ch}:{i+1}'; m=dict(WRONG); local=MIX.get(ref,{})
        m.update(local)
        R=rx(m) if local else RW
        def sub(mt):
            v=mt.group(1).lower(); cnt[('M' if v in local else 'W',v)]+=1
            if v in local: mixhit[(ref,v)]+=1
            return recase(mt.group(1),m[v])
        n=R.sub(sub,l)
        if n!=l: L[i]=n; ch_changed=True
    if ch_changed: open(f,'w',encoding='utf-8').write('\n'.join(L)); chs.add(ch)
miss=[(ref,v) for ref,d in MIX.items() for v in d if not mixhit[(ref,v)]]
multi=[(k,c) for k,c in mixhit.items() if c>1]
print('wrong variants',len(WRONG),'replacements',sum(c for (t,_),c in cnt.items() if t=='W'),'variants hit',len({v for t,v in cnt if t=='W'}))
print('wrong not found:',[v for v in WRONG if not cnt[('W',v)]])
print('mixed refs',sum(len(d) for d in MIX.values()),'hit',len(mixhit),'miss',miss,'multi-in-line',multi)
print('chapters',' '.join(sorted(chs)))
# остатки
t=''.join(open(f,encoding='utf-8').read() for f in glob.glob(D+'/roles_full-ch*.md'))
print('leftover wrong:',[v for v in WRONG if RW.pattern and re.search(B+re.escape(v)+A,t,re.I)][:10])
# exceptions: закомментировать старые правила, чья правая часть = старый неверный вариант
e=D+'/exceptions.txt'; E=open(e,encoding='utf-8').read().split('\n'); off=[]
for i,l in enumerate(E):
    if l.startswith('#') or '->' not in l: continue
    rhs=l.split('->',1)[1].split('#')[0].strip().lower()
    if rhs in WRONG: E[i]='# ОТМЕНЕНО 26.09 (вердикт Opus, Анатолий ок): '+l; off.append(l)
E+=['# === 26.09 suspected_verdicts.md: wrong — везде (Анатолий ок) ===']+[f'{v} -> {x}  # ×{cnt[("W",v)]}' for v,x in WRONG.items() if cnt[('W',v)]]
E+=['# === 26.09 suspected_verdicts.md: mixed — ТОЛЬКО по позициям, не глобально ===']+[f'# {ref}: {v} -> {x}' for ref,d in sorted(MIX.items()) for v,x in d.items() if mixhit[(ref,v)]]
open(e,'w',encoding='utf-8').write('\n'.join(E)+'\n')
print('exceptions: disabled',off)

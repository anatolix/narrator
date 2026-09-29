# Group A of yo-check: obligatory ё — replace stressed е with ё at aligned positions
import re,glob
N=lambda s:s.replace('+','').lower().replace('ё','е')
BR=re.compile(r'\[[^\[\]]+\]'); RT=re.compile(r'\[[^\[\]]+\]|[А-Яа-яЁё+][А-Яа-яЁё+\-]*'); ROLE=re.compile(r'^[А-ЯЁA-Z0-9_ ]{1,30}:\s*')
A={'ее','свое','твое','нее','своем','желтого','зеленого','придется','распределенных','искаженной'}
tot=0
for f in sorted(glob.glob('resolved/ch[0-9][0-9].md')):
    ch=f[-5:-3]; R=open(f,encoding='utf-8').read().split('\n'); C=open(f'ch{ch}.md',encoding='utf-8').read().split('\n')
    for i,(r,c) in enumerate(zip(R,C),1):
        m=ROLE.match(r); off=m.end() if m else 0
        cb=BR.findall(ROLE.sub('',c)); rts=list(RT.finditer(r[off:]))
        if not cb or len(rts)!=len(cb): continue
        reps=[]
        for b,mt in zip(cb,rts):
            t=mt.group(0)
            if t.startswith('[') or 'ё' in t.lower() or N(t) not in A: continue
            pieces=[p.split(':')[0].strip() for p in re.split(r'[,;]',b.strip('[]'))]
            if N(t)!=N(pieces[0]) or not any('ё' in p.lower() for p in pieces): continue
            new=t.replace('+е','+ё').replace('+Е','+Ё')
            if new==t: print('no stress',ch,i,t); continue
            reps.append((mt.start()+off,mt.end()+off,new))
        old=r
        for a,b2,s in reversed(reps): r=r[:a]+s+r[b2:]
        assert N(old)==N(r); R[i-1]=r; tot+=len(reps)
    open(f,'w',encoding='utf-8').write('\n'.join(R))
print('group A replaced',tot)

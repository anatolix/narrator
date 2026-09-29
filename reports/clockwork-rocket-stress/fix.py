# usage: fix.py "фраза из книги" слово ударение  — ставит ударение этому слову во всех местах, где встречается фраза
import sys,re,glob,json,os
phrase,word,stressed=sys.argv[1],sys.argv[2],sys.argv[3]
N=lambda s:s.replace('+','').lower().replace('ё','е')
tokrx=re.compile(r'\[[^\[\]]+\]|[А-Яа-яЁё+\-]+|[^А-Яа-яЁё+\[\-]+')
ph=N(phrase).split(); wi=[N(x) for x in ph].index(N(word))
DF='rules_done.json'; done=json.load(open(DF)) if os.path.exists(DF) else []
hits=0
for f in sorted(glob.glob('resolved/ch[0-9][0-9].md')):
    ch=f[-5:-3]; L=open(f,encoding='utf-8').read().split('\n'); ch_changed=False
    for n,l in enumerate(L,1):
        mp=re.match(r'^[А-ЯЁA-Z0-9_ ]{1,30}:\s*',l); pfx=mp.group(0) if mp else ''; l=l[len(pfx):]
        toks=tokrx.findall(l); words=[i for i,t in enumerate(toks) if re.match(r'[\[А-Яа-яЁё+]',t)]
        base=[N(toks[i].strip('[]').split(', ')[0]) for i in words]
        for k in range(len(words)-len(ph)+1):
            if base[k:k+len(ph)]==ph:
                i=words[k+wi]; src=toks[i].strip('[]').split(', ')[0]
                toks[i]=stressed[0].upper()+stressed[1:] if src.replace('+','')[:1].isupper() else stressed
                hits+=1; done.append([ch,n,N(word)]); print(f'ch{ch}:{n}', ''.join(toks)[:0] or ''.join(toks[max(0,words[k]-1):words[min(len(words)-1,k+len(ph)-1)]+1]))
        new=pfx+''.join(toks); l=pfx+l
        if new!=l: L[n-1]=new; ch_changed=True
    if ch_changed: open(f,'w',encoding='utf-8').write('\n'.join(L))
json.dump(done,open(DF,'w'),ensure_ascii=False); print('hits',hits)

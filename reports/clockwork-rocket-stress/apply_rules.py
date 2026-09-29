# Blanket stress rules over resolved/chNN.md (Anatoly, Sep 29):
#  самом/самой/самого -> с+ам.. (except pronoun use: before себя/себе/собой or a Name); должно -> должн+о; одновременно -> одновр+еменно
import re,glob,json,collections
T={'самом':'с+амом','самой':'с+амой','самого':'с+амого','должно':'должн+о','одновременно':'одновр+еменно'}
PRON={'себя','себе','собой','собою'}
W=r'[А-Яа-яЁё+]+'
tok=re.compile(r'\[([^\[\]]+)\]|('+W+r')')
def norm(s): return s.replace('+','').lower()
def case(src,new): return new[0].upper()+new[1:] if src.replace('+','')[:1].isupper() else new
def base(line): return re.sub(r'\[([^,\]]+)(?:, [^\]]+)*\]',lambda m:m.group(1),line).replace('+','').lower().replace('ё','е')
exc=[];stat=collections.Counter()
for f in sorted(glob.glob('resolved/ch[0-9][0-9].md')):
    ch=re.search(r'ch(\d+)',f).group(1); L=open(f,encoding='utf-8').read().split('\n'); out=[]
    for i,line in enumerate(L,1):
        ms=list(tok.finditer(line)); res=[]; pos=0
        for k,m in enumerate(ms):
            word=m.group(1).split(', ')[0] if m.group(1) else m.group(2)
            n=norm(word)
            if n not in T: continue
            if m.group(1) and not all(norm(x)==n for x in m.group(1).split(', ')): continue
            nxt=None
            for m2 in ms[k+1:]:
                nxt=(m2.group(1).split(', ')[0] if m2.group(1) else m2.group(2)); break
            if n.startswith('сам') and nxt and (norm(nxt) in PRON or (nxt.replace('+','')[:1].isupper() and line[m.end():m2.start()].strip()=='' )):
                exc.append([ch,i,word.replace('+','')]); stat['exception']+=1; continue
            res.append((m.start(),m.end(),case(word,T[n]))); stat[n]+=1
        for a,b,s in reversed(res): line=line[:a]+s+line[b:]
        out.append(line)
    assert len(out)==len(L)
    for a,b in zip(L,out): assert base(a)==base(b),(f,a[:80])
    open(f,'w',encoding='utf-8').write('\n'.join(out))
json.dump(exc,open('rules_exceptions.json','w'),ensure_ascii=False)
print(dict(stat)); print('exceptions',exc)

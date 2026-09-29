# All proper names in all forms: stress per form, flag groups where stressed vowel position differs
import re,glob,collections
ROLE=re.compile(r'^[А-ЯЁA-Z0-9_ ]{1,30}:\s*'); TOK=re.compile(r'\[[^\[\]]+\]|[А-Яа-яЁё+][А-Яа-яЁё+\-]*')
V='аеёиоуыэюяАЕЁИОУЫЭЮЯ'
END=['иями','иях','ией','ием','ии','ия','ию','ой','ей','ом','ем','ам','ям','ах','ях','ою','ею','а','я','ы','и','у','ю','е','о']
base=lambda t:t.strip('[]').split(', ')[0].replace('+','')
def stem(b):
    for e in END:
        if b.lower().endswith(e) and len(b)-len(e)>=3: return b[:-len(e)]
    return b
def sv(t):  # stressed vowel number (1-based) of first variant, 0 if none
    t=t.strip('[]').split(', ')[0]
    if '+' not in t:
        return ([i for i,ch in enumerate([c for c in t if c in V],1) if ch in 'ёЁ'] or [0])[0]
    return sum(c in V for c in t[:t.index('+')])+1
occ=collections.defaultdict(list); lower=set(); mid=set()
for f in sorted(glob.glob('resolved/ch[0-9][0-9].md')):
    for n,l in enumerate(open(f,encoding='utf-8').read().split('\n'),1):
        l=ROLE.sub('',l)
        for m in TOK.finditer(l):
            t=m.group(0); b=base(t)
            if not b: continue
            if b[0].islower(): lower.add(b.lower()); continue
            if b.isupper() and len(b)>1: continue
            pre=l[:m.start()].rstrip(' «“"(\'')
            if pre and pre[-1] not in '.!?…:—–-': mid.add(b.lower())
            occ[b.lower()].append((t,f[-7:-3],n))
names={b for b in mid if b not in lower}
grp=collections.defaultdict(lambda:collections.defaultdict(list))
for b in names:
    for t,ch,n in occ[b]: grp[stem(b).lower()][t].append(f'{ch}:{n}')
bad=[];ok=[]
for s,forms in grp.items():
    pos={sv(t) for t in forms}; br=any(t.startswith('[') for t in forms); ns=0 in pos
    (bad if len(pos)>1 or br or ns else ok).append((s,forms))
out=['# Заводная ракета — имена во всех формах','',f'Групп {len(grp)}, из них с разнобоем/без ударения/в скобках: {len(bad)}.','','## ⚠ Разнобой (разный ударный слог в разных формах), скобки или нет ударения','']
for s,forms in sorted(bad,key=lambda x:-sum(map(len,x[1].values()))):
    out.append(f'### {s}… — '+'; '.join(f'{t} ×{len(v)} ({v[0]})' for t,v in sorted(forms.items(),key=lambda x:-len(x[1]))))
out+=['','## Единообразно (проверь на слух, если имя звучит странно)','']
for s,forms in sorted(ok,key=lambda x:-sum(map(len,x[1].values()))):
    out.append(f'- '+'; '.join(f'{t} ×{len(v)}' for t,v in sorted(forms.items(),key=lambda x:-len(x[1]))))
open('names-check.md','w',encoding='utf-8').write('\n'.join(out))
print('groups',len(grp),'bad',len(bad))
for s,forms in sorted(bad,key=lambda x:-sum(map(len,x[1].values()))): print(' ; '.join(f'{t}×{len(v)}' for t,v in sorted(forms.items(),key=lambda x:-len(x[1]))))
print('--- ok top'); print(' | '.join('; '.join(f'{t}×{len(v)}' for t,v in sorted(forms.items(),key=lambda x:-len(x[1]))) for s,forms in sorted(ok,key=lambda x:-sum(map(len,x[1].values())))[:60]))

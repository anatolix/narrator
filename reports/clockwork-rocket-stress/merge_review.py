# Merge per-chapter review files into one list grouped by word, with context
import re,glob,collections
items=[]
for f in sorted(glob.glob('resolved/ch*-review.md')):
    ch=re.search(r'ch(\d+)',f).group(1); sec=None; cur=None
    for l in open(f,encoding='utf-8'):
        l=l.rstrip('\n')
        if l.startswith('## '): sec='decide' if 'решить' in l else 'maj'; continue
        m=re.match(r'- \*\*L(\d+)\*\* «(.+?)» → (.*)',l)
        if m:
            cur=dict(ch=ch,line=int(m.group(1)),word=m.group(2),pick=m.group(3).strip(),sec=sec,runs='',why='',ctx=''); items.append(cur); continue
        if cur is None: continue
        s=l.strip()
        if s.startswith('- прогон'): cur['runs']=s[2:]
        elif s.startswith('- почему:'): cur['why']=s[9:].strip()
        elif s.startswith('>'): cur['ctx']=s[1:].strip()
def variants(it):
    v=set(re.findall(r'[\w+\-ёЁ]*\+[\w+\-ёЁ]*',it['pick']+' '+it['runs']))
    return v
import json,os
RULE={'самом','самой','самого','должно','одновременно'}
EXC={(c,l) for c,l,w in json.load(open('rules_exceptions.json'))} if os.path.exists('rules_exceptions.json') else set()
items=[it for it in items if it['word'].lower() not in RULE or (it['ch'],it['line']) in EXC]
DONE={(c,l,w) for c,l,w in json.load(open('rules_done.json'))} if os.path.exists('rules_done.json') else set()  # decided by Anatoly
DONE|={('03',317,'все'),('05',83,'все')}
items=[it for it in items if (it['ch'],it['line'],it['word'].lower().replace('ё','е')) not in DONE]
items=[it for it in items if (it['ch'],it['line'],it['word'].lower()) not in DONE]
g=collections.defaultdict(list)
for it in items: g[it['word'].lower().replace('ё','е')].append(it)
out=['# Заводная ракета — ударения на проверку, сводный список','',f'Всего {len(items)} мест, {len(g)} разных слов. Отсортировано по частоте.','','Обозначения: **❓** — прогоны разошлись, в тексте стоят все варианты в скобках; **2:1** — в тексте стоит вариант большинства.','']
for w,its in sorted(g.items(),key=lambda x:(-len(x[1]),x[0])):
    vs=set()
    for it in its: vs|=variants(it)
    picks=collections.Counter(it['pick'] for it in its)
    nd=sum(it['sec']=='decide' for it in its)
    out.append(f'## {its[0]["word"]} — {len(its)} (❓{nd} / 2:1 {len(its)-nd})')
    out.append('Варианты: '+', '.join(sorted(vs))+'  ')
    out.append('Сейчас в тексте: '+'; '.join(f'{p} ×{n}' for p,n in picks.most_common()))
    whys=[it['why'] for it in its if it['why']]
    if whys: out.append(f'Модель: {whys[0]}')
    out.append('')
    for it in sorted(its,key=lambda x:(x['ch'],x['line'])):
        mark='❓' if it['sec']=='decide' else '2:1'
        out.append(f'- **ch{it["ch"]}:{it["line"]}** {mark} → {it["pick"]}  ({it["runs"]})')
        out.append(f'  > {it["ctx"]}')
    out.append('')
import json as _j
YO=_j.load(open('yo_review.json')) if os.path.exists('yo_review.json') else []
YO=[x for x in YO if (x[0],x[1],x[2]) not in DONE]
if YO:
    out.append(f'# ё под вопросом — {len(YO)} мест (ruaccent/pylem давали ё, в тексте е, прогоны единогласны)'); out.append('')
    gy=collections.defaultdict(list)
    for x in YO: gy[x[2]].append(x)
    for w,its in sorted(gy.items(),key=lambda x:-len(x[1])):
        out.append(f'## ё? {w} — {len(its)}'); out.append('Варианты с ё: '+', '.join(sorted({y for x in its for y in x[4]}))); out.append('')
        for ch,l,w2,t,yo,ctx in its: out.append(f'- **ch{ch}:{l}** сейчас {t}'); out.append(f'  > …{ctx}…')
        out.append('')
print('yo',len(YO))
open('review-all.md','w',encoding='utf-8').write('\n'.join(out))
print(len(items),'items',len(g),'words'); print([(w,len(v)) for w,v in sorted(g.items(),key=lambda x:-len(x[1]))[:25]])

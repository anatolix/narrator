# Resolve stress candidates by context with Sonnet. Text stays verbatim; model only picks among candidates.
import re,sys,os,json,subprocess,time,difflib
from concurrent.futures import ThreadPoolExecutor
import pylem
W='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace'
ST=W+'/art/new-books/stress'
CH=sys.argv[1] if len(sys.argv)>1 else '01'
SRC=f'{W}/narrator/books/clockwork-rocket-roles/roles-ch{CH}.md'
MK=f'{ST}/ra_marked/roles_full-ch{CH}.md'
OUT=f'{W}/narrator/reports/clockwork-rocket-stress/resolved'; os.makedirs(OUT,exist_ok=True)
CACHEF=f"{ST}/resolve{os.environ.get('RUN','2')}-ch{CH}.cache.json"
cs=open(ST+'/compare.py').read()
exec(cs[cs.index('POS='):cs.index('CACHE={}')])
exec(cs[cs.index('LOST=[0]'):cs.index('def conv(')])
H=pylem.MorphanHolder(pylem.MorphLanguage.Russian)
role=re.compile(r'^([А-ЯЁA-Z0-9_ ]{1,30}:)\s*(.*)$')
VOW=set('аеёиоуыэюя')
def L(f): return f.replace('+','')
def nv(w): return sum(c in VOW for c in w.lower())
PART={'кое','нибудь','либо','то','таки','ка'}
def norm(f):
    f=f.lower()
    if '-' in f: f='-'.join(x.replace('+','') if x.replace('+','') in PART else x for x in f.split('-'))
    return L(f) if nv(L(f))<=1 else f
def gram(g): return ' '.join(GR.get(x,x) for x in g.split(',') if x)
def pyl(w):
    try: res=H.accent(w.lower(),all_forms=False)
    except Exception: return []
    out=[]
    for hom in res or []:
        if not hom.get('found',True): continue
        for f in hom.get('forms',[]):
            if f.get('isInput',True) and f.get('stressed'):
                out.append((f['stressed'],(POS.get(f.get('pos'),f.get('pos','?'))+' '+gram(f.get('grammems',''))).strip()))
    return out
def apply(f,s):
    fl=L(f)
    if len(fl)!=len(s): return None
    st=set();k=0
    for ch in f:
        if ch=='+': st.add(k)
        else: k+=1
    o=[]
    for i,c in enumerate(s):
        if i in st and nv(s)>1: o.append('+')
        if fl[i] in 'ёЁ' and c in 'еЕ': c='ё' if c=='е' else 'Ё'
        o.append(c)
    return ''.join(o)
S=open(SRC,encoding='utf-8').read().split('\n'); M=open(MK,encoding='utf-8').read().rstrip('\n').split('\n')
lines=[];toks=[];amb=[]
for i,ml in enumerate(M):
    sl=S[i] if i<len(S) else ''
    if not sl.strip() or sl.lstrip().startswith(('@','#')): lines.append({'raw':sl}); continue
    ms=role.match(sl); pre,sb=(ms.group(1)+' ',ms.group(2)) if ms else ('',sl)
    mm=role.match(ml); mb=mm.group(2) if mm else ml
    if not WORD.search(sb): lines.append({'raw':sl}); continue
    rb=realign(mb,sb); rt=list(WORD.finditer(rb)); stt=list(WORD.finditer(sb))
    parts=[];pos=0
    for j,m in enumerate(stt):
        parts.append(sb[pos:m.start()]); pos=m.end(); s=m.group(0)
        r=rt[j].group(0) if len(rt)==len(stt) else s
        ra=[r.replace('ё','е').replace('Ё','Е'),r] if ('ё' in r.lower() and 'ё' not in s.lower()) else [r]
        c={}
        for f in ra:
            if nv(L(f))>1 and '+' not in f: continue
            if apply(f,s) is None: continue
            c.setdefault(norm(f),{'form':norm(f),'src':[]})['src'].append('ruaccent')
        for f,g in pyl(s):
            if nv(L(f))>1 and '+' not in f: continue
            if apply(f,s) is None: continue
            e=c.setdefault(norm(f),{'form':norm(f),'src':[]})
            if 'pylem: '+g not in e['src']: e['src'].append('pylem: '+g)
        t={'id':len(toks),'s':s,'line':i+1,'cands':list(c.values())}
        if not c: t['res']=[s]
        elif len(c)==1: t['res']=[t['cands'][0]['form']]
        else: amb.append(t['id'])
        toks.append(t); parts.append(t['id'])
    parts.append(sb[pos:]); lines.append({'pre':pre,'parts':parts,'plain':sl,'n':i+1})
print('tokens',len(toks),'ambiguous',len(amb),flush=True)
if os.environ.get('DRY'): sys.exit()
SYS='''Ты эксперт по русской орфоэпии. Перед тобой фрагмент главы русского перевода романа Грега Игана «Заводная ракета», готовим аудиокнигу. Для пронумерованных слов даны варианты ударения («+» перед ударной гласной): от нейросети ruaccent и из словаря Зализняка (pylem) с частью речи и граммемами.
Задача: выкинуть варианты, которые контекст ИСКЛЮЧАЕТ, и оставить все, которые контекст ДОПУСКАЕТ.
- Один вариант оставляй, только когда остальные в этом предложении невозможны: не тот падеж, число, род, часть речи, смысл.
- Если предложение допускает два толкования (например, род. ед. и им. мн.; наречие и краткое прилагательное; «все» и «всё»; разные значения слова) — оставь ОБА и в why коротко напиши, чем они различаются. Человек посмотрит сам. Не угадывай: лучше оставить лишний вариант, чем молча выбрать не тот.
- Буква ё. В книге ё часто не напечатана. Если вариант с ё и вариант с е — это одно и то же слово, а без ё такого произношения в русском просто нет (еще/ещё, ее/её, черный/чёрный, вперед/вперёд, тяжелый/тяжёлый), оставь только вариант с ё. Выбор между ними — не спор. Спор только там, где с е и с ё — РАЗНЫЕ слова (все/всё, небо/нёбо, осел/осёл): там решай по смыслу, а при сомнении оставляй оба.
- Словарь pylem иногда даёт ударение не на ё в словах с ё — это ошибка словаря, если ё есть, ударение на ней.
- Имена и выдуманные слова мира в книге нормальны.
- Копируй варианты в keep ТОЧНО как в списке.
Ответ строго JSON без пояснений вокруг: {\"17\":{\"keep\":[\"з+амок\"]},\"18\":{\"keep\":[\"стекл+а\",\"ст+екла\"],\"why\":\"род. ед. или им. мн.: оба подходят\"}} — все номера обязательно.'''
T={t['id']:t for t in toks}
L2=[l for l in lines if 'parts' in l]
chunks=[];cur=[];na=0
for k,l in enumerate(L2):
    a=sum(1 for p in l['parts'] if isinstance(p,int) and p in amb and 0 or (isinstance(p,int) and 'res' not in T[p]))
    cur.append(k);na+=a
    if na>=70: chunks.append(cur);cur=[];na=0
if cur: chunks.append(cur)
def render(ks):
    ctx=[L2[j]['plain'] for j in range(max(0,ks[0]-3),ks[0])]
    out=['КОНТЕКСТ ДО (не размечать):']+ctx+['','РАЗМЕТИТЬ:']; ids=[]
    for j in ks:
        l=L2[j]; txt=''; items=[]
        for p in l['parts']:
            if isinstance(p,int):
                t=T[p]; txt+=t['s']
                if 'res' not in t:
                    txt+=f'⟦{p}⟧'; ids.append(p)
                    items.append(f"  {p} «{t['s']}»: "+' | '.join(f"{c['form']} ({'; '.join(c['src'])})" for c in t['cands']))
            else: txt+=p
        out.append(f"L{l['n']}: {l['pre']}{txt}"); out+=items
    return '\n'.join(out),ids
cache=json.load(open(CACHEF)) if os.path.exists(CACHEF) else {}
def run(ci):
    key=str(ci)
    if key in cache: return
    msg,ids=render(chunks[ci])
    if not ids: cache[key]={}; return
    best={}
    for prof in ('claude-code-sonnet','claude-code-sonnet','balanced'):
        try:
            p=subprocess.run(['assistant','inference','send','--profile',prof,'--timeout-seconds','900','--max-tokens','16000','--system-prompt',SYS],input=msg,capture_output=True,text=True,timeout=960)
            o=p.stdout; j=json.loads(o[o.index('{'):o.rindex('}')+1])
            got={k:v for k,v in j.items() if k.isdigit() and int(k) in ids}
            if len(got)>len(best): best=got
            if len(best)>=len(ids)*0.97: break
            print('chunk',ci,prof,'partial',len(got),'/',len(ids),flush=True)
        except Exception as e: print('chunk',ci,prof,'fail',repr(e)[:150],(p.stderr[-150:] if 'p' in dir() else ''),flush=True)
        time.sleep(5)
    cache[key]=best; print('chunk',ci,'done',len(best),'/',len(ids),flush=True)
    json.dump(cache,open(CACHEF,'w'),ensure_ascii=False)
print('chunks',len(chunks),flush=True)
with ThreadPoolExecutor(8) as ex: list(ex.map(run,range(len(chunks))))
ans={}
for v in cache.values(): ans.update(v)
stat={'auto':len(toks)-len(amb),'amb':len(amb),'one':0,'multi':0,'noanswer':0,'badpick':0}
review=[f'# Глава {CH} — слова, где нужен твой взгляд\n']
for i in amb:
    t=T[i]; forms={c['form'] for c in t['cands']}; a=ans.get(str(i))
    if not a: t['res']=[c['form'] for c in t['cands']]; stat['noanswer']+=1; why='модель не ответила'
    else:
        keep=[norm(k) for k in a.get('keep',[]) if norm(k) in forms]
        if not keep: keep=[c['form'] for c in t['cands']]; stat['badpick']+=1
        t['res']=list(dict.fromkeys(keep)); why=a.get('why','')
    if len(t['res'])==1: stat['one']+=1
    else:
        stat['multi']+=1; ctx=S[t['line']-1]
        review.append(f"- **L{t['line']}** «{t['s']}» → {' / '.join(apply(f,t['s']) for f in t['res'])} — {why}\n  > {ctx[:300]}")
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
src_txt='\n'.join(S[:len(M)])+'\n'
stat['verbatim']=nz(chk).rstrip()==nz(src_txt).rstrip()
open(f'{OUT}/ch{CH}.md','w',encoding='utf-8').write(txt)
open(f'{OUT}/ch{CH}-review.md','w',encoding='utf-8').write('\n'.join(review)+'\n')
print('STATS',stat,flush=True)
print('ALL DONE',flush=True)

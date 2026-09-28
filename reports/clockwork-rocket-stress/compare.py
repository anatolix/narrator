# Build per-chapter comparison: every word -> [ruaccent form(s), pylem forms: POS grammemes; ...]
import re,sys,os,json,glob
import pylem
H=pylem.MorphanHolder(pylem.MorphLanguage.Russian)
POS={'N':'сущ','A':'прил','V':'гл','ADV':'нар','PRON':'мест','PN':'мест','PN_ADJ':'мест-прил','NUMERAL':'числ','NUMERAL_P':'числ-прил','PREP':'предл','CONJ':'союз','PARTICLE':'част','INTERJ':'межд','PARTICIPLE':'прич','ADVERB_PARTICIPLE':'дееприч','INFINITIVE':'инф','PREDK':'предик','A_SHORT':'кр прил','PARTICIPLE_SHORT':'кр прич','ADJ_SHORT':'кр прил','INT':'межд','P':'мест','PA':'мест-прил','NUM':'числ','PRED':'предик','PART':'част','ADVPART':'дееприч','INF':'инф','PRT':'прич','Q':'част'}
GR={'nom':'им','gen':'род','dat':'дат','acc':'вин','ins':'тв','loc':'пр','prp':'пр','voc':'зв','sg':'ед ч','pl':'мн ч','mas':'м','fem':'ж','neu':'ср','past':'прош','pres':'наст','fut':'буд','1p':'1л','2p':'2л','3p':'3л','imp':'пов','perf':'сов','impf':'несов','comp':'сравн','supr':'прев','anim':'одуш','inanim':'неод','act':'действ','pass':'страд','short':'кр'}
WORD=re.compile(r"[А-Яа-яЁё+]+(?:-[А-Яа-яЁё+]+)*")
CACHE={}
def gram(g): return ' '.join(GR.get(x,x) for x in g.split(',') if x)
def py(word):
    k=word.lower()
    if k in CACHE: return CACHE[k]
    try: res=H.accent(k, all_forms=False)
    except Exception: res=[]
    groups={}
    for hom in res or []:
        if not hom.get('found',True): continue
        for f in hom.get('forms',[]):
            if not f.get('isInput',True): continue
            key=(f.get('stressed') or k, POS.get(f.get('pos'),f.get('pos','?')))
            g=gram(f.get('grammems',''))
            groups.setdefault(key,[])
            if g not in groups[key]: groups[key].append(g)
    out='; '.join(f"{s}: {p}, {' / '.join(gs)}" if gs and gs!=[''] else f"{s}: {p}" for (s,p),gs in groups.items()) or 'нет в словаре'
    CACHE[k]=out; return out
def ra(marked, src):
    # marked: ruaccent token with '+'; src: original spelling
    plain=marked.replace('+','')
    if 'ё' in plain.lower() and 'ё' not in src.lower():
        return f"{marked.replace('ё','е').replace('Ё','Е')}, {marked}"
    return marked
def conv(mline, sline):
    mt=WORD.findall(mline); st=WORD.findall(sline)
    if len(mt)!=len(st): return None
    it=iter(st); out=[]; pos=0
    for m in WORD.finditer(mline):
        out.append(mline[pos:m.start()]); s=next(it)
        out.append(f"[{ra(m.group(0),s)}, {py(s.replace('+',''))}]"); pos=m.end()
    out.append(mline[pos:]); return ''.join(out)
role=re.compile(r'^([А-ЯЁA-Z0-9_ ]{1,30}:)\s*(.*)$')
src_dir,mk_dir,out_dir=sys.argv[1:4]; os.makedirs(out_dir,exist_ok=True)
stat={'lines':0,'mismatch':0}
for mp in sorted(glob.glob(mk_dir+'/roles_full-ch*.md')):
    n=re.search(r'ch(\d+)',mp).group(1); sp=f'{src_dir}/roles-ch{n}.md'
    S=open(sp,encoding='utf-8').read().split('\n'); M=open(mp,encoding='utf-8').read().rstrip('\n').split('\n')
    res=[]
    for i,ml in enumerate(M):
        sl=S[i] if i<len(S) else ''
        if not ml.strip() or ml.lstrip().startswith(('@','#')): res.append(ml); continue
        mm=role.match(ml); ms=role.match(sl)
        pre,mb=(mm.group(1)+' ',mm.group(2)) if mm else ('',ml)
        sb=ms.group(2) if ms else sl
        c=conv(mb,sb); stat['lines']+=1
        if c is None: stat['mismatch']+=1; c='⚠НЕ ВЫРОВНЕНО: '+mb
        res.append(pre+c)
    open(f'{out_dir}/ch{n}.md','w',encoding='utf-8').write('\n'.join(res)+'\n')
print(stat)

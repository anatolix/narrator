import re,glob,collections,json
B='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace/narrator/books/fine-structure-roles_full'
V='аеёиоуыэюя'
END=['ами','ями','ого','его','ому','ему','ой','ей','ом','ем','ою','ую','а','я','у','ю','е','ы','и','о']
TOK=re.compile(r'(?<![А-ЯЁа-яё+])[+]?[А-ЯЁ][а-яё+]+')
groups=collections.defaultdict(lambda: collections.defaultdict(list))
mid=set()
for f in sorted(glob.glob(B+'/roles_full-ch*.md')):
    ch=int(re.search(r'ch(\d+)',f).group(1))
    for n,l in enumerate(open(f,encoding='utf-8'),1):
        if l.startswith('@'): continue
        body=re.sub(r'^[А-ЯЁA-Z ]{2,}:\s*','',l)
        for m in TOK.finditer(body):
            w=m.group(0)
            if '+' not in w: continue
            plain=w.replace('+','').lower()
            if len(plain)<3: continue
            k=w.find('+'); si=sum(1 for c in w[:k].lower() if c in V)
            stem=plain
            for e in END:
                if plain.endswith(e) and len(plain)-len(e)>=3: stem=plain[:-len(e)]; break
            nstem=sum(1 for c in stem if c in V)
            pos=si if si<nstem else 'окончание'
            before=body[:m.start()].rstrip()
            if before and before[-1] not in '.?!…»"—:(':
                mid.add(stem)
            groups[stem][pos].append((w,ch,n))
rows=[]
for stem,d in groups.items():
    if stem not in mid or len(d)<2: continue
    tot=sum(len(v) for v in d.values())
    var=[]
    for pos,lst in sorted(d.items(),key=lambda x:-len(x[1])):
        forms=collections.Counter(w for w,_,_ in lst)
        locs=sorted({f'ch{c:02d}:{n}' for _,c,n in lst})
        var.append({'pos':pos,'n':len(lst),'forms':dict(forms),'locs':locs})
    rows.append({'stem':stem,'total':tot,'variants':var})
rows.sort(key=lambda r:-r['total'])
json.dump(rows,open('names_check.json','w'),ensure_ascii=False,indent=1)
print('groups with conflicting stress:',len(rows))
for r in rows:
    print(f"\n## {r['stem']} ({r['total']})")
    for v in r['variants']:
        fs=', '.join(f'{k}×{c}' for k,c in v['forms'].items())
        loc=' '.join(v['locs'][:6])+(' …' if len(v['locs'])>6 else '')
        print(f"  [{v['pos']}] {v['n']}: {fs}  | {loc}")

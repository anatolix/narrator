import json,re,collections
D='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace/narrator/books/fine-structure-roles_full'
dec=json.load(open('/tmp/fix_decisions.json'))
by=collections.defaultdict(list)
for ch,ln,o,n in dec: by[ch].append((ln,o,n))
ok=0; miss=[]; chs=set()
for ch,L in sorted(by.items()):
    f=f'{D}/roles_full-ch{ch}.md'; lines=open(f,encoding='utf-8').read().split('\n')
    for ln,o,n in L:
        pat=re.compile(r'(?<![А-Яа-яЁё+\-])'+re.escape(o)+r'(?![А-Яа-яЁё+])')
        new,c=pat.subn(n,lines[ln-1],count=1)
        if c: lines[ln-1]=new; ok+=1; chs.add(ch)
        else: miss.append((ch,ln,o,n))
    open(f,'w',encoding='utf-8').write('\n'.join(lines))
print('applied',ok,'missed',len(miss),miss[:10]); print('CHAPTERS',' '.join(sorted(chs)),len(chs))

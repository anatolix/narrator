import re,glob,collections
W='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace'
S=open(W+'/art/fine-structure/fine-structure.ru.txt',encoding='utf-8').read()
parts=re.split(r'^##\s*Глава\s+(\d+)\.',S,flags=re.M)
src_ch={int(parts[i]):parts[i+1] for i in range(1,len(parts),2)}
B=W+'/narrator/books/fine-structure-roles_full'
for ch in sorted(src_ch):
    s=src_ch[ch]
    try: scr=open(f'{B}/roles_full-ch{ch:02d}.md',encoding='utf-8').read().replace('+','')
    except FileNotFoundError: continue
    for m in re.finditer(r'(\S*?)(\w+)/(\w+)(\S*)',s):
        a,b=m.group(2),m.group(3)
        if re.match(r'https?:|www',m.group(0)): continue
        glued=a+b
        cands={'СКЛЕЙКА':glued,'слэш':a+'/'+b,'пробел':a+' '+b,'дефис':a+'-'+b}
        found=[k for k,v in cands.items() if re.search(r'(?<!\w)'+re.escape(v)+r'(?!\w)',scr,re.I)]
        # words-form of numbers: check what surrounds
        ctx=s[max(0,m.start()-40):m.end()+30].replace('\n',' ')
        print(f'ch{ch:02d} | {m.group(0)} | {",".join(found) or "НЕ НАЙДЕНО"} | {ctx}')

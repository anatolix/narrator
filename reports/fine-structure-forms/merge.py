import json,collections,re
S='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace/scratch/suspect'
OUT='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace/narrator/reports/fine-structure-forms/suspected_verdicts.md'
items={};res=[]
for i in range(1,9):
    for it in json.load(open(f'{S}/batch{i}.json')): items[it['form']]=it
    t=open(f'{S}/out{i}.txt').read(); res+=json.loads(t[t.find('['):t.rfind(']')+1])
json.dump(res,open(f'{S}/verdicts.json','w'),ensure_ascii=False,indent=1)
T=[('wrong','Неверно — менять везде'),('mixed','Смешанно — менять только в указанных местах'),('unsure','Не уверены'),('both_ok','Оба варианта допустимы'),('correct','Верно')]
g=collections.defaultdict(list)
for r in res: g[r['verdict']].append(r)
esc=lambda s:s.replace('|','/')
out=['# Подозрительные формы — вердикты по контексту (26.09)','',f'869 форм, {len(res)} вариантов ударения. Проверка: 8 параллельных прогонов Opus, до 12 примеров контекста на вариант. Вердикт — модели, не мой; wrong/mixed я просмотрю отдельно. В текст ничего не внесено.','','Итог: '+', '.join(f'{n} — {len(g[k])}' for k,n in T),'']
for k,name in T:
    L=sorted(g[k],key=lambda r:-r.get('count',0))
    out+=[f'## {name} — {len(L)}','']
    if k=='correct':
        out+=['| форма | вариант | × | пример | заметка |','|---|---|---:|---|---|']
        for r in L:
            ex=items[r['form']]['text_variants'].get(r['variant'],{}).get('examples',[''])[0]
            out.append(f"| {r['form']} | {r['variant']} | {r.get('count','')} | {esc(ex)} | {esc(r.get('note',''))} |")
        out.append(''); continue
    for r in L:
        fx=f" → **{r['fix']}**" if r.get('fix') else ''
        out+=[f"### {r['form']}: {r['variant']} ×{r.get('count','')}{fx}",'',esc(r.get('note','')),'']
        bad=set(r.get('bad') or [])
        exs=items[r['form']]['text_variants'].get(r['variant'],{}).get('examples',[])
        for e in exs:
            ref=e.split(' ',1)[0]; mark='❌ ' if (ref in bad or k=='wrong') else ('✅ ' if k=='mixed' else '')
            out.append(f'- {mark}{esc(e)}')
        n=r.get('count',0)
        if n>len(exs): out.append(f'- …ещё {n-len(exs)} мест не показаны')
        out.append('')
open(OUT,'w',encoding='utf-8').write('\n'.join(out)+'\n')
import os;print('size',os.path.getsize(OUT))
for k in ('wrong','mixed','unsure'):
    print('=====',k)
    for r in sorted(g[k],key=lambda r:-r.get('count',0)):
        ex=items[r['form']]['text_variants'].get(r['variant'],{}).get('examples',[''])
        b=r.get('bad') or []
        e=next((x for x in ex if x.split(' ',1)[0] in b),ex[0]) if ex else ''
        print(f"{r['variant']}×{r.get('count')} -> {r.get('fix')} bad={len(b)} | {r.get('note','')[:90]} || {e[:130]}")

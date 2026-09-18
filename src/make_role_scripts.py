import re, sys
VERBS="сказал|сказала|спросил|спросила|ответил|ответила|кивнул|кивнула|пробормотал|пробормотала|произнес|произнесла|добавил|добавила|крикнул|крикнула|позвал|позвала|вздохнул|вздохнула|усмехнулся|усмехнулась|улыбнулся|улыбнулась|пожал[а]? плечами|продолжил|продолжила|перебил|перебила|сообщил|сообщила|подумал|подумала|заметил|заметила|спросил|бросил|бросила|фыркнул|фыркнула|хмыкнул|хмыкнула|объяснил|объяснила|повторил|повторила|прошептал|прошептала|заявил|заявила|предложил|предложила|потребовал|потребовала|уточнил|уточнила|подтвердил|подтвердила|возразил|возразила|согласился|согласилась|обернулся|обернулась|вскинул|вскинула"
NAME=r'[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?'
def speaker_after(t):
    m=re.search(rf'(?:{VERBS})\s+({NAME})\b',t)
    if m: return m.group(1)
    m=re.search(rf'\b({NAME})\s+(?:{VERBS})',t)
    return m.group(1) if m else None
def speaker_before(t):
    m=re.search(rf'\b({NAME})\s+(?:{VERBS})[^.—]*\.\s*$',t)
    return m.group(1) if m else None
def build(n):
    ps=[l[7:] for l in open(f"script-ch{n:02d}.md") if l.startswith("ДИКТОР: ")]
    out=["@ДИКТОР: filipp neutral 1.25","@ГОЛОС: zahar neutral 1.1","@ЖЕНЩИНА: jane neutral 1.0","@gap: 0.4",""]
    # collect cast: known names -> assign later; header placeholder
    body=[]; unattr=0
    for p in ps:
        p=p.strip()
        if not p: continue
        if p=="***" or set(p)<=set("*—- "):
            body.append("@pause: 2.5"); continue
        p=p.replace("***","").replace("* * *","")
        if p.startswith("— "):
            # dialogue, maybe "— реплика, — сказала Зеф. — продолжение"
            chunks=re.split(r'\s—\s',p[1:])
            sp=None
            for c in chunks[1:]:
                s=speaker_after(c)
                if s: sp=s; break
            quote=chunks[0]
            body.append(f"@{sp.upper() if sp else None}" if False else (f"{sp.upper() if sp else 'ГОЛОС'}: {quote}"))
            if not sp: unattr+=1
            rest=chunks[1:]
            for c in rest:
                c=c.strip()
                if not c: continue
                body.append(f"ДИКТОР: {c}")
        else:
            # narration; may contain trailing "— реплика" after name intro
            m=re.match(rf'^(.*?)({NAME})\s+(?:{VERBS})[^.—]*\.\s*—\s*(.+)$',p)
            if m:
                pre=(m.group(1)+"").strip()
                if pre: body.append(f"ДИКТОР: {pre}")
                body.append(f"ДИКТОР: {m.group(2)} сказал." if False else f"{m.group(2).upper()}: {m.group(3)}")
            else:
                body.append(f"ДИКТОР: {p}")
    # build cast from used roles
    roles=sorted({b.split(":")[0] for b in body if re.match(r'^[А-ЯЁA-Z0-9 _-]{2,30}: ',b)})
    male=["zahar","ermil","madirus"]; female=["jane","alena","omazh"]
    cast={"ДИКТОР":"filipp neutral 1.25","ГОЛОС":"zahar neutral 1.1","ЖЕНЩИНА":"jane neutral 1.0"}
    mi=fi=0
    for r in roles:
        if r in cast: continue
        fem=bool(re.search(r'(А|Я|ИЯ|Ь)$',r))  # crude gender guess
        if fem: cast[r]=f"{female[fi%len(female)]} neutral 1.05"; fi+=1
        else: cast[r]=f"{male[mi%len(male)]} neutral 1.05"; mi+=1
    hdr="\n".join(f"@{r}: {cast[r]}" for r in sorted(cast))
    open(f"roles-ch{n:02d}.md","w").write(hdr+"\n@gap: 0.4\n\n"+"\n".join(body)+"\n")
    return unattr
tot=0
for n in range(1,43):
    u=build(n); tot+=u
    if u: print(f"ch{n:02d}: {u} unattributed")
print("total unattributed:",tot)

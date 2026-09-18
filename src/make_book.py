import re, subprocess, sys, os
ps = open("fine-structure.ru.txt").read().split("\n\n")
idx = [k for k,p in enumerate(ps) if p.startswith("## Глава")]
print(len(idx), "chapters")
import os as _os
_DONE=_os.environ.get("MAX_CH","999")
_cnt=0
for n,k in enumerate(idx, 1):
    e = idx[n] if n < len(idx) else len(ps)
    ch = ps[k:e]
    title = ch[0][3:].strip()
    out = [f"# Тонкая структура — {title}","", "@ДИКТОР: filipp neutral 1.25","@gap: 0.5",""]
    if n == 1: out.append("ДИКТОР: Сэм Хьюз. Тонкая структура.")
    out.append("ДИКТОР: " + title + ".")
    for p in ch[1:]:
        p = re.sub(r"\[\d+\]", "", p).strip()
        if p: out.append("ДИКТОР: " + p)
    fn = f"script-ch{n:02d}.md"
    open(fn, "w").write("\n\n".join(out) + "\n")
    mp3 = f"/workspace/art/fine-structure-ch{n:02d}.mp3"
    if os.path.exists(mp3): print(f"ch{n:02d} exists, skip"); continue
    _cnt+=1
    if _cnt>int(_DONE): print("BATCH LIMIT"); sys.exit(0)
    r = subprocess.run(["python3","/workspace/skills/translate-voice-story/scripts/voice_script.py", fn, mp3],
                       capture_output=True, text=True)
    print(f"ch{n:02d}", r.stdout.strip().splitlines()[-1] if r.stdout else "", r.stderr[-200:] if r.returncode else "", flush=True)
    if r.returncode: sys.exit(1)
print("ALL DONE")

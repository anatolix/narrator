#!/usr/bin/env python3
"""v6: replace 19 fixed line-segments in v4 chapter mp3s, re-stitch, rebuild SRTs."""
import subprocess, os, re, sys, urllib.request, urllib.parse, time, shutil

WS = "/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace"
BOOK = f"{WS}/narrator/books/fine-structure-roles_full"
V4 = f"{WS}/art/v5/out"
V4BASE = f"{WS}/art/v5/v5out"
V5 = f"{WS}/art/v6/v6out"
os.makedirs(V5, exist_ok=True)
KEY = open(f"{WS}/.secrets/yandex_api_key").read().strip()

# chapter -> [script line numbers (1-based) that were fixed after v4]
TARGETS = {
 'ch01':[17],'ch15':[95],'ch18':[21,159],'ch21':[33],'ch25':[125,195],
 'ch26':[17],'ch34':[107],'ch36':[129],'ch37':[13],'ch38':[9],'ch39':[9],
 'ch40':[13],'ch41':[23,199],'ch42':[329,689,803]}

def parse(path):
    cast, gap, segs = {}, 0.4, []
    for ln, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        m = re.match(r"^@gap:\s*([\d.]+)", line)
        if m: gap = float(m.group(1)); continue
        m = re.match(r"^@pause:\s*([\d.]+)", line)
        if m: segs.append((ln, "@pause", m.group(1))); continue
        m = re.match(r"^@([^:]+):\s*(\S+)\s+(\S+)\s+([\d.]+)", line)
        if m: cast[m.group(1).strip()] = (m.group(2), None if m.group(3) == "-" else m.group(3), m.group(4)); continue
        m = re.match(r"^([А-ЯЁA-Z][А-ЯЁA-Z0-9 _-]{1,30}):\s*(.+)$", line)
        if m and m.group(1).strip() in cast: segs.append((ln, m.group(1).strip(), m.group(2).strip()))
    return cast, gap, segs

def synth(text, voice, emotion, speed, path):
    for attempt in range(4):
        fields = {"text": text, "lang": "ru-RU", "voice": voice, "speed": speed, "format": "mp3"}
        if emotion: fields["emotion"] = emotion
        req = urllib.request.Request("https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize",
              data=urllib.parse.urlencode(fields).encode(), headers={"Authorization": f"Api-Key {KEY}"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r: body = r.read()
            if len(body) > 500: open(path, "wb").write(body); return True
        except Exception as e:
            print(f"  synth retry {attempt}: {e}"); time.sleep(3)
    return False

def probe(p):
    try:
        d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],
                           capture_output=True,text=True).stdout.strip()
        v = float(d); return v if v > 0 else None
    except ValueError: return None

def run(c):
    x = subprocess.run(c, capture_output=True, text=True)
    if x.returncode: print(x.stderr[-400:]); sys.exit(1)

def srt_ts(sec):
    ms = round(sec*1000)
    return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"

all_ch = [f"ch{n:02d}" for n in range(1,43)]
for ch in all_ch:
    v4mp3 = f"{V4BASE}/fine-structure-v5-{ch}.mp3"
    v5mp3 = f"{V5}/fine-structure-v6-{ch}.mp3"
    v4srt = f"{V4BASE}/fine-structure-v5-{ch}.srt"
    v5srt = f"{V5}/fine-structure-v6-{ch}.srt"
    if ch not in TARGETS:
        shutil.copy(v4mp3, v5mp3)
        open(v5srt,"w",encoding="utf-8").write(open(v4srt,encoding="utf-8").read().replace("+",""))
        continue
    cast, gap, segs = parse(f"{BOOK}/roles_full-{ch}.md")
    work = f"{V4}/.work-fine-structure-v4-{ch}"
    n_existing = len([f for f in os.listdir(work) if re.match(r"seg-\d+\.mp3", f)])
    assert n_existing == len(segs), f"{ch}: segs {len(segs)} != files {n_existing}"
    # 1. synthesize replacements
    for ln in TARGETS[ch]:
        idx = next(i for i,(l,r,t) in enumerate(segs) if l == ln)
        role, text = segs[idx][1], segs[idx][2]
        v, e, s = cast[role]
        p = f"{work}/seg-{idx:04d}.mp3"
        ok = synth(text, v, e, s, p)
        print(f"{ch} seg-{idx:04d} (line {ln}, {role}/{v}) {'OK' if ok else 'FAIL'} dur={probe(p)}")
        if not ok: sys.exit(1)
    # 2. re-stitch
    run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t",str(gap),"-q:a","2",f"{work}/sil.mp3"])
    with open(f"{work}/list.txt","w") as f:
        for i in range(len(segs)):
            f.write(f"file '{work}/seg-{i:04d}.mp3'\nfile '{work}/sil.mp3'\n")
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",f"{work}/list.txt","-c:a","libmp3lame","-q:a","2",v5mp3])
    # 3. rebuild SRT
    cursor, n = 0.0, 0
    with open(v5srt,"w",encoding="utf-8") as f:
        for i,(ln,r,t) in enumerate(segs):
            dur = float(t) if r=="@pause" else probe(f"{work}/seg-{i:04d}.mp3")
            if r != "@pause":
                n += 1
                clean = t.replace("+","")
                f.write(f"{n}\n{srt_ts(cursor)} --> {srt_ts(cursor+dur)}\n{r}: {clean}\n\n")
            cursor += dur + gap
    d = probe(v5mp3)
    print(f"{ch} RESTITCHED {d/60:.1f} min, cues={n}")
print("V6_BUILD_DONE")

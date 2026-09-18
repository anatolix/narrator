import subprocess, os, sys, re, time, urllib.request, urllib.parse

D = "/workspace/art/halloween"; os.chdir(D)
KEY = subprocess.run(["assistant","credentials","reveal","--service","yandex","--field","api_key"],
                     capture_output=True, text=True).stdout.strip()
if not KEY.startswith("AQVN"): print("no key"); sys.exit(1)

# narrator (heroine, 1st person) = alena; old woman = omazh (older female), slow; men = zahar
NARR = ("jane", "good", "0.9")
CRONE = ("omazh", "evil", "0.85")
MAN = ("zahar", "neutral", "0.9")

text = open("my-REMOVED.ru.md").read()
paras = [p.strip() for p in text.split("\n\n") if p.strip()]
paras = paras[2:]  # drop title + byline; add spoken title
segs = [(NARR, "Мой хеллоуинский костюм. Рассказ Джо Доу. Перевод с английского.")]

# lines the crone speaks (start with dash and match crone markers)
CRONE_HINTS = ["без костюма", "Туфли не забывай", "Надевай. Это твой", "этот костюм — ТВОЙ", "Не продаю", "Дай, надену",
               "Нравится «костюм»", "Это африканское ожерелье", "Да, это твой костюм", "Я никто", "Большой босс",
               "Верь, не верь", "Видишь? — рассмеялась"]
MAN_HINTS = ["Моджа", "Мбили", "Тату!"]

def split_dialog(p):
    """split '— quote, — narration. — quote' into (speaker, text) parts"""
    parts = []
    if not p.startswith("—"):
        return [("N", p)]
    # crude: split on ' — ' boundaries alternating quote/narration
    chunks = re.split(r'\s—\s', p[1:].strip())
    who = "Q"
    for i, c in enumerate(chunks):
        c = c.strip()
        if not c: continue
        parts.append((who, c))
        who = "N" if who == "Q" else "Q"
    return parts

for p in paras:
    if p in ("— Моджа…", "— Мбили…", "— Тату!"):
        segs.append((MAN, p.strip("— "))); continue
    crone = any(h in p for h in CRONE_HINTS)
    for who, t in split_dialog(p):
        t = t.replace("«", "").replace("»", "")
        if who == "Q":
            segs.append((CRONE if crone else NARR, t))
        else:
            segs.append((NARR, t))

# merge consecutive narrator bits into chunks <= 4500 chars (API limit 5000)
merged = []
for v, t in segs:
    if merged and merged[-1][0] == v and len(merged[-1][1]) + len(t) < 4000:
        merged[-1] = (v, merged[-1][1] + " " + t)
    else:
        merged.append((v, t))
print(len(merged), "segments")

def synth(text, voice, emotion, speed, out):
    data = urllib.parse.urlencode({"text": text, "lang": "ru-RU", "voice": voice, "emotion": emotion,
                                   "speed": speed, "format": "mp3"}).encode()
    req = urllib.request.Request("https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize",
                                 data=data, headers={"Authorization": f"Api-Key {KEY}"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read()
            if len(body) > 500: open(out, "wb").write(body); return
        except urllib.error.HTTPError as e:
            msg = e.read()[:300]
            if b"Unsupported voice" in msg or b"emotion" in msg.lower():
                data = urllib.parse.urlencode({"text": text, "lang": "ru-RU", "voice": voice if b"emotion" in msg.lower() else "alena",
                                               "speed": speed, "format": "mp3"}).encode()
                req = urllib.request.Request(req.full_url, data=data, headers={"Authorization": f"Api-Key {KEY}"}); continue
            if attempt == 2: print(f"HTTP {e.code} {voice}: {msg} :: {text[:60]}"); sys.exit(1)
        time.sleep(1)

parts = []
for i, ((v, e, s), t) in enumerate(merged):
    out = f"seg-{i:03d}.mp3"
    if not os.path.exists(out): synth(t, v, e, s, out)
    parts.append(out)
    if i % 20 == 0: print(f"...{i}/{len(merged)}", flush=True)

def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode: print(r.stderr[-300:]); sys.exit(1)
run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t","0.4","-q:a","2","sil.mp3"])
with open("list.txt","w") as f:
    for p in parts: f.write(f"file '{p}'\nfile 'sil.mp3'\n")
run(["ffmpeg","-y","-f","concat","-safe","0","-i","list.txt","-c:a","libmp3lame","-q:a","2","/workspace/art/REMOVED.mp3"])
subprocess.run("rm -f seg-*.mp3 sil.mp3 list.txt", shell=True)
d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0","/workspace/art/REMOVED.mp3"],capture_output=True,text=True).stdout.strip()
print("DONE", d, "sec")

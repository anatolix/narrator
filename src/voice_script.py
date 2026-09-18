#!/usr/bin/env python3
"""Voice a role-tagged script.md with Yandex SpeechKit v1 and stitch into one MP3.
Usage: python3 voice_script.py <script.md> <out.mp3> [--dry]   (needs network_mode: proxied, credential yandex/api_key)

script.md format:
  @РОЛЬ: voice emotion speed      <- cast lines (anywhere; usually at top). emotion may be '-' for none.
  @gap: 0.4                        <- optional pause between segments, seconds
  РОЛЬ: text of the segment        <- one segment per line; blank lines / other lines ignored
Verified v1 voices: jane, alena, omazh (F); filipp, ermil, zahar, madirus (M). 'kirill' is NOT supported.
"""
import subprocess, os, sys, re, time, urllib.request, urllib.parse, tempfile, shutil
src, out = sys.argv[1], sys.argv[2]; dry = "--dry" in sys.argv
cast, gap, segs = {}, 0.4, []
for line in open(src, encoding="utf-8"):
    line = line.strip()
    m = re.match(r"^@gap:\s*([\d.]+)", line)
    if m: gap = float(m.group(1)); continue
    m = re.match(r"^@pause:\s*([\d.]+)", line)
    if m: segs.append(("@pause", m.group(1))); continue
    m = re.match(r"^@([^:]+):\s*(\S+)\s+(\S+)\s+([\d.]+)", line)
    if m: cast[m.group(1).strip()] = (m.group(2), None if m.group(3) == "-" else m.group(3), m.group(4)); continue
    m = re.match(r"^([А-ЯЁA-Z][А-ЯЁA-Z0-9 _-]{1,30}):\s*(.+)$", line)
    if m and m.group(1).strip() in cast: segs.append((m.group(1).strip(), m.group(2).strip()))
    elif m: print(f"WARN unknown role, skipped: {line[:60]}")
# merge consecutive same-role lines under ~4000 chars (API limit 5000)
merged = []
for r, t in segs:
    if r == "@pause": merged.append((r, t)); continue
    if merged and merged[-1][0] == r and len(merged[-1][1]) + len(t) < 4000: merged[-1] = (r, merged[-1][1] + " " + t)
    else: merged.append((r, t))
from collections import Counter
print("roles:", dict(Counter(r for r, _ in segs)), "| segments:", len(segs), "-> merged:", len(merged), "| cast:", cast)
if dry: sys.exit(0)
KEY = subprocess.run(["assistant", "credentials", "reveal", "--service", "yandex", "--field", "api_key"], capture_output=True, text=True).stdout.strip()
if not KEY.startswith("AQVN"): print("no yandex/api_key"); sys.exit(1)
work = os.path.dirname(os.path.abspath(out)) + "/.work-" + os.path.splitext(os.path.basename(out))[0]
os.makedirs(work, exist_ok=True)
def synth(text, voice, emotion, speed, path):
    for attempt in range(4):
        fields = {"text": text, "lang": "ru-RU", "voice": voice, "speed": speed, "format": "mp3"}
        if emotion: fields["emotion"] = emotion
        req = urllib.request.Request("https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize", data=urllib.parse.urlencode(fields).encode(), headers={"Authorization": f"Api-Key {KEY}"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r: body = r.read()
            if len(body) > 500: open(path, "wb").write(body); return
        except urllib.error.URLError as e:
            if not isinstance(e, urllib.error.HTTPError):
                print(f"net error, retry: {e.reason}"); time.sleep(5); continue
            msg = e.read()[:300]
            msg = e.read()[:300]
            if b"Unsupported voice" in msg: print(f"voice {voice} unsupported -> jane"); voice, emotion = "jane", None; continue
            if b"emotion" in msg.lower() or b"unknown role" in msg.lower(): print(f"emotion {emotion} unsupported for {voice} -> none"); emotion = None; continue
            if attempt == 3: print(f"HTTP {e.code} {voice}: {msg} :: {text[:60]}"); sys.exit(1)
        time.sleep(1)
parts = []
for i, (r, t) in enumerate(merged):
    p = f"{work}/seg-{i:03d}.mp3"
    if r == "@pause":
        if not os.path.exists(p):
            run0 = subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t",t,"-q:a","2",p],capture_output=True)
        parts.append(p); continue
    v, e, s = cast[r]
    if not os.path.exists(p): synth(t, v, e, s, p)
    parts.append(p)
    if i % 20 == 0: print(f"...{i}/{len(merged)}", flush=True)
def run(c):
    x = subprocess.run(c, capture_output=True, text=True)
    if x.returncode: print(x.stderr[-400:]); sys.exit(1)
run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", str(gap), "-q:a", "2", f"{work}/sil.mp3"])
with open(f"{work}/list.txt", "w") as f:
    for p in parts: f.write(f"file '{p}'\nfile '{work}/sil.mp3'\n")
run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt", "-c:a", "libmp3lame", "-q:a", "2", out])
shutil.rmtree(work)
d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
print(f"DONE {out} {float(d)/60:.1f} min")

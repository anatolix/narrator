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
# NO merging: one API call per script line, so each seg-N.mp3 maps 1:1 to a subtitle cue.
# (SpeechKit bills per character, not per call — line-per-call costs the same money.)
merged = segs
from collections import Counter
print("roles:", dict(Counter(r for r, _ in segs)), "| segments:", len(segs), "| cast:", cast)
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
def probe(p):
    """Duration of an audio file, or None if missing/undecodable (corrupt cache entry)."""
    if not os.path.exists(p): return None
    try:
        d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip()
        v = float(d)
        return v if v > 0 else None
    except ValueError: return None
parts = []
for i, (r, t) in enumerate(merged):
    p = f"{work}/seg-{i:04d}.mp3"
    if r == "@pause":
        if probe(p) is None:
            run0 = subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t",t,"-q:a","2",p],capture_output=True)
        parts.append(p); continue
    v, e, s = cast[r]
    if probe(p) is None:
        if os.path.exists(p): os.remove(p)  # corrupt cache entry — resynthesize, never trust it for timing
        synth(t, v, e, s, p)
        if probe(p) is None: print(f"seg {i} still invalid after synth"); sys.exit(1)  # fail BEFORE writing any SRT
    parts.append(p)
    if i % 20 == 0: print(f"...{i}/{len(merged)}", flush=True)
def run(c):
    x = subprocess.run(c, capture_output=True, text=True)
    if x.returncode: print(x.stderr[-400:]); sys.exit(1)
run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", str(gap), "-q:a", "2", f"{work}/sil.mp3"])
with open(f"{work}/list.txt", "w") as f:
    for p in parts: f.write(f"file '{p}'\nfile '{work}/sil.mp3'\n")
run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt", "-c:a", "libmp3lame", "-q:a", "2", out])

# SRT subtitles: one cue per script line, timed from per-segment durations + inter-segment gap.
# Written ONLY after every segment passed probe() above — a failed synthesis exits first, so an SRT can never be emitted against missing/broken audio.
def seg_dur(i, r, t, p):
    if r == "@pause": return float(t)
    return probe(p)
def srt_ts(sec):
    ms = round(sec * 1000)
    return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
srt_path = os.path.splitext(out)[0] + ".srt"
cursor, n = 0.0, 0
with open(srt_path, "w", encoding="utf-8") as f:
    for i, (r, t) in enumerate(merged):
        dur = seg_dur(i, r, t, parts[i])
        if r != "@pause":
            n += 1
            f.write(f"{n}\n{srt_ts(cursor)} --> {srt_ts(cursor + dur)}\n{r}: {t}\n\n")
        cursor += dur + gap
print(f"SRT {srt_path} cues={n}")
shutil.rmtree(work)
d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
print(f"DONE {out} {float(d)/60:.1f} min")

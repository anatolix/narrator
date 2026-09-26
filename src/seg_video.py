#!/usr/bin/env python3
"""Segmented video pipeline v8: per-scene mp4 segments + concat.
- Re-anchors scene timings from v6 SRT cue indices onto v8 SRT cues.
- Renders each scene as seg/chNN-sNN.mp4 (linked image + v8 audio slice + shifted subs).
- Caches segments with manifest.json (scene -> img,start,end) for future partial re-renders.
- Concats segments per chapter -> 'NN - Title.mp4', uploads to S3.
Resumable: existing segment with matching manifest entry is skipped.
"""
import os, re, json, subprocess, sys, time, hashlib, boto3

VID = "/home/ubuntu/vid"
IMG = f"{VID}/img-linked"
SEG = f"{VID}/seg"
OUT = f"{VID}/v8final"
A8 = "/home/ubuntu/v8work/v8out"
A6 = f"{VID}/v6out"
os.makedirs(SEG, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

k = open(f"{VID}/yandex_s3_static").read().split()
s3 = boto3.client("s3", endpoint_url="https://storage.yandexcloud.net",
                  aws_access_key_id=k[0], aws_secret_access_key=k[1])
BUCKET = "juno-ruaccent-2027131566"

timing = open(f"{VID}/scenes-timing.md", encoding="utf-8").read()
titles = dict(l.strip().split("|", 1) for l in open(f"{VID}/titles.txt") if "|" in l)
MANIFEST_PATH = f"{SEG}/manifest.json"
manifest = json.load(open(MANIFEST_PATH)) if os.path.exists(MANIFEST_PATH) else {}

def probe(p):
    d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],
                       capture_output=True, text=True).stdout.strip()
    return float(d)

def srt_ts(sec):
    ms = max(0, round(sec*1000))
    return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"

def parse_srt(path):
    raw = open(path, encoding="utf-8").read()
    cues = []
    for _, a, b, text in re.findall(r"(\d+)\n(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)\n(.*?)(?=\n\n|\Z)", raw, re.S):
        def parse(t):
            h, m, rest = t.split(":"); s, ms = rest.split(",")
            return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
        cues.append((parse(a), parse(b), text.replace("\n", " ")))
    return cues

def chapter_scenes_v6(ch):
    n = int(ch[2:])
    m = re.search(rf"## Глава {n}\n(.*?)(?=\n## Глава |\Z)", timing, re.S)
    scenes = re.findall(
        rf"### Сцена \d+\s+`(\d\d):(\d\d):(\d\d),(\d\d\d) → (\d\d):(\d\d):(\d\d),(\d\d\d)`.*?"
        rf"ИЗОБРАЖЕНИЕ: .*?/({ch}-s\d+)\.\w+", m.group(1), re.S)
    def ts(h, m_, s, ms): return int(h)*3600 + int(m_)*60 + int(s) + int(ms)/1000
    return [(ts(*sc[0:4]), sc[8]) for sc in scenes]

def split_srt_sentences(cues):
    """cue -> sentence-level cues with proportional timing (same as gen_video)."""
    out = []
    for start, end, text in cues:
        text = re.sub(r"^[А-ЯЁA-Z][А-ЯЁA-Z0-9 _-]{1,30}: ", "", text).strip()
        sents = [x.strip() for x in re.split(r"(?<=[.!?…])\s+", text) if x.strip()]
        if not sents: continue
        total = sum(len(x) for x in sents) or 1
        cur = start
        for x in sents:
            d = (end - start) * len(x) / total
            out.append((cur, min(cur + d, end), x))
            cur += d
    return out

def slice_srt(sent_cues, start, end, dst):
    n = 0
    with open(dst, "w", encoding="utf-8") as f:
        for a, b, text in sent_cues:
            if b <= start or a >= end: continue
            a2, b2 = max(a, start) - start, min(b, end) - start
            n += 1
            f.write(f"{n}\n{srt_ts(a2)} --> {srt_ts(b2)}\n{text}\n\n")
    return n

import os as _os
FPS = int(_os.environ.get("SEG_FPS", "3"))
GOP = int(_os.environ.get("SEG_GOP", "72"))
CRF = _os.environ.get("SEG_CRF", "24")
FILT_STYLE = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1"

results = []
for i in range(1, 43):
    ch = f"ch{i:02d}"
    t0 = time.time()
    try:
        audio = f"{A8}/fine-structure-v8-{ch}.mp3"
        srt8 = f"{A8}/fine-structure-v8-{ch}.srt"
        srt6 = f"{A6}/fine-structure-v6-{ch}.srt"
        scenes6 = chapter_scenes_v6(ch)
        assert scenes6, "no scenes"
        cues6 = parse_srt(srt6); cues8 = parse_srt(srt8)
        assert len(cues6) == len(cues8), f"{ch}: cue count {len(cues6)} vs {len(cues8)}"
        starts6 = [c[0] for c in cues6]
        adur = probe(audio)
        # re-anchor: scene v6 start -> nearest v6 cue index -> v8 cue start
        scenes8 = []
        for st6, name in scenes6:
            idx = min(range(len(starts6)), key=lambda j: abs(starts6[j] - st6))
            assert abs(starts6[idx] - st6) < 1.5, f"{ch} {name}: anchor off by {abs(starts6[idx]-st6):.2f}s"
            scenes8.append((cues8[idx][0], name))
        sent8 = split_srt_sentences(cues8)
        # render segments
        segfiles = []
        for j, (st, name) in enumerate(scenes8):
            end = scenes8[j+1][0] if j+1 < len(scenes8) else adur
            dur = max(0.2, end - st)
            segf = f"{SEG}/{name}.mp4"
            key = f"{name}"
            entry = {"img": name, "start": round(st, 3), "end": round(end, 3), "v": 8}
            segfiles.append(segf)
            if os.path.exists(segf) and manifest.get(key) == entry and probe(segf) > 0.1:
                continue
            cmd = ["ffmpeg", "-y",
                   "-loop", "1", "-t", f"{dur:.3f}", "-i", f"{IMG}/{name}.jpg",
                   "-ss", f"{st:.3f}", "-t", f"{dur:.3f}", "-i", audio,
                   "-filter_complex", FILT_STYLE,
                   "-map", "0:v", "-map", "1:a",
                   "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", CRF, "-g", str(GOP),
                   "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                   "-movflags", "+faststart", segf]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode:
                print(f"{ch} {name} FFMPEG_FAIL {r.stderr[-300:]}", flush=True)
                raise RuntimeError("ffmpeg fail")
            manifest[key] = entry
            json.dump(manifest, open(MANIFEST_PATH, "w"))
            print(f"{ch} {name} seg OK {dur:.1f}s", flush=True)
        # chapter subtitle track (sentence-split, switchable)
        chsrt = f"{SEG}/track-{ch}.srt"
        with open(chsrt, "w", encoding="utf-8") as f:
            for n, (a, b, text) in enumerate(sent8, 1):
                f.write(f"{n}\n{srt_ts(a)} --> {srt_ts(b)}\n{text}\n\n")
        # concat
        final = f"{OUT}/{ch[2:]} - {titles[ch[2:]]}.mp4"
        lst = f"{SEG}/list-{ch}.txt"
        with open(lst, "w") as f:
            for sf in segfiles: f.write(f"file '{sf}'\n")
        r = subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-i",chsrt,
                           "-c:v","copy","-c:a","copy","-c:s","mov_text","-metadata:s:s:0","language=rus",
                           "-movflags","+faststart",final],
                           capture_output=True, text=True)
        if r.returncode:
            print(f"{ch} CONCAT_FAIL {r.stderr[-300:]}", flush=True)
            raise RuntimeError("concat fail")
        vdur = probe(final)
        s3.upload_file(final, BUCKET, f"video8/fine-structure-v8-{ch}.mp4")
        print(f"{ch} DONE scenes={len(scenes8)} dur={vdur:.1f}s render={(time.time()-t0)/60:.1f}min uploaded", flush=True)
        results.append((ch, "OK"))
        os.remove(final)
    except Exception as e:
        print(f"{ch} ERROR {e}", flush=True)
        results.append((ch, f"ERROR {e}"))

ok = sum(1 for _, s in results if s == "OK")
print(f"SEG_VIDEO_DONE ok={ok}/42", flush=True)

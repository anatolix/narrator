#!/bin/bash
# Concat the re-voiced fine-structure-roles series into one MP3.
# Post-completion step for the re-voice batch. Run from /workspace/art/fine-structure.
set -e
cd /workspace/art

echo "=== checking for complete series (42 chapters) ==="
total=$(ls fine-structure-roles-ch*.mp3 2>/dev/null | wc -l)
echo "files present: $total"
if [ "$total" -lt 42 ]; then
  echo "WARN: only $total/42 present — batch not finished. Exiting."
  exit 1
fi

# Build a sorted, zero-padded file list.
ls fine-structure-roles-ch*.mp3 | sort -V > /tmp/concat_list.txt
echo "sorted order:"
cat /tmp/concat_list.txt

echo ""
echo "=== concatenating with ffmpeg concat demuxer ==="
ffmpeg -y -f concat -safe 0 -i /tmp/concat_list.txt -c copy \
  /workspace/art/fine-structure-roles-full.mp3 2>&1 | tail -5

echo ""
echo "=== done ==="
ls -lh /workspace/art/fine-structure-roles-full.mp3

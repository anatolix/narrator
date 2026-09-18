#!/bin/bash
cd /workspace/art/fine-structure
for f in roles-ch*.md; do
  n=${f#roles-ch}; n=${n%.md}
  out="/workspace/art/fine-structure-roles-ch${n}.mp3"
  if [ -s "$out" ]; then echo "ch$n skip"; continue; fi
  python3 /workspace/skills/translate-voice-story/scripts/voice_script.py "$f" "$out" >> make_roles.log 2>&1
  rc=$?
  echo "ch$n rc=$rc"
  [ $rc -ne 0 ] && exit 1
done
echo "ALL DONE"

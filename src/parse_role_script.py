import re
from collections import Counter
# Explicit role-tagged script parser — reads a script.md with one 'РОЛЬ: text' line per segment.
# Roles are the literal Russian tokens used in the script (e.g. РАССКАЗЧИЦА / СТАРУХА / КУЗНЕЦ).
# Usage: replace the role set below with the script's roles; drop the role-tag lines into
# make_audio/radio's input instead of a dash-heuristic split.
ROLES = ["РАССКАЗЧИЦА", "СТАРУХА", "КУЗНЕЦ"]
alt = "|".join(ROLES)
segs = []
for line in open("script.md"):
    line = line.strip()
    m = re.match(rf"^({alt}):\s*(.+)$", line)
    if m:
        segs.append((m.group(1), m.group(2)))
c = Counter(s for s, _ in segs)
print(c)

---
name: "Russian Stress Context Resolve"
description: "Disambiguate Russian word stress for audiobook TTS using 3 Sonnet runs + pylem dictionary vote"
metadata:
  vellum:
    emoji: 🎤
    activation-hints:
      - needs to disambiguate stress for Russian TTS/audiobook
      - wants to resolve stress candidates by context for Russian narration
      - when ruaccent and pylem disagree on Russian word stress
      - needs to find correct Russian word stress by context across many chapters
    category: content
---

Procedure to disambiguate Russian word stress using 3 parallel Sonnet runs + pylem dictionary + 3-way vote.

**Input:** chapter roles script (roles-chNN.md from narrator repo), ruaccent-marked script (roles_full-chNN.md).
**Output:** resolved/chNN.md (each word has one stress, brackets only for human-decision items), resolved/chNN-review.md (divergences flagged for human review).

## Procedure

### 1. Setup
- Working directory: `art/new-books/stress/`.
- Requires: `pylem` (conda env `main`), `assistant inference send` CLI via shim (`claude-code-sonnet` profile, fallback `balanced`).
- Source: `narrator/books/<book>-roles/roles-chNN.md`. For ruaccent marking: provision a Yandex Cloud VM with ruaccent turbo3.1 (or use pre-marked files).
- `resolve.py`, `vote.py`, `driver_all.py` live in the working directory.

### 2. Run comparison (already done)
`python3 compare.py <src_dir> <ra_marked_dir> <out_dir>` — per-word comparison `[ruaccent, pylem: POS, grammemes; ...]`.

### 3. Single resolve run
`python3 resolve.py <chapter_number>` — processes one chapter. Creates/reads cache at `resolve*-chNN.cache.json`. Uses env var `RUN` to distinguish cache files (1st run no var, 2nd `RUN=2`, 3rd `RUN=3`). Env var `THREADS` controls parallelism (default 4 to avoid shim timeouts). Env var `DRY=1` to count tokens without inference. Env var `FINAL=1` to commit partial chunk results even if incomplete.

**Gotchas:**
- The shim (`claude-code-sonnet` profile) times out on some chunks after ~13+ minutes. Script retries up to 4 times per chunk. Fallback `balanced` profile is slower.
- When restarting after a broken run (different prompt version, credits exhausted mid-way), clear the chapter's cache JSON first (`pop("chunk_key")` or delete file).
- Always activate conda env `main` before running — `pylem` import fails outside it.

### 4. Vote merge
`python3 vote.py <chapter_number>` — merges three cache files into resolved output. 3-way voting:
- Unanimous → single stress.
- 2:1 → majority stress (listed in review as "Решено большинством 2:1").
- All diverged or model left multiple → bracketed in text, listed in review for human decision.
Also fixes: restores stress dropped on single-syllable parts in compounds (кое-, -нибудь, -то, -ка), assigns ё→+ё where dictionary bug missed it.

### 5. Batch driver
`python3 driver_all.py` — iterates chapters 02–24 sequentially (1 chapter at a time), runs all 3 resolve runs then vote and git commit. Uses `ThreadPoolExecutor(1)` for chapters, 4 threads within each.

### 6. Repeat for each book
For Вечное пламя and Стрелы времени: create directory, run same pipeline. VM with ruaccent can be shared across books (mark scripts per chapter).

### Sonnet prompt
Key rules embedded in resolve.py SYS string:
- Keep ALL context-permitted variants — never guess when multiple are possible.
- If two interpretations exist (gen.sg vs nom.pl; все vs всё; adverbial vs short adjective), keep both with why.
- ё: if the word exists only with ё in Russian (еще→ещё, ее→её, черный→чёрный), answer is ё without dispute. Only dispute when е/ё give DIFFERENT words (все/всё, небо/нёбо).
- pylem sometimes gives wrong stress on ё-words (dictionary bug) — ignore, ё always stressed.

### Special cases
- Unstressed proper names not in dictionary (Массимой, Ялда) — collect per-book list, add stress manually.
- Formulas without words (ch22) — keep verbatim, no stress marking.
- ruaccent drops punctuation (quotes «», +/=/× symbols) — char-level difflib realignment is applied via `realign()` in compare.py.
- Known majority-vote errors found in ch01: L683 больш+ая→б+ольшая (meaning majority), L379 самог+о→с+амого (у самого края), L315 утр+а→+утра (without preposition).

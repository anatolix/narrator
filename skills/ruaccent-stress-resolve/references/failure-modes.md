## Failure modes

### Shim timeout
`chunk N claude-code-sonnet fail ValueError('substring not found') OpenAI-compatible request failed: The operation timed out.`
Common on chunks >70 words after ~13+ minutes. Fallback profile `balanced` also times out on same chunks sometimes. Script retries up to 4 times. On retry exhaustion, the chunk is skipped and `noanswer` increases.

### Different prompt per run
Chapter 01 had `run 1` with 'pick one' prompt, runs 2/3 with 'keep all plausible' prompt. This causes systematic voting bias — run 1 always picks one, runs 2/3 may leave multiples. For subsequent chapters, all 3 runs use the same prompt. When restarting a chapter after a prompt change, **clear the cache JSON** (`rm resolve*-chNN.cache.json`) before re-running.

### Credits exhaustion mid-batch
When OpenRouter balance drops during a batch run, `assistant inference send` returns timeouts. The chapter being processed will have partial cached data (some runs missing chunks). Clear the affected chapter's cache and restart.

### conda env activation
`resolve.py` needs `pylem` which is only installed in conda env `main`. Running outside this env produces `ModuleNotFoundError: No module named 'pylem'`. Always activate before running.

### Dynamic VM IP
YC VM juno-ruaccent gets a new IP every stop/start. Old IP reassigns to another tenant immediately — host key change is expected, not a security concern. Look up IP via compute API before SSH.

### Strategic flush lock on git pushes
When driver_all.py pushes many commits quickly, git push may conflict. The script publishes per-chapter commits, which may collide. If push fails, wait and retry.

### Words with no stress after vote
Unstressed proper names (Массимой, Ялда) are not in pylem dictionary and ruaccent may not mark them. Collect per-book list using grep, add stress manually. Words with ё get automatic stress placement (ёт rule: if ё is present, it IS the stressed syllable).

### Review element counts differ from expected
Chapters where a total chunk was skipped show divergent `noanswer` values. Flagged in log as `noanswer N`. The vote script tolerates up to 3% missing chunks before marking the run as broken.
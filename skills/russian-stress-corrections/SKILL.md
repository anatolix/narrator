---
name: "Правка ударений (russian-stress-corrections)"
description: "Apply stress/ё corrections Anatoly reports by ear to ruaccent-marked narration scripts (roles_full-chNN.md, '+' before stressed vowel): find ALL forms and contexts, fix, log in exceptions.txt, commit+push. Includes the dictionary ё-fication sweep (eyo-kernel) that finds every missing ё in one pass, context-checked, shown to him BEFORE writing."
metadata:
  vellum:
    activation-hints:
      - user reports a wrong stress in the audiobook ("спорА должно быть сПора", "арИка -> Арика")
      - user says "не сработала ёрификация" or reports е instead of ё ("на нЕм -> на нЁм")
      - user asks to find all missing ё in narration scripts
      - "правки к ударениям"
    avoid-when:
      - full in-context audit of every '+' marker in a chapter (use russian-stress-mark-audit)
      - diff of original vs ruaccent output for letter drops (use ruaccent-letter-diff)
---

# Правка ударений

Scripts: `narrator/books/<book>/roles_full-chNN.md`. Format: `РОЛЬ: text`, `@РОЛЬ:` = cast header (skip), `+` placed immediately BEFORE the stressed vowel. Corrections log: `exceptions.txt` in the same dir, format `wrong -> right # chNN:line — note`.

## Single correction from Anatoly (the usual loop)

1. **Find every form, not just the one he heard.** Grep case-insensitively over all chapters, with context. Names: check ALL cases (Арика/Арики/Арике/Арику/Арикой) AND forms with NO `+` at all (ruaccent sometimes skips words). Exclude substring false hits (ш+арика ≠ Арика).
2. **Check meaning per context** before replacing. Example: «сб+егала» (сходила туда-обратно) vs «сбег+ала» (убегала, несов.) — fix only where the meaning matches; report the others and why they stay.
3. Replace with targeted `sed -i 'Ns/old/new/'` (line-scoped) or global only when every hit was verified.
4. Append a line to `exceptions.txt`.
5. Commit + push. **Push needs the explicit key:**
   `GIT_SSH_COMMAND="ssh -i $W/.ssh/id_ed25519 -o IdentitiesOnly=yes" git push` (plain push → Permission denied publickey).
6. Reply short: what changed (ch:line + snippet), commit hash, and the running list of chapters that need re-synthesis (the delivered audio/video still has the old stress). Don't re-synthesize until he says so — let corrections pile up.

## Ё-fication sweep (his "отличный хак", Sep 26)

ruaccent does not reliably restore ё. Instead of waiting for him to hear each one:

1. Download eyo-kernel dictionaries (path is `dictionary/`, NOT `dict_src/`):
   `https://raw.githubusercontent.com/e2yo/eyo-kernel/master/dictionary/{safe,not_safe}.txt`
   Format: `base(end1|end2|)` expands to forms; `#` = comment; leading `_` = flag, strip it.
2. Run `scripts/find_yo.py` — tokenizes every line, strips `+`, **lowercases** (library is unreliable with capitals), looks up е-form → ё-form, dumps `yo_candidates.json` with ch/line/context/whether the `+` already sits on the ё position.
3. **Do NOT auto-apply. Review every hit by context**, show him a table (ch:line | было → надо | context), plus a short "на твоё решение" list and a list of discarded false positives. Write nothing until he says go.
   - `safe` list: near-always real.
   - `not_safe` list: mostly noise. Typical false positives: все(pl)/всё, всем/всём (творит. «со всем» has no ё), чем/чём (only after о/в/при/на), лет/лёт, небо/нёбо, перед/перёд, самое/самоё, вселенная/вселённая, genitive sg vs nom pl (стекла, жены, звезды «две звезды», гнезда, весны), черта (line), темно, future узнаете/примет/пахнет, сложенный, воронье гнездо.
   - Truly optional variants (заряженный/заряжённый, перегруженными) → ask him.
4. On his go, run `scripts/apply_yo.py <book_dir>` after editing its table (`ch:line|unique context|word`). It locates the word by context in the `+`-stripped line, takes the ё index **from the dictionary** (never hand-count), and rewrites the word as `...+ё...` — so the stress moves onto ё even where ruaccent stressed another syllable (призн+ает → призна+ёт, щек+и → щ+ёки). Aborts entirely if any context is missing or ambiguous.
5. exceptions.txt note + commit + push as above. Recompute the re-synthesis chapter list.

## Pitfalls
- `grep -E` with `[а-яё]` ranges → "Invalid collation character". Use Python for Cyrillic regexes.
- Proper names from the dictionary (Кардашёв) — he wants ё; also consider splitting glued suffixes («КардашевV») for TTS.
- Heteronym/ё fix changes rhythm → the whole chapter's audio shifts; subtitles need re-timing on re-render.

## Годы и даты цифрами (Sep 26)
SpeechKit reads «в 1988 году» as bare digits, no case agreement. Fix: find all `(1[5-9]|20)\d\d` tokens, write each out by hand in the right case WITH `+` stress (only the last word of a compound ordinal declines: «между т+ысяча девятьс+от девян+осто восьм+ым и дв+е т+ысячи тр+етьим год+ами»). Expand «г.» → «г+ода/г+оду», day numbers in the same date («1 июля» → «п+ервое/п+ервого и+юля»), decades («1980-х» → «восьмидес+ятых», «2000-х» → «двухт+ысячных»). Watch non-years that match the pattern («в 2048 раз» = cardinal). Apply with `scripts/apply_nums.py` (table `ch:line|old clean substring|new`, context must be unique in the +-stripped line; aborts otherwise). Re-grep afterwards: 0 left.

## Числа внутри слов (Sep 26)
«31-мерный», «806-мерный» не ловятся поиском годов. Искать `\d+-?мерн` и битую склейку `(31) — мерный` (артефакт конвертации) → писать одним словом: тридцатиодном+ерный, восьмисотшестим+ерный. «размерность 31» → «тр+идцать од+ин». Generic applier: `scripts/apply_table.py <book_dir> <table.tsv>` (строки `ch:line|old|new`). Трюк: чтобы не потерять `+` в соседнем слове, бери в old хвост слова («сти 31.» → «сти тр+идцать од+ин.»).

## Все прочие цифры + потерянные символы (Sep 26)
При конвертации в roles_full потерялись %, /, №, +, −, =, ², ·10ⁿ, ω («50/50»→«5050», «100 %»→«100  », «Вселенная+1»→«Вселенная1»). НЕ угадывать — сверять с исходником art/fine-structure/fine-structure.ru.txt (grep по соседним словам). Мои догадки ошибались: «23 пути» было «2/3 пути», «Вселенная1» в 41:237 было «Вселенная–1». Время → «восемь двадцать», проценты → «сто процентов/стопроцентный», десятичные → «ноль целых восемь десятых», коды (M2B, F-22, A4, 88-0009-ATY) не трогать, номера глав и «(часть N)» в заголовках — цифрой. Таблица: scratch/nums/digits.tsv, применение apply_table.py.

## Имена в косвенных падежах (Sep 27)
- ruaccent в косвенных падежах перескакивает ударение: Р+ула → Рул+е, М+оксон → Мокс+она. Норма: ударение как в именительном, во всех падежах.
- `scripts/names_check.py` группирует слова с заглавной по основе и показывает основы, где слог ударения разный. Ложные срабатывания: обычные слова в начале предложения (Земля, как, потом, больше, вещи). Показать таблицу Анатолию, применять после его ОК.
- Ограничение: ловит только расхождения. Если имя везде размечено одинаково неправильно, найдётся только на слух.
- Если правка не находит слово в строке, посмотреть строку глазами: часто это склейка от съеденного символа («Митч+уКсио» = «Митчу/Ксио»).

## Косые черты «/» (Sep 27)
- Конверсия съедала «/» и склеивала слова. `scripts/slash_check.py` сверяет каждое «/» исходника со скриптом: СКЛЕЙКА / дефис / НЕ НАЙДЕНО.
- Как заменять:
  - одна сущность или составной термин → дефис (Кс+ио-М+итч, жрец-астролог, массы-энергии, ана-ката);
  - выбор → «или» (работает или работал), пара → «и» (сюжет и хронологию);
  - перечень → запятые (камеры, страж, охранник, …);
  - ж/д → железнодор+ожными; км/ч → километров в час; 50/50 → пятьдесят на пятьдесят; 2/3 → две трети;
  - коды (LSEAT …199204/444KJ) → вернуть «/».
- Аббревиатуры и адреса: синтезировать пробы, выбирает Анатолий. Выбрано: бункер A/T/Y → Эй-Ти-Уай; qntm.org/discuss → «кью-эн-ти-эм т+очка орг слэш диск+асс». Код 88-0009-ATY не трогать.

## Римские числа (Sep 27)
- XXI век → дв+адцать п+ервого в+ека / в дв+адцать п+ервом в+еке; VI/VII/VIII класса → шест+ого/седьм+ого/восьм+ого кл+асса.
- Название с номером → дефис, число не склоняется: «Кардаш+ёв-П+ять», «Кардаш+ёвым-П+ять», «Вен+ерой-дв+а».
- Буквы (ось X, об X, блок C) не трогать, движок читает их как буквы.

## Проверки движка и мелкие правила (Sep 27)
- Сравнивать пробы по md5, а не по длительности: если плюс ничего не меняет, mp3 побайтно одинаковые. Так выяснилось, что плюс на «вести» игнорируется, а плюс на «без» даёт «бЕз». Норма: «без в+ести».
- «на (его/твоём) счету» → счет+у, без ё. «по счёту», «по большому счёту» → сч+ёту.
- Ё-свип пропускает формы с заглавной буквы (Нерождённых) — после свипа грепнуть заглавные отдельно.

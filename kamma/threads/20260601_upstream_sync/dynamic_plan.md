# Dynamic Plan: Upstream Sync 2026-06-01

> **Stage 3 executor (FAST): read this file and `kamma/upstream_sync/guide.md` only.**
> Execute items in the order written. Mark each `[ ]` → `[~]` → `[x]`.
> Every edit below gives an exact file path, a literal anchor string, and the literal
> text to insert/replace. Do not analyze, redesign, or improvise. If any anchor is
> missing or a test fails in a way not covered here, STOP and hand off to ADVANCED.

## Upstream Range
- From (`as_upstream` start): `44a8a00556cce9bd3874a94efb5dfaceaaf20a66`
- To (`upstream/main`, tag v0.4.20260531): `40083765d770a68b93bfc5e7227b5973e3faf414`

## Iron Rule (reminder)
When a shadow breaks, the ONLY fix is to copy upstream's exact solution, then re-apply
the local changes named in `smd/`. No workarounds, no alternative imports, no try/except
papering. The upstream sources are correct.

## Critical tooling facts that shape this sequence (verified Stage 2)
1. `execute_sync.py` refuses to pull if `prep_manifest.json.discuss_paths` OR `blocker_paths`
   is non-empty (`verify_manifest(allow_discuss=False, allow_blockers=False)`,
   execute_sync.py:178-185; sync_runtime.py:75-92). `blocker_paths` is cleared by the
   registry+code edits in Phase A. `discuss_paths` (`.gitignore`, `AGENTS.md`, `db/models.py`)
   is permanent — those three are in `modified_upstream_files` so the pull always excludes
   them via `get_permanent_exclusions` (execute_sync.py:69-76). After the prep rerun, FAST
   manually sets `"discuss_paths": []` in `prep_manifest.json` (Phase A step 6). This is safe:
   emptying the field only satisfies the gate; it cannot cause an overwrite.
2. `execute_sync.py` refuses on a dirty tree and requires branch `sbs-ru`
   (`_check_if_dirty` via `git status --porcelain`, execute_sync.py:40-48,155-164).
   Phase B restores submodules and makes a user-run pre-sync commit to get a clean tree.
3. `check_shadow_modifications.py` is DIRECTORY-granular (lines 189-232): a dir-mapped
   shadow is flagged only if NO file under it changed since the sync commit. Because we DO
   port `dpd_headword.html`/`.jinja` into the `ru_*`/`sbs_*` template dirs, and edit
   `shared_data/help_ru/abbreviations.tsv`, those dirs count as "modified" → **no
   `reviewed_shadow_noops.json` entries are required this sync.** The home.html RSS skip
   is documented in prose only (Phase D, Skips).

---

## LOCKED DECISIONS (confirmed; do NOT re-ask the user)
- **A1 `db/models.py` → PORT** (additive to `SuttaInfo`). Literal hunks in Phase D.1.
- **A2 `.gitignore` → MERGE** (port upstream additions, keep all fork lines). Phase D.2.
- **A3 `AGENTS.md` → SKIP** (preserve fork version; upstream only added 3 generic sections).
- **B Blocker strategy → Option 1 (code fix)**: make `prep_analyzer.is_skipped()` honor
  `no_sync_files`. Phase A.
- **C `tools/ai_models.json` → `no_sync_files`** (fork tracks it; not gitignored). Phase A.
- **`exporter/analysis/` + `exporter/mcp/` → keep local** (already in `no_sync_files`).
- **`gui2/pass2_add_view.py` → PORT** the upstream X-queue + sutta-filter feature.
  `discuss:false`, orthogonal to the fork's removed stash code, dependencies arrive via the
  pull. Keep the local `tools.fast_api_utils_dps` import. Phase D.10.

### Inspection skips (document in commit prose; no ledger entries)
- **home.html (ru + sbs) RSS → SKIP.** Upstream added an `<link rel="alternate">` RSS head
  tag + an RSS button; the URL is the English DPD feed, not relevant to RU/SBS sites. Both
  shadows diverge (no matching anchor).
- **tools/paths_ru.py + tools/paths_dps.py → SKIP.** New upstream attrs
  (`dpd_anki_apkg_path`, `syn_var_del_exceptions_path`) are unused locally (`rg` exit 1).
- **mkdocs_ru.yaml → SKIP** upstream's `custom_dir` (English-branded header) and the
  `Anki` nav entry (deferred to Stage 4 with `docs_rus/install/anki.md`).
- **ru_static.yml → SKIP** the RSS step (English feed) and the `uv sync` modernization
  (CI-only, no local test coverage; user may request separately).

---

## Phase A — Clear blockers (registry + code) [no pull yet]

### A.1 Registry edits — `kamma/upstream_sync/registry.json`
Add these to the existing `skip_sync_patterns` array (skip_sync files are STILL synced
unless also in `no_sync_files`; this only removes them from prep's blocker scan):
- Dir patterns (trailing slash REQUIRED): `scripts/find/`, `scripts/suttas/`,
  `exporter/anki/`, `db_tests/`, `.claude/`, `.zed/`, `scripts/build/mkdocs_overrides/`
- File patterns: `scripts/fix/double_consonant_replacer.py`, `scripts/fix/variant_cleaner.py`,
  `scripts/fix/verb_finder.py`, `scripts/build/generate_books_tsv.py`,
  `scripts/build/anki_updater.py`, `tools/ai_nvidia.py`, `tools/cst_book_translator.py`,
  `tools/cst_book_translator.tsv`, `tools/rss_feed.py`, `tools/synonym_variant.py`,
  `gui2/pass2_x_manager.py`, `misc/DPD-feedback.xlsx`, `scripts/dbreader.py`

Add to the existing `no_sync_files` array: `tools/ai_models.json`

> No new shadows/categories are created → no `smd/` edits and no registry-category edits.
> But A.4 still runs `validate_registry.py` + `verify_smd_coverage.py` (Shadow Doc Gate).

### A.2 Code fix — `kamma/upstream_sync/scripts/registry_helper.py`
After the existing `get_skip_sync_patterns` function (it ends at line 168), ADD this new
function:
```python
def get_no_sync_files(data: dict[str, object]) -> list[str]:
    """Return the list of permanent no-sync infrastructure paths."""
    entries = data.get("no_sync_files", [])
    if not isinstance(entries, list):
        return []
    return [p for p in entries if isinstance(p, str)]
```

### A.3 Code fix — `kamma/upstream_sync/scripts/prep_analyzer.py`
1. In the `from ...registry_helper import (` block (lines 12-20), add `get_no_sync_files,`
   to the imported names.
2. In `__init__`, immediately AFTER the line `self.skip_patterns = ...` (line 103), add:
   ```python
           self.no_sync_files = get_no_sync_files(self.registry)
   ```
   (Match the existing indentation of `self.skip_patterns`.)
3. Replace the entire current `is_skipped` method (lines 110-117) with:
   ```python
       def is_skipped(self, path: str) -> bool:
           """Return True when the path is outside sync scanning scope."""
           for entry in self.no_sync_files:
               if path == entry or path.startswith(entry.rstrip("/") + "/"):
                   return True
           for pattern in self.skip_patterns:
               if pattern.endswith("/") and path.startswith(pattern):
                   return True
               if fnmatch.fnmatch(path, pattern):
                   return True
           return False
   ```

### A.4 Validate registry + code
- `uv run ruff check --fix kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/prep_analyzer.py`
- `uv run ruff format kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/prep_analyzer.py`
- `uv run pyright kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/prep_analyzer.py`
- `uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/prep_analyzer.py`
- `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` → must pass.
- `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` → must pass.

### A.5 Rerun prep and assert blockers cleared
- `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py kamma/threads/20260601_upstream_sync`
- **→ verify:** open `kamma/threads/20260601_upstream_sync/prep_manifest.json` and confirm
  `"blocker_paths": []`. If non-empty, STOP and hand off to ADVANCED.

### A.6 Acknowledge permanent discuss paths
- Manually edit `kamma/threads/20260601_upstream_sync/prep_manifest.json`: set
  `"discuss_paths": []`. (Safe — `.gitignore`, `AGENTS.md`, `db/models.py` are
  `modified_upstream_files`, permanently excluded from the pull regardless.)
- **→ verify:** `discuss_paths` and `blocker_paths` are both `[]`.

---

## Phase B — Clean tree + pre-sync commit (USER-RUN commit)

> **ADVANCED resolution (2026-06-01, dirty-submodule blocker):** The submodules show
> `" M"` in `git status --porcelain` from INTERNAL worktree content only (untracked temp
> files in `resources/bw2`; modified tracked files + a deleted `.DS_Store` in
> `resources/sc-data`). `git submodule status` shows NO `+` prefix → parent gitlinks are
> correct; a superproject commit cannot clean submodule internals. Resolution = **Option 2**:
> patch `execute_sync._check_if_dirty` to pass `--ignore-submodules=dirty`. This is the
> design-correct fix (the check protects upstream-tracked files, not submodule internals;
> gitlink drift is still reported), it is local (`kamma/` is never synced → never clobbered),
> and it is non-destructive (does NOT touch the unknown sc-data modifications). Verified:
> `git status --porcelain --ignore-submodules=dirty` already shows zero `resources/*` lines.

### B.1 Patch the dirty check — `kamma/upstream_sync/scripts/execute_sync.py`
Replace the ENTIRE current `_check_if_dirty` method (execute_sync.py:40-48):
```python
    def _check_if_dirty(self) -> bool:
        """Check if the current working tree has uncommitted changes."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
```
with:
```python
    def _check_if_dirty(self) -> bool:
        """Check if the current working tree has uncommitted changes.

        Submodule-internal modifications and untracked files are ignored
        (``--ignore-submodules=dirty``): they cannot be cleaned by a
        superproject commit and are irrelevant to protecting uncommitted
        edits to upstream-tracked files. Gitlink (recorded-commit) changes
        are still reported.
        """
        result = subprocess.run(
            ["git", "status", "--porcelain", "--ignore-submodules=dirty"],
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
```
Then run the Python gate on the edited file:
- `uv run ruff check --fix kamma/upstream_sync/scripts/execute_sync.py`
- `uv run ruff format kamma/upstream_sync/scripts/execute_sync.py`
- `uv run pyright kamma/upstream_sync/scripts/execute_sync.py`
- `uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/execute_sync.py`
- **→ verify:** `rg -n "ignore-submodules=dirty" kamma/upstream_sync/scripts/execute_sync.py`
  returns 1. (Do NOT run `git submodule update --init --recursive` — it does not clean the
  internal dirt and `resources/fdg_dpd` fetch fails anyway.)

### B.2 Pre-sync commit (prepare message; USER runs `git commit`)
Stage the thread dir + the Phase A edits + the B.1 execute_sync fix, then present this
commit for the user to run:
- `git add kamma/threads/20260601_upstream_sync kamma/upstream_sync/registry.json kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/execute_sync.py`
- Commit message (USER runs):
  `#pre-sync: clear sync blockers, ack discuss, 2026-06-01`
- **→ verify:** after the user commits, branch is `sbs-ru` and
  `git status --porcelain --ignore-submodules=dirty` is EMPTY. (A bare
  `git status --porcelain` will still list ` M resources/*` — that is the expected,
  ignored submodule-internal dirt, NOT a blocker. Do not attempt to clean it.) If
  `--ignore-submodules=dirty` is non-empty, resolve before Phase C.

---

## Phase C — Automated pull (Commit 1, USER-RUN commit)

### C.1 Run execute_sync
- (Optional) review `kamma/threads/20260601_upstream_sync/run_exclusions.txt` if present.
- `uv run python3 kamma/upstream_sync/scripts/execute_sync.py kamma/threads/20260601_upstream_sync`
- This pins `as_upstream` to the verified manifest SHA and leaves changes UNSTAGED.

### C.2 Delete upstream-removed files (git rm — BEFORE staging)
`git checkout as_upstream -- .` does not delete files upstream removed. Run:
- `git rm .zed/launch.json`
- `git rm scripts/dbreader.py`
- `git rm scripts/build/anki_updater.py`  (upstream MOVED it to
  `exporter/anki/anki_updater.py`, which arrives via the `exporter/anki/` pull)
- (`.claude/commands/dpd-newsletter.md` is already absent — no action.)

### C.3 Review + stage + Commit 1 (USER-RUN commit)
- Review `git diff`.
- Stage with `git add .` (respects `.gitignore`; NEVER `git add -A -- <list>`).
- Commit message (USER runs): replace `<N>` with the file count from execute_sync output:
  `#sync: upstream pull 44a8a00..40083765, <N> files, 2026-06-01`

### C.4 Post-pull dependency verification (BEFORE Phase D.10)
- `rg -n "^SUTTA_FIELDS = " gui2/dpd_fields_lists.py` → must match (arrives via pull).
- `test -f gui2/pass2_x_manager.py` → must exist (arrives via pull).
- If either is missing, STOP before D.10 and hand off to ADVANCED.

---

## Phase D — Manual ports (Commit 2, USER-RUN commit)

> Apply each edit literally. After ALL edits, run Phase E verification, then prepare
> Commit 2. Run ruff check --fix + ruff format + pyright + pyrefly on every edited `.py`
> before reporting completion.

### D.1 `db/models.py` — PORT (A1) — anchors VERIFIED against local file
Three additive insertions into `class SuttaInfo`. (Local fork reordered members vs
upstream, so anchors differ from the raw upstream diff — use these exact local anchors.)

**(a) AN-nipāta branch** — inside the `sc_vagga_link` property. Anchor (unique):
```
            return f"https://suttacentral.net/dn-{slug}"

        if not self.sc_vagga:
```
Replace with:
```
            return f"https://suttacentral.net/dn-{slug}"

        # AN individual nipāta: pitaka path with nipāta number
        # (e.g. AN1 → pitaka/sutta/numbered/an/an1)
        if book_code.lower() == "an" and self.is_nipata:
            m = re.match(r"^AN(\d+)$", self.dpd_code, re.IGNORECASE)
            if m:
                return (
                    f"https://suttacentral.net/pitaka/sutta/numbered/an/an{m.group(1)}"
                )
            return None

        if not self.sc_vagga:
```

**(b) `is_nipata` property** — after `is_samyutta`, before `is_vagga`. Anchor (unique):
```
        return base.endswith("saṃyutta")

    @cached_property
    def is_vagga(self) -> bool:
```
Replace with:
```
        return base.endswith("saṃyutta")

    @cached_property
    def is_nipata(self) -> bool:
        if not (self.dpd_sutta and self.dpd_code):
            return False
        if "." in self.dpd_code or "-" in self.dpd_code:
            return False
        names = [self.dpd_sutta, self.dpd_sutta_var]
        return any("nipāta" in name for name in names if name)

    @cached_property
    def is_vagga(self) -> bool:
```

**(c) `is_pannasaka` property** — after the `is_vagga` block, before `sc_vagga_link`.
Anchor (unique):
```
        return "-" in self.dpd_code and bool(
            self.cst_vagga or self.sc_vagga or self.bjt_vagga
        )

    @cached_property
    def sc_vagga_link(self) -> str | None:
```
Replace with:
```
        return "-" in self.dpd_code and bool(
            self.cst_vagga or self.sc_vagga or self.bjt_vagga
        )

    @cached_property
    def is_pannasaka(self) -> bool:
        names = [self.dpd_sutta, self.dpd_sutta_var]
        return any(
            name and ("paṇṇāsapāḷi" in name or "paṇṇāsaka" in name) for name in names
        )

    @cached_property
    def sc_vagga_link(self) -> str | None:
```
**→ verify:** `rg -n "def is_nipata|def is_pannasaka|pitaka/sutta/numbered/an" db/models.py`
returns 3 matches; `uv run pyright db/models.py` clean.

### D.2 `.gitignore` — MERGE (A2)
Apply these edits to the LOCAL `.gitignore`. (Upstream additions ported; all fork lines
kept. `exporter/analysis/{input,output,reports}` are already ignored via the fork's unique
section, so they are NOT re-added. `.claude/scheduled_tasks.lock` is left as-is because the
fork's unique section already has the broad `.claude/`. `tools/ai_models.json` removal is a
no-op — the fork never had that line.)

**(a)** Replace `.zed/tasks.json` with `.zed/`.

**(b)** After the line `/.qwen` (the FIRST occurrence, immediately before `__init__.py`),
insert these four lines:
```
/dpd.db-shm
/dpd.db-wal
/exporter/anki/templates/.backups
/exporter/anki/templates/old
```

**(c)** After `db/suttas/Untitled Document`, before `docs_site`, insert:
```
docs/rss.xml
```

**(d)** Delete the line `dpd/` (it sits between `dpd.db.tar.bz2` and
`exporter/archive/other_dictionaries_legacy/*`).

**(e)** Replace the two lines
```
scripts/suttas/cst/*.tsv
scripts/suttas/sc/*.tsv
```
with the single line:
```
scripts/suttas/*/*.tsv
```

**(f)** After the line `typescript`, before the second `/.qwen` line, insert:
```
/graphify-out
.antigravitycli/
.pytest_cache/
.ruff_cache/
```
**→ verify:** `rg -n "graphify-out|/dpd.db-shm|docs/rss.xml|scripts/suttas/\*/\*.tsv" .gitignore`
returns matches; `rg -n "^dpd/$" .gitignore` returns nothing (exit 1).

### D.3 family imports (russian_copies) — MIRROR
In each of `db/families/family_compound_ru.py`, `db/families/family_root_ru.py`,
`db/families/family_word_ru.py`: replace
`from scripts.build.anki_updater import family_updater`
→ `from exporter.anki.anki_updater import family_updater`
**→ verify:** `rg -n "from scripts.build.anki_updater" db/families/` returns nothing;
`rg -n "from exporter.anki.anki_updater import family_updater" db/families/` returns 3.

### D.4 `exporter/webapp/main_ru.py` (CORS) — PORT
- After the line `from fastapi import FastAPI, Request` add:
  `from fastapi.middleware.cors import CORSMiddleware`
- Immediately BEFORE the line `app.add_middleware(GZipMiddleware, minimum_size=500)` add:
  `app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])`
**→ verify:** `rg -n "CORSMiddleware" exporter/webapp/main_ru.py` returns 2.

### D.5 webapp templates (ru + sbs) — PORT, depends on D.1
Apply the SAME upstream hunks to BOTH `exporter/webapp/ru_templates/dpd_headword.html`
and `exporter/webapp/sbs_templates/dpd_headword.html`:
1. After the line `{% set is_samyutta = d.su.is_samyutta if d.su else false %}` add:
   ```
   {% set is_nipata = d.su.is_nipata if d.su else false %}
   {% set is_pannasaka = d.su.is_pannasaka if d.su else false %}
   ```
2. Button label line — replace
   `{% if is_samyutta %}saṃyutta{% elif is_vagga %}vagga{% else %}<X>{% endif %}</a>`
   → `{% if is_samyutta %}saṃyutta{% elif is_pannasaka %}paṇṇāsaka{% elif is_vagga %}vagga{% elif is_nipata %}nipāta{% else %}<X>{% endif %}</a>`
   where `<X>` is the existing else word — `сутта` in ru, `sutta` in sbs. KEEP it.
3. Replace `{% if d.su.sc_eng_sutta and not is_vagga and not is_samyutta %}`
   → `{% if d.su.sc_eng_sutta and not is_samyutta %}`
   (This exact string is unique; do NOT touch the cst/sc/bjt `_sutta` conditions that also
   contain `not is_vagga and not is_samyutta`.)
4. After the `SC Saṃyutta Card` `<a ...>...</a>` line, insert:
   ```
   {% elif is_nipata and d.su.sc_vagga_link %}
   <a href="{{ d.su.sc_vagga_link }}" target="_blank">SC Nipāta Card</a>
   ```
**→ verify:** `rg -n "is_nipata|is_pannasaka|SC Nipāta Card" exporter/webapp/ru_templates/dpd_headword.html exporter/webapp/sbs_templates/dpd_headword.html` shows the new lines in both.

### D.6 goldendict templates (ru + sbs) — PORT, depends on D.1
Actual shadow files are `exporter/goldendict/ru_components/templates/dpd_headword_ru.jinja`
and `exporter/goldendict/sbs_templates/dpd_headword_sbs.jinja` (NOT `dpd_headword.jinja` —
ignore the manifest's naive `local_target_path`). Apply the SAME 4 hunks as D.5:
1. After `{% set is_samyutta = d.su.is_samyutta if d.su else false %}` add the two `set`
   lines (`is_nipata`, `is_pannasaka`).
2. Button label (single line) inner — merge to:
   `{% if is_samyutta %}saṃyutta{% elif is_pannasaka %}paṇṇāsaka{% elif is_vagga %}vagga{% elif is_nipata %}nipāta{% else %}<X>{% endif %}`
   (`<X>` = `сутта` ru / `sutta` sbs; ru uses `data-target="ru_sutta_info_..."`, sbs uses
   `data-target="sbs_sutta_info_..."` — keep each file's existing data-target unchanged).
3. Replace `{% if d.su.sc_eng_sutta and not is_vagga and not is_samyutta %}`
   → `{% if d.su.sc_eng_sutta and not is_samyutta %}`.
4. After the `SC Saṃyutta Card` `<a ...>...</a>` line, insert:
   ```
   {% elif is_nipata and d.su.sc_vagga_link %}
   <a href="{{ d.su.sc_vagga_link }}" target="_blank">SC Nipāta Card</a>
   ```
**→ verify:** `rg -n "is_nipata|is_pannasaka|SC Nipāta Card" exporter/goldendict/ru_components/templates/dpd_headword_ru.jinja exporter/goldendict/sbs_templates/dpd_headword_sbs.jinja` shows the new lines in both.

### D.7 `shared_data/help_ru/abbreviations.tsv` — PORT (DNnt row)
help_ru is 7 columns. Insert this row AFTER the `DNa` row (between `DNa` and `DNt`),
verbatim (tabs between columns; columns 3, 4, and 6... note: 7 fields total, the Russian
column already filled):
```
"DNnt"	"Dīgha Nikāya Nava-ṭīkā, Sādhuvilāsinī"			"Newer sub-commentary on the Sīlakkhandhavagga of the Dīgha Nikāya; lit. charming and beautiful"		"Дигха Никая Новый Подкомментарий"
```
**→ verify:** `rg -n "DNnt" shared_data/help_ru/abbreviations.tsv` returns 1; the row has
7 tab-separated fields.

### D.8 `scripts/bash/generate_components.sh` — inspired backport (REQUIRED)
The line `uv run python scripts/build/anki_updater.py` references a path being deleted
(C.2). Replace that line with `uv run python exporter/anki/anki_updater.py` AND add a new
line `uv run python exporter/anki/anki_apkg_exporter.py` (match the file's existing line
style). Read the `.sh` first to match exact indentation/prefix.
**→ verify:** `rg -n "scripts/build/anki_updater.py" scripts/bash/generate_components.sh`
returns nothing; `rg -n "exporter/anki/anki_updater.py|exporter/anki/anki_apkg_exporter.py" scripts/bash/generate_components.sh` returns 2.

### D.9 `tests/smoke_test_sync.py` — update moved import (5 refs)
Replace `scripts.build.anki_updater` → `exporter.anki.anki_updater` in all 5 places
(lines ~622 docstring, ~626, ~627, ~878, ~879). Use replace-all on the exact dotted string.
**→ verify:** `rg -n "scripts.build.anki_updater" tests/smoke_test_sync.py` returns nothing;
`rg -n "exporter.anki.anki_updater" tests/smoke_test_sync.py` returns 5.

### D.10 `gui2/pass2_add_view.py` — PORT (depends on C.4 dependencies)
Apply these 12 literal edits. Keep the local `from tools.fast_api_utils_dps import
request_dpd_server` (line 24) UNCHANGED. Do not restore stash code.

1. In the `from gui2.dpd_fields_lists import (` block, between `    ROOT_FIELDS,` and
   `    WORD_FIELDS,`, insert `    SUTTA_FIELDS,`.
2. After the line `from gui2.pass2_pre_new_word_manager import Pass2NewWordManager`, insert
   `from gui2.pass2_x_manager import Pass2XManager`.
3. After the line `        self.additions_manager = self.toolkit.additions_manager`, insert
   `        self._x_manager = Pass2XManager(self._db)`.
4. After the `self._additions_button = ft.ElevatedButton(...)` block (3 lines ending
   `        )`), before `        self._pread_button = ft.ElevatedButton(`, insert:
   ```python
           self._x_button = ft.ElevatedButton(
               "X", on_click=self._click_x_button, tooltip="filter queue"
           )
   ```
5. After the line `            on_submit=self._click_edit_headword,`, insert
   `            on_blur=self._disable_id_field_autofocus,`.
6. In the filter RadioGroup, after `                    ft.Radio(value="compound", label="Compound"),`,
   insert `                    ft.Radio(value="sutta", label="Sutta"),`.
7. In the top-section button Row, replace the two consecutive lines
   ```
                               self._additions_button,
                               self._pread_button,
   ```
   with
   ```
                               self._additions_button,
                               self._x_button,
                               self._pread_button,
   ```
8. Replace the anchor (controls-list end → `_on_delete_hover`):
   ```
           self.controls = [
               self._top_section,
               self._middle_section,
               self._bottom_section,
           ]

       def _on_delete_hover(self, e: ft.ControlEvent) -> None:
   ```
   with the same block plus the new method inserted before `_on_delete_hover`:
   ```
           self.controls = [
               self._top_section,
               self._middle_section,
               self._bottom_section,
           ]

       def _disable_id_field_autofocus(self, e: ft.ControlEvent) -> None:
           if self._enter_id_or_lemma_field.autofocus:
               self._enter_id_or_lemma_field.autofocus = False

       def _on_delete_hover(self, e: ft.ControlEvent) -> None:
   ```
9. In `add_headword_to_examples_and_commentary`, replace the anchor:
   ```
                   example_2_field.word_to_find_field.value = lemma_clean[:-1]
                   example_2_field.word_to_find_field.value = lemma_clean[:-1]

       def _click_edit_headword(self, e: ft.ControlEvent) -> None:
   ```
   with:
   ```
                   example_2_field.word_to_find_field.value = lemma_clean[:-1]
                   example_2_field.word_to_find_field.value = lemma_clean[:-1]

           self._apply_sutta_prefill()

       def _click_edit_headword(self, e: ft.ControlEvent) -> None:
   ```
10. Insert the `_apply_sutta_prefill` method. Replace the anchor:
    ```
            self.update_message("speech marks updated")

        def _handle_filter_change(self, e: ft.ControlEvent) -> None:
    ```
    with:
    ```
            self.update_message("speech marks updated")

        def _apply_sutta_prefill(self) -> None:
            """If sutta filter is active, prefill empty source_1 and commentary with '-'."""
            if self._filter_radios.value != "sutta":
                return
            for prefill_name in ("source_1", "commentary"):
                prefill_field = self.dpd_fields.get_field(prefill_name)
                if prefill_field is not None and not prefill_field.value:
                    prefill_field.value = "-"

        def _handle_filter_change(self, e: ft.ControlEvent) -> None:
    ```
11. In `_handle_filter_change`, replace the anchor:
    ```
            elif filter_type == "compound":
                visible_fields = COMPOUND_FIELDS
            elif filter_type == "word":
    ```
    with:
    ```
            elif filter_type == "compound":
                visible_fields = COMPOUND_FIELDS
            elif filter_type == "sutta":
                visible_fields = SUTTA_FIELDS
                self._apply_sutta_prefill()
            elif filter_type == "word":
    ```
12. In `clear_all_fields`, replace the anchor:
    ```
            self.headword = None  # Resetting the data model reference
            self._filter_radios.value = "all"  # Reset filter to 'all'
            self.headword_original = None  # Resetting the original data reference
    ```
    with:
    ```
            self.headword = None  # Resetting the data model reference
            if self._filter_radios.value == "sutta":
                self._apply_sutta_prefill()
                self.dpd_fields.filter_fields(SUTTA_FIELDS)
            else:
                self._filter_radios.value = "all"  # Reset filter to 'all'
            self.headword_original = None  # Resetting the original data reference
    ```
13. Add the `_click_x_button` method. Replace the anchor (end of
    `_click_additions_button` → start of `_click_pread_button`):
    ```
            self.page.update()

        def _click_pread_button(self, e: ft.ControlEvent) -> None:
            """Loads the next proofreader correction and populates the gui."""
    ```
    with:
    ```
            self.page.update()

        def _click_x_button(self, e: ft.ControlEvent) -> None:
            """Loads the next headword from the X filter queue."""
            if self._x_manager._loaded and not self._x_manager._queue:
                # Re-read pass2_x_manager.py from disk so edits to filter_query
                # take effect without restarting the app. Bypasses sys.modules
                # and __pycache__ — importlib.reload was not reliably picking
                # up changes.
                import importlib.util
                from pathlib import Path

                path = Path(__file__).parent / "pass2_x_manager.py"
                spec = importlib.util.spec_from_file_location(
                    f"pass2_x_manager_live_{id(self)}", path
                )
                assert spec is not None and spec.loader is not None
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                self._x_manager = mod.Pass2XManager(self._db)

            headword_id, remaining = self._x_manager.get_next()

            if headword_id is None:
                self.update_message("No more X words")
                self.page.update()
                return

            try:
                headword = self._db.get_headword_by_id(headword_id)
                if not headword:
                    self.update_message(f"Headword ID {headword_id} not found in DB")
                    self.page.update()
                    return

                self.clear_all_fields()
                self.headword = headword
                self._enter_id_or_lemma_field.value = headword.lemma_1
                self.headword_original = copy.deepcopy(headword)
                self.dpd_fields.update_db_fields(headword)
                self.add_headword_to_examples_and_commentary()

                self.update_message(
                    f"Loaded {headword.lemma_clean}. {remaining} X remaining."
                )
            except Exception as ex:
                self.update_message(f"Error loading X word: {str(ex)}")

            self.page.update()

        def _click_pread_button(self, e: ft.ControlEvent) -> None:
            """Loads the next proofreader correction and populates the gui."""
    ```
**→ verify:** `uv run ruff check gui2/pass2_add_view.py` and `uv run pyright gui2/pass2_add_view.py`
clean; `rg -n "_click_x_button|_apply_sutta_prefill|_disable_id_field_autofocus|SUTTA_FIELDS|Pass2XManager" gui2/pass2_add_view.py` shows all new symbols.

### D.11 export_dpd_ru.py / export_dpd_sbs.py — OPTIONAL (recommend YES)
After `p.join()` (`export_dpd_ru.py:301`, `export_dpd_sbs.py:326`), inside the
`for p in processes:` loop, add:
```python
            if p.exitcode != 0:
                raise RuntimeError(f"Worker process failed with exit code {p.exitcode}")
```
(Match the loop indentation.) Mark OPTIONAL — user may veto during approval.
**→ verify:** `rg -n "Worker process failed" exporter/goldendict/export_dpd_ru.py exporter/goldendict/export_dpd_sbs.py` returns 2 (if applied).

---

## Phase E — Verification (Stage 3)
Run all and record output in `handoff.md`:
- Per-file Python gate on every edited `.py` (models.py, main_ru.py, family_*_ru.py,
  pass2_add_view.py, smoke_test_sync.py, optionally export_dpd_*):
  `uv run ruff check --fix <file>` ; `uv run ruff format <file>` ;
  `uv run pyright <file>` ; `uv run --with pyrefly pyrefly check --min-severity warn <file>`
- `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py -v`
- `uv run python3 tests/check_shadow_modifications.py` → expect clean (dir-granular; the
  edited template dirs + help_ru count as modified; home.html RSS skip needs no ledger).
- `uv run python tests/smoke_test_sync.py`

## Phase F — Commit 2 (USER-RUN commit)
- Stage with `git add .`.
- Commit message (USER runs): `#sync: manual merge resolutions 2026-06-01`

---

## Out of scope for this plan (later stages)
- **Stage 4 (docs):** `docs/abbreviations.md`, `docs/changelog.md`, `docs/install/anki.md`
  (NEW), `docs/install/chromebook.md`, `docs/newsletters.md` → `docs_rus/` parity. The
  `mkdocs_ru.yaml` Anki nav entry is added in Stage 4 alongside `docs_rus/install/anki.md`.

## Known issues / notes (do NOT fix in this sync)
- `execute_sync.py` has no `--acknowledge-discuss` flag — the manual `discuss_paths: []`
  edit (A.6) is the only path. Future tooling improvement.
- `resources/fdg_dpd` submodule fetch fails (remote not found) — pre-existing.
- Submodules report `" M"` from internal worktree dirt (untracked temp files, modified
  tracked files, stray `.DS_Store`). RESOLVED in B.1 via `--ignore-submodules=dirty` in
  `execute_sync._check_if_dirty`. This dirt is pre-existing, not caused by the sync, and is
  intentionally left untouched.
- Manifest `mapped_actions[].local_target_path` is wrong for renamed goldendict shadows
  (`dpd_headword_ru.jinja`/`_sbs.jinja`, not `dpd_headword.jinja`) — D.6 uses the real paths.

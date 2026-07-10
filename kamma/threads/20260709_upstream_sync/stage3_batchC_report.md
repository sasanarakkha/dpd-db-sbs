# Stage 3, Batch C — Execution Report

Range: `OLD=518672a65fa3` → `NEW=be49bffe2c2c`. Items: S4, S5, S6, S7, S8 (§9 of `dynamic_plan.md`).

## S4 — `exporter/deconstructor/deconstructor_exporter_ru.py` + registry

**Status: DONE**

Files changed:
- `exporter/deconstructor/deconstructor_exporter_ru.py`
- `kamma/upstream_sync/registry.json` (new `russian_copies` entry)

Upstream pattern mirrored (`git diff OLD NEW -- exporter/deconstructor/deconstructor_exporter.py`):
upstream dropped `DeconstructorData.__init__(pth, jinja_env)` in favor of `DeconstructorData(result)` (1 arg) plus a module-level `generate_deconstructor_header(jinja_env)` called once before the loop; the loop then does `data = DeconstructorData(i); html_string = header + minify(template.render(data=data))`.

Edit applied:
- Removed `DeconstructorData_ru(DeconstructorData)` subclass and its `_generate_header` override.
- Added module-level `generate_deconstructor_header_ru(jinja_env: Environment) -> str` — literal copy of upstream `generate_deconstructor_header`'s body, with `get_template("deconstructor_header_ru.jinja")` substituted for the RU template.
- Added `from jinja2 import Environment` (needed for the new function's type hint; not previously imported).
- In `make_deconstructor_dict_data`, computed `header = generate_deconstructor_header_ru(jinja_env_header)` once before the loop (using the existing `jinja_env_header = get_jinja2_env("exporter/deconstructor")`, matching the RU template's location).
- Changed loop body to `data = DeconstructorData(i)` and `html_string = header + minify(template.render(data=data))`.

Registry: added `exporter/deconstructor/deconstructor_header_ru.jinja` to `russian_copies` (upstream counterpart `exporter/deconstructor/deconstructor_header.jinja`), matching the shape of the sibling `exporter/tpr/templates/tpr_headword_ru.jinja` entry (`upstream`/`sync_rule`/`local_changes`/`watch_for`). Per Hard rules, the pre-existing `deconstructor_exporter_ru.py` registry entry's `local_changes` text (which still mentions the now-removed `DeconstructorDataRu` subclass) was left untouched — out of the batch's authorized scope (only the ONE new jinja registry line was authorized).

Verify:
- `uv run python -c "import exporter.deconstructor.deconstructor_exporter_ru"` — PASS (no output/error).
- `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` — PASS (`registry.json is valid`).

## S5 — `exporter/goldendict/export_rpd.py`

**Status: DONE**

Upstream pattern mirrored (`git diff OLD NEW -- exporter/goldendict/export_epd.py`): (a) empty-db early return before the loop; (b) header rendered once via `EpdData(lookup_db[0], pth, jinja_env).header`, squashed once; (c) loop replaced with an inline `html_string` join (`epd_unpack`-derived) instead of constructing a per-entry `EpdData`, rendering `template.render(d={"header": header, "html_string": html_string})`.

`RpdData` branch taken: read `exporter/goldendict/data_classes_dps.py` (where `RpdData` actually lives, not a `rpd_data.py`). `RpdData(EpdData)` overrides only `self.epd_entries = lookup_entry.rpd_unpack` in `__init__` and re-runs the inherited `_generate_html_string`, which is the exact same `"<br>".join(f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}" for ... in self.epd_entries)` join as `EpdData`. This is the "simple join like `epd_unpack`" branch named in the recipe, so it was **inlined** using `lookup_entry.rpd_unpack` directly, exactly mirroring upstream's `EpdData`→inline transformation. `data_classes_dps.py` itself was read-only reference — not edited (out of this batch's scope; it is not one of the 4 authorized shadow files).

Edit applied to `exporter/goldendict/export_rpd.py`:
- Added `if not lookup_db: pr.yes(0); return epd_data_list, size_dict` right after `epd_data_list: list[DictEntry] = []`.
- Hoisted `header = RpdData(lookup_db[0], pth, jinja_env).header` and `header_squashed = squash_whitespaces(header)` once before the loop (still constructing one `RpdData` instance, matching upstream's own one-time `EpdData(...).header` construction for the header — not eliminating the class, just calling it once instead of per-row).
- Inside the loop, replaced `data = RpdData(lookup_entry, pth, jinja_env); html_rendered = template.render(d=data)` with an inline `html_string` join over `lookup_entry.rpd_unpack`, then `template.render(d={"header": header, "html_string": html_string})`.
- Replaced `header = data.header` / `squash_whitespaces(header)` uses with the hoisted `header_squashed`.
- Template `rpd_ru.jinja` unchanged — its `{{ d.header }}` / `{{ d.html_string }}` dot-access works identically against a plain dict (Jinja2 attribute lookup falls back to item lookup), matching upstream's own template (verified: `epd.jinja` uses the identical `{{ d.header }}`/`{{ d.html_string }}` pattern against the same dict-passing convention).

Verify:
- `uv run python -c "import exporter.goldendict.export_rpd"` — PASS (no output/error).

## S6 — `exporter/grammar_dict/grammar_dict_ru.py`

**Status: DONE**

Upstream pattern mirrored (`git diff OLD NEW -- exporter/grammar_dict/grammar_dict.py` + `exporter/grammar_dict/data_classes.py`): base `GrammarData.__init__` is now `(lookup_entry, header)`; new module-level `generate_grammar_header(jinja_env)`; exporter computes `header = generate_grammar_header(jinja_env)` once before the loop and constructs `GrammarData(lookup_entry, header)` per row (cache-miss row only).

Edit applied:
- Import changed to `from exporter.grammar_dict.data_classes import GrammarData, generate_grammar_header`.
- Added `header = generate_grammar_header(jinja_env)` once before the loop in `generate_html_from_lookup` (right after `template = jinja_env.get_template("grammar.jinja")`).
- Changed construction from `GrammarData_ru(lookup_entry, g.pth, jinja_env)` to `GrammarData_ru(lookup_entry, header)`.
- `GrammarData_ru` itself needed no `__init__` change — it only overrides `_process_grammar` (not `__init__`), so it inherits the new 2-arg base constructor automatically; Python's dynamic dispatch still calls the RU `_process_grammar` override from inside the base `__init__`.
- No `grammar_dict_header_ru.jinja` exists in the RU env (`exporter/grammar_dict/` has only `grammar_dict_header.jinja`) — confirmed by directory listing — so `generate_grammar_header(jinja_env)` resolves to the base English header template, matching the recipe's documented fallback branch.

Verify:
- `uv run python -c "import exporter.grammar_dict.grammar_dict_ru"` — PASS (no output/error).

## S7 — `exporter/kindle/kindle_exporter_ru.py`

**Status: DONE**

Upstream pattern mirrored (`git diff OLD NEW -- exporter/kindle/data_classes.py exporter/kindle/kindle_exporter.py`): base `KindleData` no longer mutates the ORM headword (`_make_html_friendly`/`_html_friendly` removed); instead a module-level `html_friendly(text)` and `_make_friendly(headword) -> dict[str, str]` (built from `_FRIENDLY_ATTRS`) precompute a `friendly` dict passed into `template.render(..., friendly=self.friendly)` for `ebook_grammar.jinja`/`ebook_example.jinja`. `kindle_exporter.py` also gained `if not isinstance(value, str): continue` in `save_abbreviations_xhtml_page`'s loop, and dropped the old in-module `html_friendly` (now imported from `data_classes`).

**Deviation from the literal dispatch text, documented per Iron Rule / stop-condition judgment:** the recipe's bullet (a) said `from exporter.kindle.data_classes import KindleData, html_friendly`, but `KindleData` is never instantiated anywhere in this RU file (the RU exporter uses its own independent function pipeline — `render_ebook_entry_ru`/`render_grammar_templ_ru`/`render_example_templ_ru` — not the `KindleData` class at all). Importing `KindleData` unused would fail `ruff` (F401) and adds nothing. Bullet (b) of the same recipe item, however, explicitly names the actual mechanism to use: `friendly = _make_friendly(i)`. `_make_friendly` is upstream's own private helper in `data_classes.py` (confirmed present per the dispatch's "Confirmed pulled signatures" section). I imported `_make_friendly` and `html_friendly` (not `KindleData`) — this is upstream's own exact solution for building the friendly dict, applied literally per bullet (b), not an invented alternative. Flagging this for the record; happy to be corrected in a follow-up review if `KindleData` was truly intended for some other purpose.

Edit applied:
- Import: `from exporter.kindle.data_classes import _make_friendly, html_friendly`.
- Deleted the local `html_friendly` function (was at lines 376-383).
- Deleted the ORM `setattr` mutation loop in `render_ebook_entry_ru` (was lines 198-216, including the `i.ru.ru_notes` mutation) and replaced it with:
  ```python
  friendly = _make_friendly(i)
  if i.ru and i.ru.ru_notes:
      friendly["ru_notes"] = html_friendly(i.ru.ru_notes)
  ```
- `render_grammar_templ_ru` and `render_example_templ_ru` gained a `friendly: dict[str, str]` parameter, passed through from the call sites in `render_ebook_entry_ru`, and pass `friendly=friendly` into their respective `template.render(...)` calls (mirroring upstream `KindleData._render_grammar_table`/`_render_examples`).
- `save_abbreviations_xhtml_page`'s loop gained `if not isinstance(value, str): continue` before the `value == ">"` check, matching upstream's exact addition.
- `render_ebook_entry_ru` already had no `pth` parameter — confirmed, no signature change needed (matches recipe bullet (d)).

**Exact `friendly` dict keys used** (for S8 parity): the 12 base keys from upstream `_FRIENDLY_ATTRS` — `root_base`, `construction`, `sanskrit`, `compound_type`, `phonetic`, `example_1`, `example_2`, `sutta_1`, `sutta_2`, `commentary`, `notes`, `cognate` — plus one RU-only extension key, `ru_notes` (populated only when `i.ru and i.ru.ru_notes` is truthy, mirroring the original mutation guard).

Verify:
- `uv run python -c "import exporter.kindle.kindle_exporter_ru"` — PASS (no output/error).
- `uv run pytest tests/test_template_syntax.py -v` — PASS, 178 passed.

## S8 — `ebook_ru_example.jinja`, `ebook_ru_grammar.jinja`

**Status: DONE** (paired with S7)

Upstream pattern mirrored (`git diff OLD NEW -- exporter/kindle/templates/ebook_example.jinja exporter/kindle/templates/ebook_grammar.jinja`): all 12 `_FRIENDLY_ATTRS` reads switched from `i.<attr>` to `friendly.<attr>`; non-friendly fields (`i.source_1`/`i.source_2`, `i.compound_construction`, `i.derivative`, etc.) stayed on `i.`.

Edits applied, keyed to the same 12 attrs + the RU-only `ru_notes` extension:
- `ebook_ru_example.jinja`: `i.example_1`/`i.example_2`/`i.sutta_1`/`i.sutta_2` → `friendly.example_1`/`friendly.example_2`/`friendly.sutta_1`/`friendly.sutta_2`. `i.source_1`/`i.source_2` left unchanged (not in `_FRIENDLY_ATTRS`).
- `ebook_ru_grammar.jinja`: `i.root_base`, `i.construction`, `i.phonetic`, `i.compound_type` (guard only — `i.compound_construction` on the same line stays `i.`), `i.commentary`, `i.notes`, `i.cognate`, `i.sanskrit` all switched to `friendly.*`. The RU-only `i.ru and i.ru.ru_notes` block (absent from the upstream template, a local addition) was switched to `friendly.ru_notes` for consistency with the `friendly` dict now populated by S7 — including the nested `"[пер. ИИ]" in friendly.ru_notes and friendly.notes` check and its inner `{{ friendly.notes }}` read, and the `{% elif friendly.notes %}` fallback branch. This key (`ru_notes`) is exactly what S7's `friendly` dict extension provides — confirmed matching.
- Non-friendly fields left untouched: `i.family_root`, `i.root_key`/`i.rt.*`, `i.derivative`/`i.suffix`, `i.compound_construction`, `i.antonym`, `i.synonym`, `i.variant`, `i.link`/`i.link_list`, `i.non_ia`.

Verify:
- `uv run pytest tests/test_template_syntax.py -v` — PASS, 178 passed (covers both files; jinja syntax loads cleanly).

## Post-batch verification (as required)

```
uv run python -c "import exporter.deconstructor.deconstructor_exporter_ru; import exporter.goldendict.export_rpd; import exporter.grammar_dict.grammar_dict_ru; import exporter.kindle.kindle_exporter_ru"
```
→ PASS, no output/error.

```
uv run ruff check exporter/deconstructor/deconstructor_exporter_ru.py exporter/goldendict/export_rpd.py exporter/grammar_dict/grammar_dict_ru.py exporter/kindle/kindle_exporter_ru.py
```
→ `All checks passed!`

```
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
```
→ `registry.json is valid`

```
uv run pytest tests/test_template_syntax.py -v
```
→ 178 passed.

## Files changed (this batch only)

- `exporter/deconstructor/deconstructor_exporter_ru.py`
- `exporter/goldendict/export_rpd.py`
- `exporter/grammar_dict/grammar_dict_ru.py`
- `exporter/kindle/kindle_exporter_ru.py`
- `exporter/kindle/ru_components/templates/ebook_ru_example.jinja`
- `exporter/kindle/ru_components/templates/ebook_ru_grammar.jinja`
- `kamma/upstream_sync/registry.json` (added `exporter/deconstructor/deconstructor_header_ru.jinja` to `russian_copies`)

All edits left unstaged (no `git add`/`commit`/`stash`/`restore` run). Other dirty paths visible in `git status` (S1-S3, D-items, etc.) belong to earlier batches (A/B) and were not touched.

## Deviations / blockers

- S7 bullet (a) literal-text deviation documented above (imported `_make_friendly` instead of unused `KindleData`) — not a workaround, uses upstream's own private helper exactly as bullet (b) specifies.
- No other blockers. No item required stopping.

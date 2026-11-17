# Localizing DPD into Other Languages — How the Russian Fork Does It

Written for people who want to build a DPD in another language (Hindi, Tamil, Sinhala, Chinese, Spanish, …).
Context: [dpd-db discussion #291](https://github.com/digitalpalidictionary/dpd-db/discussions/291).

Repository: [sasanarakkha/dpd-db-sbs](https://github.com/sasanarakkha/dpd-db-sbs), branch `sbs-ru`.
It is a fork of [digitalpalidictionary/dpd-db](https://github.com/digitalpalidictionary/dpd-db) and currently produces a complete Russian DPD (GoldenDict/MDict, Kindle/EPUB, web app, grammar dictionary, deconstructor, TPR, SuttaCentral data), plus SBS study-tool exports and experimental Tamil data.

Coverage on 2026-11-17 (live `dpd.db`):

| Data | Rows |
|---|---|
| DPD headwords | 89,789 |
| `russian` rows | 89,050 |
| — human-verified meaning (`ru_meaning`) | 24,052 |
| — AI draft only (`ru_meaning_raw`, no human meaning) | 64,921 |
| — literal meaning (`ru_meaning_lit`) | 7,159 |
| — notes (`ru_notes`), of which AI-translated | 2,188 / 758 |
| roots with Russian meaning | 753 / 753 |
| `tamil` rows (all AI) | 62,400 |

So roughly 27% of headwords are human-verified and almost everything else has a labelled AI draft.

---

## 1. Core principles

1. **Never touch upstream data; add beside it.** English DPD stays the single source. Each language lives in its own table keyed by `dpd_headwords.id`, so upstream updates never collide with translation work.
2. **Two tiers of trust, kept in separate columns.** A human-verified field and an AI draft field (`ru_meaning` vs `ru_meaning_raw`). AI output never overwrites human work, and the exporter always knows which is which.
3. **Visible fallback chain in every export.** Human → AI (labelled) → English (with a "translate this" link). Readers always get something, and always know how reliable it is.
4. **TSV is the durable store, the DB is rebuilt.** Translation tables are dumped to tracked TSVs and re-imported into a freshly built upstream DB. This is what makes the fork survive upstream rebuilds.
5. **AI generation is grounded, checked, and resumable.** The model receives the full DPD entry, not just a word; a second model pass judges the draft; rejected drafts loop back; every run is chunked and restartable.

These match the proposal in #291 (human entries take priority, AI as fallback, start with high-frequency words).

---

## 2. Database layout

All in `db/models.py` (a modified upstream file in this fork).

### 2.1 Per-language tables (1:1 with `DpdHeadword`)

```python
class Russian(Base):
    __tablename__ = "russian"
    id: Mapped[int] = mapped_column(ForeignKey("dpd_headwords.id"), primary_key=True)
    ru_meaning: Mapped[str]       # human-verified meaning
    ru_meaning_raw: Mapped[str]   # AI draft meaning
    ru_meaning_lit: Mapped[str]   # literal meaning
    ru_notes: Mapped[str]         # notes (AI ones prefixed "[пер. ИИ]")
    ru_cognate: Mapped[str]       # Russian cognates

class Tamil(Base):   # experimental, AI only
    id, ta_meaning

class Sinhala(Base): # schema exists, empty
    id, si_meaning, checked
```

Relationships on `DpdHeadword`: `.ru`, `.ta`, `.sbs` (`uselist=False`).

### 2.2 Translated columns added to existing upstream tables

| Table | Added columns | Content |
|---|---|---|
| `dpd_roots` | `root_ru_meaning`, `sanskrit_root_ru_meaning` | root meanings |
| `family_root`, `family_word`, `family_compound`, `family_idiom` | `html_ru`, `data_ru` | family tables rendered with Russian meanings |
| `family_set` | `set_ru`, `html_ru`, `data_ru` | set name + rendered tables |
| `lookup` | `rpd` (Russian→Pāḷi), `tpd` (Tamil→Pāḷi) | reverse dictionary, analogous to upstream `epd` |

Rule of thumb: **source data** (meanings) goes in the language table; **generated data** (family HTML, reverse lookup) goes in a `*_xx` column next to the upstream column it mirrors, written by a `*_ru.py` copy of the upstream generator.

### 2.3 Persistence: TSV round-trip

| Script | Role |
|---|---|
| `db/backup_tsv/backup_dps.py` | Dumps `russian`, `tamil`, `sbs`, Russian root meanings to `db/backup_tsv/russian.tsv`, `tamil.tsv`, `sbs.tsv`, `ru_roots.tsv` (tracked in git) |
| `scripts/build/db_rebuild_from_tsv_dps.py` | After the upstream `db_rebuild_from_tsv.py`, repopulates the local tables; checks duplicate ids and orphan rows (ids no longer in `dpd_headwords`) |

The release workflow (`.github/workflows/ru_release.yml`) does exactly this from scratch on CI: upstream rebuild → `db_rebuild_from_tsv_dps.py` → inflections → upstream families → `*_ru` families → `rpd_to_lookup.py` → Russian exporters.

**Orphan check matters:** upstream deletes and merges headwords. A translation keyed to a removed id must be reported, not silently dropped.

---

## 3. How the Russian exporter is built

### 3.1 The fallback chain (`tools/tools_for_ru_exporter.py`)

```text
ru_meaning exists      → <b>ru_meaning</b>; досл. ru_meaning_lit
else ru_meaning_raw    → [пер. ИИ] ru_meaning_raw      (link to feedback form)
else                   → [перевести] English meaning   (link to feedback form)
```

Variants of the same logic exist per output format: `make_ru_meaning` (GoldenDict HTML), `make_ru_meaning_simpl`, `make_ru_meaning_html`, `make_ru_meaning_for_ebook`, `make_short_ru_meaning` (first synonym, used in family tables). The feedback link is how reader corrections flow back into the human tier. `tools/degree_of_completion_ru.py` also greys out entries without a human meaning.

### 3.2 Three kinds of fields (matches Bodhirasa's list in #291)

| Kind | Examples | How it is handled here |
|---|---|---|
| **Translate** | meaning, literal meaning, notes, root meanings, help, thanks, bibliography | Stored per language; meanings by human + AI pipeline; static texts by hand in `shared_data/reference_ru/*.tsv` |
| **Substitute grammar terms** | grammar line, POS, inflection table labels, family headers | `ru_replace_abbreviations()` + `shared_data/reference_ru/abbreviations.tsv` (upstream file with added `ru_abbrev`, `ru_meaning` columns). Abbreviations are translated once, applied everywhere |
| **Keep / transliterate** | Pāḷi lemma, construction, examples, sutta refs | Kept in Roman script. `tools/translit_ru.py` only handles the reverse case (Cyrillic input in search) |

For a non-Latin-script language you will additionally want Pāḷi rendered in the native script; DPD already has transliteration via aksharamukha upstream.

### 3.3 Shadow copies (`kamma/upstream_sync/registry.json`)

Every upstream file that needed a Russian version was copied under a suffixed name and recorded in the registry with its upstream source, `sync_rule`, `local_changes` and `watch_for`. Current counts:

| Category | Count | Meaning |
|---|---|---|
| `russian_copies` | 32 | RU-only shadows of upstream files/folders |
| `dps_copies` | 6 | shared RU/SBS/Tamil shadows (e.g. `data_classes_dps.py`, backup/rebuild scripts, `tpd_to_lookup.py`) |
| `sbs_copies` | 5 | SBS-only shadows |
| `tamil_copies` | 1 | Tamil-only |
| `inspired_by_upstream` | 25 | local files modelled on upstream but not 1:1 |
| `modified_upstream_files` | 10 | upstream files edited in place (`db/models.py`, `pyproject.toml`, …) |
| `unique_paths` | 101 | fork-only files |

The Russian shadows, grouped:

- **DB generators:** `db/families/family_{root,word,compound,set,idiom}_ru.py`, `db/rpd/rpd_to_lookup.py` (copy of `epd_to_lookup.py`), `db/lookup/help_abbrev_add_to_lookup_ru.py`, `scripts/build/families_to_json_ru.py`.
- **Exporters:** GoldenDict (`exporter/goldendict/main_ru.py`, `export_dpd_ru.py`, `export_roots_ru.py`, `export_rpd.py`, `export_help_ru.py`, `export_variant_spelling_ru.py`, `ru_components/templates|javascript`), Kindle/EPUB (`kindle_exporter_ru.py`, `ru_components/{templates,epub,cover}`), grammar dictionary, deconstructor, TPR, TBW, SuttaCentral, web app (`main_ru.py`, `data_classes_ru.py`, `toolkit_ru.py`, `preloads_ru.py`, `ru_templates/`).
- **Tools:** `tools/paths_ru.py`, `tools/version_ru.py`, `tools/degree_of_completion_ru.py`, `tools/ru_spelling.py`, `tools/translit_ru.py`.
- **Reference data:** `shared_data/reference_ru/`, `shared_data/rus/`.
- **Release:** `scripts/bash/make_ru_dpd.sh`, `scripts/rus_exporter/set_config.py` (config profiles: `release_rus`, `local_rus`, `release_full_ru`, …), `.github/workflows/ru_release*.yml`.

Conventions that kept this maintainable:

- **Naming tiers:** exact upstream name = untouched copy; `_ru` / `_sbs` / `_ta` suffix = single-locale shadow; `_dps` = shared between locales. HTML ids/CSS classes/JS names prefixed (`ru_`, `rudata_`) so RU and EN can coexist in one GoldenDict install.
- **Surgical layering:** a shadow keeps upstream logic line-for-line and only layers the language on top, so upstream diffs can be ported mechanically.
- **Registry as gate:** `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` must pass; every shadow lists what to watch for when upstream changes.
- **Sync protocol:** `kamma/upstream_sync/guide.md` (run via the `update-upstream` skill) diffs upstream changes against every registered shadow and ports them.

**Honest cost:** ~40 shadow files must be re-checked on every upstream sync. This is the biggest maintenance burden of the approach — see §6.

---

## 4. Producing the data

### 4.1 Human tier

- Translators edit in the DPD GUI (`gui2/`), extended by `gui2/dps_*.py` (Russian fields, Russian spell checker `tools/ru_spelling.py` with a custom word list, AI suggestion button via `gui2/dps_ai_service.py`). The human writes or approves `ru_meaning`; the AI draft is only a suggestion.
- Reader feedback (Google Form links on `[пер. ИИ]` / `[перевести]`) is processed with `gui2/dps_process_corrections.py` / `dps_process_additions.py`.
- Prioritize by frequency: pool queries order by `ebt_count` so the most common words come first.

### 4.2 AI tier — the `/translate` skill

Entry: `.claude/commands/translate.md` (the `/translate` command) points to **`kamma/translate/pipeline.md`**, a menu-driven procedure an agent follows. State lives next to it: `state.json` (totals, last op), `log.md` (one line per session), `rejects.json` (reject memory).

Scripts in `kamma/translate/scripts/`:

| Script | Job |
|---|---|
| `ai_generate_translation.py` | Generate (`-lang ru\|ta`, `-mode meaning\|lit\|note`), cleanup (`-remove`), batch-API JSONL export |
| `ai_check_russian_meanings.py` / `ai_meaning_checker.py` | AI semantic checker, 6 column modes + `*_list` variants for just-generated ids, resumable snapshots |
| `ai_translation_check.py` | Mechanical check: leftover Latin script, length outliers |
| `batch_runner.py` | Chunked (50), resumable wrapper; `--status` prints all pool counts |
| `synonym_audit.py` | Strip duplicate / near-identical synonyms (report → reviewed TSV → apply) |
| `model_benchmark.py` | Compare candidate models on fixed samples before changing the chain |
| `offpeak.py`, `rejects.py`, `session_log.py`, `ids_file.py` | Guards and bookkeeping |

**Menu (operations):**

1. Translate new words → writes `ru_meaning_raw` (never `ru_meaning`).
2. Verify the latest generation → mechanical check, then AI check; `MISMATCH` clears the draft so it re-enters op 1 (the retranslate loop). `PARTIAL_MATCH` is kept and listed.
3. Check existing columns (human ones are report-only; AI ones are cleared on mismatch).
4. Synonym audit.
5. Remove empty / contaminated rows.
6. Re-ground old drafts (regenerate with same-root context).

**What the prompt contains** (`tools/ai_related.py`, `create_translation_prompt`):

- lemma, grammar (abbreviations expanded), English meaning (`meaning_1`, fallback `meaning_2`), first example sentence;
- a per-POS format example (`shared_data/rus/ru_translation_examples.csv`);
- **same-root grounding:** verified Russian translations of other words from the same root, plus the root's Russian meaning — keeps terminology consistent across a family;
- if the word was rejected before, the checker's reason;
- rules: ≤3 *distinct* senses separated by `;`, translate bracketed glosses, lowercase, no leftover English, one line, no commentary.

**Quality controls that turned out to matter:**

- Checker verdicts are three-way (`MATCH` / `PARTIAL_MATCH` / `MISMATCH`); only `MISMATCH` deletes, and an unparseable reply never deletes.
- Reject memory: after 2 rejections a word is parked instead of looping forever.
- Snapshots of checked ids auto-invalidate when the English source changes (upstream edits a meaning → recheck).
- Destructive ops are dry-run first, require confirmation and a fresh `backup_dps.py`.
- Never re-run an LLM to fix formatting; use local text processing.

**Cost controls:** model chain in `tools/ai_models.json` (`default_models`: DeepSeek Flash direct, OpenRouter Qwen fallback; `grounded_models` for re-grounding), chosen by `model_benchmark.py`. An off-peak guard refuses runs in DeepSeek's full-price hours. Chunks of 50 commit as they go, so interruption loses nothing.

### 4.3 Tamil as the second-language test case

Tamil reuses the same generator via `LANG_CONFIG` in `ai_generate_translation.py`:

```python
LANG_CONFIG = {
    "ru": {"orm_model": Russian, "rel_name": "ru", "field_name": "ru_meaning_raw",
           "prompt_builder": generate_messages_for_meaning},
    "ta": {"orm_model": Tamil,   "rel_name": "ta", "field_name": "ta_meaning",
           "prompt_builder": generate_messages_for_meaning_ta},
}
```

It shows what is cheap to add (generation: a table, a prompt builder, a format-example file) and what is not: Tamil has no semantic checker, no human/AI split (one column), no grounding, and no dedicated exporter (only `show_ta_data` in the combined GoldenDict view and `tpd` reverse lookup). That gap is exactly the work a new language needs.

---

## 5. Recipe for a new language (using this fork as a template)

Minimum viable (AI-only draft, combined view):

1. Add a table `xx` with `id`, `xx_meaning`, `xx_meaning_raw` (keep the human/AI split from day one).
2. Add it to `backup_dps.py` and `db_rebuild_from_tsv_dps.py`.
3. Add an entry to `LANG_CONFIG` + a prompt builder in `tools/ai_related.py` + `shared_data/xx/xx_translation_examples.csv`.
4. Generate for high-frequency words first (pool is ordered by `ebt_count`).
5. Run the mechanical check; adapt `ai_translation_check.py`'s script detection to your alphabet.

Full dictionary (what Russian has):

6. Translate `abbreviations.tsv` (add `xx_abbrev`, `xx_meaning`) and the help/thanks/bibliography TSVs.
7. Port the semantic checker and reject memory for your language.
8. Add `*_xx` columns for families/sets and copy the family generators; add a reverse lookup column (`xpd`) from `epd_to_lookup.py`.
9. Copy the exporters you need (GoldenDict first, then web/Kindle), with prefixed ids and templates.
10. Register every shadow in a registry and set up an upstream-sync routine.
11. Build human review into the GUI and add a reader feedback link to every AI-labelled entry.

---

## 6. Recommendations and caveats for a unified multi-language system

These are lessons from Russian, not features that exist today.

1. **Don't repeat per-language shadow copies.** Steps 8–10 above multiply by the number of languages. For an upstream-supported system, a generic structure would scale better, e.g. one table `translation(id, lang, field, value, source, status)` where `source ∈ {human, ai}` and `status ∈ {draft, checked, verified}`, and exporters parameterised by `lang` instead of copied. The Russian fork predates this idea; migrating it would be a separate project.
2. **Separate human and AI tiers in the schema, not by text markers.** The Russian notes column uses a `[пер. ИИ]` prefix to mark AI text; meanings use two columns. Columns are easier to query and safer.
3. **Grammar terms first.** A translated abbreviations table gives the biggest visible improvement per hour of human work, because grammar lines, inflection tables and family headers all reuse it.
4. **Ground the AI in already-verified translations** (same root, same POS). This was the single largest quality gain in the Russian pipeline.
5. **Always run a second-pass judge**, and make clearing conservative (three-way verdict, parking after repeated rejects).
6. **Key everything by headword `id` and check orphans** on every rebuild; upstream ids do get removed.
7. **Plan the sync burden up front.** A lighter alternative is a read-only overlay with a sidecar DB and English fallback, as in the Spanish fork [jorgecaa/dpd-db-es](https://github.com/jorgecaa/dpd-db-es) — fewer copied files, at the cost of not translating the generated parts (families, reverse lookup, grammar).

---

## 7. Where to look

| Topic | Path |
|---|---|
| Models | `db/models.py` (`Russian`, `Tamil`, `Sinhala`, `*_ru` columns) |
| Shadow registry + sync guide | `kamma/upstream_sync/registry.json`, `kamma/upstream_sync/guide.md` |
| AI pipeline procedure | `kamma/translate/pipeline.md` |
| AI scripts | `kamma/translate/scripts/` |
| Prompts | `tools/ai_related.py` |
| Model chain | `tools/ai_models.json` |
| Fallback rendering | `tools/tools_for_ru_exporter.py` |
| TSV backup / rebuild | `db/backup_tsv/backup_dps.py`, `scripts/build/db_rebuild_from_tsv_dps.py` |
| Translated reference data | `shared_data/reference_ru/`, `shared_data/rus/` |
| Build / release | `scripts/bash/make_ru_dpd.sh`, `scripts/rus_exporter/set_config.py`, `.github/workflows/ru_release.yml` |
| Russian user docs | `docs_rus/` |

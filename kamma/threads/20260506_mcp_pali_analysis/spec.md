# Spec: MCP Pāḷi Analysis Pipeline

## Goal
Populate `SBS.dhp_example` for Dhammapada headwords using AI-analyzed word-by-word grammar per verse.

## 3-Script Pipeline

### 1. `exporter/mcp/book_to_verses.py`
Extracts verses from CST, deduplicates, outputs to `exporter/mcp/input/{book}.json`
- Input: `--book kn2`
- Output: list of `{num, vagga, text}` objects

### 2. `exporter/mcp/ai_batch_translate.py`
Batch processes verses through AI analysis, resumable.
- Input: `exporter/mcp/input/{book}.json`
- Calls: `translate_sentence()` from `ai_pali_translate.py`
- Output: `exporter/mcp/output/{book}_analysis.json` with full analysis per verse

### 3. `scripts/change_in_db/fill_dhp_examples.py`
Reads analysis output, fills `SBS.dhp_example` for all headword IDs with bolded verse text.
- For each verse: iterate all tokens → all IDs (including nested components via `collect_all_ids()`)
- Bold component in verse text using `bold_component_in_token()`
- Create/update `SBS(id)` row with `dhp_example`

## Key Functions

**`translate_core.py`** (shared utilities):
- `build_system_prompt(analysis)` — system prompt for AI
- `merge_ai_selections(analysis_data, ai_response)` — merge AI scores into analysis
- `format_markdown_table(enriched_analysis)` — pretty-print

**`fill_dhp_examples.py`** (critical):
- `collect_all_ids(option, word_in_verse)` — **recursive**, yields all IDs (includes nested components)
- `find_token_in_apos_verse(word, verse_text)` — finds apostrophe form of word in verse
- `bold_component_in_token(apos_token, component_pali)` — bolds component left/right of apostrophe
- `bold_word_in_verse(verse_text, word, bolded_word)` — replaces word in verse with bolded version

## Important Details

**Apostrophes**: CST XML has none (e.g., `subhānupassiṃ`). Use `DpdHeadword.example_1` as source of truth (has apostrophes via DPD editors). Strip bold tags first: `re.sub(r"</?b>", "", example_1)`.

**Bolding sandhi**: `<b>subh</b>'ānupassiṃ` (LEFT) vs `subh'<b>ānupassiṃ</b>` (RIGHT). Handled by `bold_component_in_token()`.

**Sub-components**: Analysis nests components. Only top-level has AI scores; sub-components have `ai_score: 0`. `collect_all_ids()` recurses all levels.

## API Constraints
- `ai_pali_translate.py` uses `exporter/mcp.analyzer.analyze_sentence()` (existing, not modified)
- `translate_sentence()` accepts `ai_manager` parameter (for batch mode)
- All code: ruff check/format clean, pyright strict

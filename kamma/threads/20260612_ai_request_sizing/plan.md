# Plan: JSON-size-driven AI request sizing for passage analysis

See `spec.md` in this thread for full context and root-cause analysis.

## Architecture Decisions

- **Transport over chunking as the real fix.** The 772 KB failure was an argv byte
  limit, not a model limit. `agy --print -` reads the prompt from stdin (verified
  empirically), so switching transport removes the ceiling and fixes the reported
  bug by itself. Phases 2–3 are robustness, not the fix.
- **The existing splitter is already JSON-size-driven** (decision + packing by
  compact-JSON length, cut at sentence boundaries). Keep it; only raise the
  threshold. Its sole defect — a lone sentence over the threshold returned
  unsplit — is handled by the Phase 3 fallback.
- **Char count of compact JSON as the size proxy.** No tokenizer dependency.
  Threshold = `MAX_FIRST_CONTEXT_CHARS = 900_000` (~300–360k tokens, deep headroom
  in a 1M-token window). Single named constant.
- **Sentence-boundary chunks translate themselves; concatenation is fine.** A
  whole-sentence translation is only incoherent when a sentence is split mid-way.
  So no grounded-translation step on the normal path.
- **Option C (grounded translation) = dormant fallback only**, for a single
  sentence whose JSON alone exceeds the threshold. Reuses `format_markdown_table`
  for the chosen-sense context (no circular dependency — it needs no translation).
  Not designing for small-window fallback providers.

## Phase 1 — Transport fix (stdin) — the actual bug fix

Goal: `antigravity_cli` sends the prompt via stdin; the 700k argv ceiling is gone;
DHP12 succeeds on the first provider as a single un-chunked call.

- [ ] 1.1 Switch `run_antigravity_print` (`tools/antigravity_cli_models.py`) to pass
  the prompt via stdin: command uses `--print -` (drop the inline prompt arg), set
  `input=prompt`, and remove `stdin=subprocess.DEVNULL`. Keep `--sandbox`,
  `--model`, `--print-timeout`, isolated cwd, and the timeout contract.
  → verify: update + run `uv run pytest tests/tools/test_antigravity_cli_models.py -v`;
    assertions confirm the prompt is NOT in `command`, is passed via `input=`, and
    the sandbox/model/print-timeout contract is preserved. Expect all pass.
- [ ] 1.2 In `tools/ai_antigravity_cli.py`, replace the
  `MAX_ARGV_PROMPT_BYTES = 700_000` pre-send check in `generate_content` with a high
  sanity ceiling (`MAX_PROMPT_BYTES = 4_000_000`) and update the error message (no
  longer "argv transport").
  → verify: update + run `uv run pytest tests/tools/test_ai_antigravity_cli.py -v`;
    update `test_prompt_size_budget_is_safe_margin` and the oversized-prompt test to
    the new constant/value; a 772 KB prompt is NOT rejected pre-send. Expect all pass.
- [ ] 1.3 Phase verification.
  → verify: run `up exporter/analysis/study_passage.py --debug` on DHP12; confirm
    `antigravity_cli` SUCCEEDS on the first attempt, no "prompt too large" error, no
    size-driven DeepSeek fallback, and `chunk_requests` is empty (single call). Run
    `uv run ruff check --fix`, `ruff format`, `pyright`, `pyrefly --min-severity warn`
    on each changed file (one command per file); all pass.

## Phase 2 — Raise threshold, confirm JSON-size sentence chunking

Goal: chunking triggers by JSON size at model-capacity scale; normal passages stay
one call; large multi-sentence passages split at sentence boundaries.

- [ ] 2.1 Set `MAX_FIRST_CONTEXT_CHARS = 900_000` in `exporter/analysis/prompts.py`
  with a comment explaining the JSON-size / token-budget rationale (replaces the
  250,000 argv-era value).
  → verify: `uv run python -c "from exporter.analysis.prompts import MAX_FIRST_CONTEXT_CHARS; assert MAX_FIRST_CONTEXT_CHARS == 900_000"` exits 0.
- [ ] 2.2 Add direct unit tests for `_split_into_sentence_chunks` in
  `tests/exporter/analysis/test_translate_core.py` (none exist today): (a) analysis
  with compact JSON ≤ a small injected threshold → one chunk; (b) a multi-sentence
  analysis exceeding the threshold → splits at sentence boundaries, each chunk
  ≤ threshold, total words preserved and in order.
  → verify: `uv run pytest tests/exporter/analysis/test_translate_core.py -v`, all pass.
- [ ] 2.3 Phase verification.
  → verify: run `up exporter/analysis/study_passage.py --debug` on DHP12 (single
    chunk) and on a long multi-paragraph passage (e.g. an AN sutta, "analyze ALL");
    confirm chunk behavior tracks JSON size and the report reads coherently. Run
    ruff/pyright/pyrefly on the changed file; all pass.

## Phase 3 — Option C: grounded translation as dormant fallback

Goal: a single sentence whose JSON alone exceeds the threshold is handled by
word-level scoring + one grounded whole-sentence translation from the chosen
senses. Default-dormant; not hit by normal passages.

- [ ] 3.1 Add `_build_grounded_translation_prompt(sentence, word_table_md)` in
  `exporter/analysis/prompts.py`: sentence + the chosen-sense Markdown word table →
  asks only for `translation` + `literal_translation`, grounded in those senses, no
  full candidate JSON.
  → verify: unit test asserts the prompt contains the sentence and the word-table
    text and requests only translation/literal_translation. `uv run pytest
    tests/exporter/analysis/test_translate_core.py -v` passes.
- [ ] 3.2 In `translate_core.py`, detect the lone-oversize-sentence case inside the
  splitter (the `len(sentences) < 2` / single-sentence-over-threshold branch) and
  word-split that sentence's analysis for scoring only. After scores are merged and
  `merge_ai_selections` has produced `merged`, when this fallback was used: render
  `format_markdown_table(merged["analysis"])`, issue one
  `_build_grounded_translation_prompt` request, and overwrite
  `translation`/`literal_translation`; on AI failure keep the concatenated chunk
  translations.
  → verify: unit test (mocked `AIManager`) proves: a single sentence whose JSON
    exceeds an injected threshold triggers word-level scoring AND one grounded
    translation call whose result replaces the concatenation; a normal passage
    (≤ threshold, or multi-sentence) does NOT issue the grounded call. `uv run
    pytest tests/exporter/analysis/test_translate_core.py -v` passes.
- [ ] 3.3 Phase verification.
  → verify: with a temporarily lowered threshold (test/fixture, not committed),
    confirm end-to-end that a single long sentence routes through the fallback and
    the final prose translation matches the word table. Run ruff/pyright/pyrefly on
    the changed files; all pass.

## Phase 4 — Docs and final validation

- [ ] 4.1 Update `exporter/analysis/README.md`: transport is now stdin (remove/correct
  the 700k argv claim); chunking is JSON-size-driven at sentence boundaries with a
  word-level grounded-translation fallback for lone oversize sentences.
  → verify: `grep -n "argv\|700\|sentence-level chunks" exporter/analysis/README.md`
    shows the stale claims are gone/corrected.
- [ ] 4.2 Full quality-gate sweep on every changed file (one command per file, never
  batched, never on `.`): ruff check --fix, ruff format, pyright, pyrefly
  --min-severity warn, and the targeted pytest files.
  → verify: every command exits clean; `git status --short` shows no stray
    root-level scratch files (Clean Root Folder Protocol).

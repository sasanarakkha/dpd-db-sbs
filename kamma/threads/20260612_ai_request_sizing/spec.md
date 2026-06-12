# Spec: JSON-size-driven AI request sizing for passage analysis

## Overview
The Stage 1 passage analyzer (`exporter/analysis/study_passage.py` →
`translate_core.translate_sentence`) sends a per-word dictionary "analysis" JSON
to an AI model for word-sense disambiguation and translation. For DHP12 — a
9-word verse — the prompt reached 772,102 bytes and the `antigravity_cli`
provider rejected it with `prompt too large for argv transport
(772102 bytes > 700000)`. The run only succeeded by falling back to DeepSeek.

Root cause, confirmed empirically: **this is a transport limit, not a model
limit.**

- `agy` receives the prompt as a command-line argument (`--print "<prompt>"`,
  `tools/antigravity_cli_models.py:40-49`, `stdin=subprocess.DEVNULL`). The OS
  `ARG_MAX` on the dev machine is 1,048,576 bytes, and
  `MAX_ARGV_PROMPT_BYTES = 700_000` (`tools/ai_antigravity_cli.py:21`) is a
  hand-picked safety margin below it.
- Gemini 3.5 Flash itself accepts ~1M tokens (~3M chars of dense JSON). The
  772 KB prompt is ~180k–245k tokens — roughly a quarter of the window. The model
  was never the bottleneck.
- **Verified:** `agy --print -` reads the prompt from **stdin** (tested: it
  computed `17 + 25 → 42` from a piped prompt). Switching the transport to stdin
  removes the argv ceiling entirely.

A secondary, pre-existing defect: the chunker
(`_split_into_sentence_chunks`, `translate_core.py:220`) already *decides* whether
to split by JSON payload size and already *packs* by JSON size at sentence
boundaries — that part is correct. Its only flaw is that a **single sentence**
whose JSON exceeds the threshold cannot be split (`len(sentences) < 2` returns the
whole thing unsplit), so an oversized lone verse is sent whole.

## What it should do
1. **Transport fix (primary, solves the bug):** `antigravity_cli` feeds the prompt
   to `agy` via **stdin** (`--print -`, `input=prompt`) instead of argv. The 700k
   argv ceiling is removed; a 772 KB prompt for a single verse goes through in one
   request. With the raised threshold (below), DHP12 is a single, un-chunked call.
2. **Raise the chunk threshold to model capacity:** `MAX_FIRST_CONTEXT_CHARS` goes
   from the artificial argv-derived 250,000 to **900,000** compact-JSON chars
   (~300–360k tokens; deep headroom inside a 1M-token window). Chunking then
   triggers only when the JSON genuinely approaches model limits.
3. **Keep JSON-size, sentence-boundary chunking:** the existing splitter is
   retained — decision and packing by JSON size, cut at sentence boundaries (a
   semantic unit). Each sentence-chunk translates itself coherently and the
   results are concatenated, as today. No change to the multi-sentence path beyond
   the raised threshold.
4. **Option C — grounded translation as a dormant fallback only:** for the rare
   case of a **single sentence whose analysis JSON alone exceeds the threshold**
   (cannot be split at a sentence boundary), split that sentence at **word**
   granularity for *scoring only*, then issue one final **grounded whole-sentence
   translation** request built from the **chosen senses** (the resolved analysis,
   rendered via the existing `format_markdown_table`), so the prose translation is
   grounded in — and consistent with — the word table rather than a free
   hallucination. On failure, fall back to the concatenated chunk translations.
   This path is **not exercised by normal passages** (DHP12 and typical suttas
   stay well under 900k); it exists purely as a safety net.

## Design decisions (locked)
- **Sizing metric:** byte/char length of the compact
  `json.dumps(analysis, separators=(",",":"))`. No tokenizer dependency; char
  length tracks both prompt size and the number of dictionary "possibilities."
- **Threshold:** `MAX_FIRST_CONTEXT_CHARS = 900_000` chars. Single named constant,
  easy to tune.
- **Not designing for small-window fallback providers.** We assume the answering
  provider has a ~1M-token window (Gemini / gpt-4.1-nano / llama-4-scout). The
  threshold is NOT sized to the smallest fallback. If a small-window fallback ever
  rejects an oversized chunk, that is acceptable and out of scope.
- **Chunk decision = JSON size; chunk boundary = sentence; word-level split =
  last-resort fallback** feeding Option C.
- **Grounded translation context = the rendered Markdown word table**
  (`format_markdown_table(merged["analysis"])`), which needs no translation in
  hand (verified — no circular dependency) and reuses existing rendering code.

## Affected files
- `tools/antigravity_cli_models.py` — `run_antigravity_print`: prompt via stdin.
- `tools/ai_antigravity_cli.py` — remove/raise `MAX_ARGV_PROMPT_BYTES`; update the
  pre-send size check + message in `generate_content` (high sanity ceiling, not
  700k argv).
- `exporter/analysis/prompts.py` — `MAX_FIRST_CONTEXT_CHARS = 900_000` (+ rationale
  comment); add `_build_grounded_translation_prompt` (Phase 3, fallback only).
- `exporter/analysis/translate_core.py` — keep `_split_into_sentence_chunks`
  (JSON-size, sentence-boundary); add the lone-oversize-sentence detection +
  word-level fallback + grounded-translation wiring (Phase 3).
- `exporter/analysis/rendering.py` — reuse `format_markdown_table` (no change).
- Tests: `tests/tools/test_antigravity_cli_models.py`,
  `tests/tools/test_ai_antigravity_cli.py`,
  `tests/exporter/analysis/test_translate_core.py`.
- `exporter/analysis/README.md` — correct transport (stdin, not argv) and chunking
  notes.

## How we'll know it's done
- `up exporter/analysis/study_passage.py --debug` on **DHP12** completes with
  `antigravity_cli` succeeding on the **first** attempt — no "prompt too large for
  argv transport" error, no size-driven DeepSeek fallback — as a **single
  un-chunked call**.
- A unit test proves `run_antigravity_print` passes the prompt via `input=`
  (stdin), not in the argv `command`, and a >700 KB prompt is not rejected
  pre-send.
- A unit test proves the splitter keeps DHP12-scale JSON (<900k) as one chunk, and
  splits a large multi-sentence analysis at sentence boundaries by JSON size.
- A unit test proves the Option-C fallback fires only for a single sentence whose
  JSON exceeds the threshold, issues the grounded translation from the chosen
  senses, and falls back to concatenation on failure.
- All quality gates pass (ruff, pyright, pyrefly, targeted pytest) on each changed
  file.

## What's not included
- No per-model tokenizer / true subword token counting.
- No changes to HTTP providers (DeepSeek/OpenRouter/Claude/Gemini API).
- No threshold tuning for small-window fallback providers.
- No grounded-translation step on the common (single-call / multi-sentence) path —
  Option C is fallback-only and dormant by default.
- No changes to scoring logic, prompt content, or report rendering beyond reusing
  `format_markdown_table` for the fallback grounding context.

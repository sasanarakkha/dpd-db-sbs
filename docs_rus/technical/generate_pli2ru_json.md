# Generating pli2ru_dpd.json for SuttaCentral

`pli2ru_dpd.json` is a JSON export of the Russian DPD translations in the format
expected by SuttaCentral's simple dictionary API. Each entry maps an inflected
Pāḷi form (as it appears in SC sutta texts) to a list of Russian definition
strings.

## Output format

```json
[
  {
    "entry": "dhammaṁ",
    "definition": [
      "dhammo: сущ. <b>учение; закон; принцип</b> [dhamma]",
      "dhamma + ṁ"
    ]
  }
]
```

Each `definition` item is either:

- A headword definition: `<lemma>: <pos_ru>. <b>meaning</b>[; досл. <literal>] [<construction>]`
- A deconstruction line: `part + part + ...` (compound split, language-neutral)

## Prerequisites

### 1. Python environment

```bash
# Install dependencies with uv (used project-wide)
uv sync
```

### 2. SC bilara data submodule

The exporter builds the word set by reading actual SC sutta text files. These
live in the `resources/sc-data` submodule, which is **not initialized by
default**.

```bash
git submodule update --init resources/sc-data
```

This is a large download (~1 GB). After initialization, verify the text files
are present:

```bash
ls resources/sc-data/sc_bilara_data/root/pli/ms/sutta/dn/
```

### 3. Enable the exporter in config.ini

The exporter is gated by a flag in `config.ini` (same gate used by all TBW/SC
exporters). Set it to `yes` before running:

```ini
[exporter]
make_tbw = yes
```

Remember to revert it to `no` afterwards if you don't want it running as part
of the full build pipeline.

## Running the exporter

```bash
uv run python -m exporter.sutta_central.sutta_central_exporter_ru
```

Output is written to:

```bash
resources/sc-data/dictionaries/simple/ru/pli2ru_dpd.json
```

### Optional flags

| Flag | Effect |
|---|---|
| `--with-ai` | Include AI-translated entries (`ru_meaning_raw`, marked `[пер. ИИ]`) |
| `--with-eng-fallback` | Include headwords with no Russian translation at all (falls back to English meaning) |

Both flags are **disabled by default** to comply with SuttaCentral's AI-free
content policy. Use them only when generating for non-SC targets.

Example for a local/internal build with full coverage:

```bash
uv run python -m exporter.sutta_central.sutta_central_exporter_ru --with-ai --with-eng-fallback
```

## Verifying the output

```bash
# Entry count and shape
python -c "
import json
d = json.load(open('resources/sc-data/dictionaries/simple/ru/pli2ru_dpd.json'))
print('entries:', len(d))
print('keys:', list(d[0].keys()))
print('sample:', d[0])
"

# Confirm no AI leakage in default mode
grep -c "пер. ИИ" resources/sc-data/dictionaries/simple/ru/pli2ru_dpd.json
# Expected: 0
```

The entry count will be smaller than `pli2en_dpd.json` because untranslated
headwords are omitted. Entries that have only a deconstructor line (no
translated headword) are still included — the Pāḷi compound split is
language-neutral and useful for readers.

## Limitations

### SC bilara data not in repo

The word set is derived from actual SC sutta text files, which live in a Git
submodule (`resources/sc-data`) that is not initialized by default. Without it,
the exporter runs but produces an empty JSON array. See [Prerequisites](#2-sc-bilara-data-submodule).

### Partial Russian translation coverage

As of the current DB, roughly 25,000 headwords have no Russian translation row
at all, and ~38,700 have only an AI-generated raw translation (`ru_meaning_raw`).
In default (SC-safe) mode these are all omitted. The resulting JSON covers only
headwords with a human-reviewed `ru_meaning`. Coverage will improve as
translation work continues.

### `ṃ` → `ṁ` normalisation

SuttaCentral uses `ṁ` (m with dot above) for the *niggahīta*, while the DPD
database uses `ṃ` (m with dot below). The exporter normalises all output
automatically via the `flip()` method, matching the English exporter's
behaviour.

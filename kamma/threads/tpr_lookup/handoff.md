# Handoff: TBW/FDG Pali Lookup — Headword Display

**Date:** 2026-06-06  
**Branch:** sbs-ru  
**Status:** Decision pending — no code changed yet

---

## What We Were Discussing

The TBW ("A Treasury of Dhamma") Pali word-lookup popup currently (in the online deployed version) shows meanings **without** the headword. For example, hovering over *vācāhi* shows:

```
vācāhi
adj. talking; speaking; of speech [√vac + *ā + a]
fem. speech; words; statement; talk [√vac + *ā]
fem. line of verse; sentence [√vac + *ā]
```

The user wants each meaning line to show the Pali headword (lemma) it belongs to:

```
vācāhi
vācā adj. talking; speaking; of speech [√vac + *ā + a]
vācā fem. speech; words; statement; talk [√vac + *ā]
vācā fem. line of verse; sentence [√vac + *ā]
```

---

## Architecture Overview

### Data pipeline (`exporter/tbw/tbw_exporter.py`)

Generates three JS data files for both `resources/bw2/js/` and `resources/fdg_dpd/assets/standalone-dpd/`:

| File | JS variable | Content |
|---|---|---|
| `dpd_i2h.js` | `dpd_i2h` | inflected form → list of `lemma_1` headwords |
| `dpd_ebts.js` | `dpd_ebts` | `lemma_1` → `"pos. meaning [construction]"` |
| `dpd_deconstructor.js` | `dpd_deconstructor` | compound word → split breakdown |

Key function: `generate_dpd_ebt_dict()` at line 149. Currently builds the value as:

```python
string = f"{i.pos}. "
string += i.meaning_combo_html
if i.construction:
    string += f" [{i.construction_summary}]"
g.dpd_dict[i.lemma_1] = string
```

### Rendering (`resources/bw2/js/pali-lookup-standalone.js`, line 114)

```js
out += '<li>' + headword + '. ' + dpd_ebts[headword] + '</li>'
```

Where `headword` is `lemma_1` (e.g. `"vācā 1"` — **includes number suffix**).

### CSS popup (`resources/bw2/css/css.css`, lines 1208–1250)

Pure CSS hover tooltip. Light: `background: #fff3d6`, `border: darkorchid`. Dark mode variant exists.

---

## Key Finding

The **submodule** (`resources/bw2`) was recently updated and line 114 in `pali-lookup-standalone.js` **already prepends the headword** (`headword + '. '`). The **online deployed website** is running an older version of this JS that does not have this line — hence no headword appears online currently.

### Model fields available on `DpdHeadword`

- `lemma_1` → `"vācā 1"` (with number suffix, used as dict key)
- `lemma_clean` → `"vācā"` (strips number via `re.sub(r" \d.*$", "", self.lemma_1)`, defined at model line 1173)

---

## Decision Point (unresolved)

Two format options remain:

### Option A — Deploy updated submodule as-is (no code change)
- The updated bw2 JS already adds `headword + '. '`
- Result: `"vācā 1. fem. speech; ..."` — headword shown **with** number suffix
- Zero code change required in dpd-db

### Option B — Clean headword without number (two-file change)
- `tbw_exporter.py` `generate_dpd_ebt_dict()`: prepend `i.lemma_clean` inside the value string
- bw2 JS line 114: remove `headword + '. '`, use only `dpd_ebts[headword]`
- Result: `"vācā fem. speech; ..."` — headword shown **without** number suffix
- Requires touching both dpd-db exporter and bw2 submodule

### Why Option B requires both files
If you add `lemma_clean` to the data value AND the JS still prepends `headword + '. '`, the output is doubled:
`"vācā 1. vācā fem. ..."` — broken.

---

## Files to Change (if Option B)

1. `exporter/tbw/tbw_exporter.py` — `generate_dpd_ebt_dict()`, line ~155
2. `resources/bw2/js/pali-lookup-standalone.js` — line 114 (submodule)
   - Same fix needed in `resources/fdg_dpd/assets/standalone-dpd/pali-lookup-standalone.js` if that file is separate

---

## No Changes Made

No code was modified during this session. The handoff is at decision stage — user needs to confirm Option A or Option B before implementation begins.

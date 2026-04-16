# how_to_use.md — dpd-vib-rule Workflow

## Start
Run `dpd-vib-rule` from anywhere in the terminal.

**First-ever run** (no saved state):
```
Enter source value (e.g. VIN2.5.6.10) [or Enter to quit]: VIN2.5.6.10
Enter PAT file path (e.g. misc/pat/pc61.txt): misc/pat/pc60.txt
```

**Subsequent runs** (state remembered from last session):
```
Last rule: VIN2.5.6.10 (misc/pat/pc60.txt)
Source for next rule (suggested next PAT: misc/pat/pc61.txt) [or Enter to quit]: VIN2.5.6.11
PAT file [misc/pat/pc61.txt]:   ← just press Enter to accept suggestion
```

---

## Per-rule loop (repeats until you quit)

**Step 1 — Text input**

If the PAT file already exists on disk, it reads it automatically. Otherwise:
```
Paste the rule text below. Press Ctrl-D (EOF) when done:
```
Paste the Vibhanga rule text, press **Ctrl-D**. The script strips `{...}` variant readings,
saves cleaned text to `misc/pat/pcXX.txt` and `temp/text.txt`.

**Step 2 — Word extraction**
```
Found 7 unrecognized words:
bhikkhu
saṃgho
...
Backup TSV saved to temp/text_vib_example_pat_example.tsv
```
These are words not yet in the DB with `vib_example`/`pat_example` filled.

**Step 3 — GUI pause**
```
Add the above words in gui2/main.py → Pass2Add tab.
Press Enter when done (or type 'q' to quit):
```
Switch to gui2, add the words, come back, press **Enter**.

**Step 4 — Dry-run preview**
```
Previewing copy_examples for VIN2.5.6.10 (DRY RUN)...
[shows which rows would be updated, their IDs and lemmas]
Apply these changes to the database? [y/N]:
```
Review the preview. Type **`y`** to commit, anything else to skip.

**Step 5 — Progress saved, continue prompt**
```
Rule VIN2.5.6.10 done.
Suggested next PAT file: misc/pat/pc61.txt
Continue to next rule? [Enter] or quit [q]:
```
Press **Enter** to loop back to the next rule. Type **`q`** to exit.

---

## Quitting mid-rule

At the GUI pause (Step 3), typing `q` saves progress and exits cleanly.
Next session picks up from where you left off.

---

## Log

Everything is logged automatically to `~/logs/vib_rule_YYYY-MM-DD_HH-MM-SS.log`
(last 10 logs kept). `run_and_log.sh` handles this transparently.

---

## Old 7-step workflow → new

| Old | New |
|-----|-----|
| Edit `copy_examples.py` → set `source_value` | Enter source at prompt |
| Manually copy text → `misc/pat/pcXX.txt` | Paste at prompt |
| Copy text → `temp/text.txt` | Automatic |
| Run `list_of_words_from_txt.py` | Automatic |
| Review TSV | Words printed in terminal |
| Add words in gui2 | Same (still manual — gui2 is unchanged) |
| Run `copy_examples.py` again | Replaced by dry-run preview + `y` confirm |

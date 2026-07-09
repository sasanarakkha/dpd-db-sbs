# Docs Translation Queue

Stage 1 prep (`prep_analyzer.py`) appends `docs/` paths changed in the upstream sync range to
this checklist. Drain this queue in a separate session after the code sync is stable —
translation is independent of the code sync commit gate.

## Usage

During Stage 1 prep, `prep_analyzer.py` appends each changed `docs/` path here as an unchecked item.
ADVANCED reviews and assigns a translation strategy (full translation, targeted update, or
no-translate redirect). Items are checked off as translations land.

## Pending

- [ ] docs/technical/local_server_setup.md
- [ ] docs/technical/quick_start.md
- [ ] docs/technical/use_db.md
<!-- Stage 1 prep appends items here, e.g.:
- [ ] docs/changelog.md  (no-translate — mostly Pali data; use redirect pattern)
- [ ] docs/technical/dpd_headwords_table.md  (full translation needed)
-->

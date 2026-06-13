# Docs Translation Queue

Stage 3 appends `docs/` paths changed in the upstream sync range to this checklist.
Drain this queue in a separate session after the code sync is stable — translation
is independent of the code sync commit gate.

## Usage

After Stage 3 execution, FAST appends each changed `docs/` path here as an unchecked item.
ADVANCED reviews and assigns a translation strategy (full translation, targeted update, or
no-translate redirect). Items are checked off as translations land.

## Pending

<!-- Stage 3 appends items here, e.g.:
- [ ] docs/changelog.md  (no-translate — mostly Pali data; use redirect pattern)
- [ ] docs/technical/dpd_headwords_table.md  (full translation needed)
-->

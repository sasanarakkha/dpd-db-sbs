# project.md — DPS Fork of the Digital Pāḷi Dictionary

## What it is and why
A localized fork of the upstream Digital Pāḷi Dictionary (dpd-db), maintained at
sasanarakkha/dpd-db-sbs. It extends the upstream database with:
- A `Russian` table providing localized meanings, literal translations, and
  etymological cognates for Russian-speaking scholars.
- An `SBS` table mapping Pāḷi examples, chantings, and chapter references to the
  SBS curriculum and Pāḷi course materials.

**Upstream sync is a primary goal.** The fork must remain as close as possible to
upstream dpd-db/main at all times. Local extensions (Russian, SBS) are layered on
top without diverging from core upstream logic.

## Who it is for
- Russian-speaking Dhamma practitioners and Pāḷi students
- Students following the SBS curriculum
- Contributors verifying and enriching Russian and SBS data

## One-off or ongoing
Ongoing. Releases follow the Buddhist lunar calendar (full moon Uposatha, ~monthly).
Upstream sync runs continuously: upstream dpd-db/main → local `as_upstream` branch
→ local `sbs-ru` branch.

## What it will produce
- A SQLite database with DPD headwords extended by Russian and SBS tables
- Multi-format dictionary exports (GoldenDict, MDict, Kindle, Kobo, PDF)
- A Flet-based GUI for lexicographers
- A FastAPI webapp and MCP server for programmatic access
- Anki decks and SBS study materials for the study-tools repo

## How you'll know it worked
- **Upstream sync is clean** — shadow files are in parity with upstream sources,
  no unresolved drift between `as_upstream` and `sbs-ru`
- All data-integrity tests pass (100+ pytest checks)
- Russian and SBS tables are consistent with their source repositories
- Exports generate without error and render correctly in target platforms
- Each Uposatha release ships without regression

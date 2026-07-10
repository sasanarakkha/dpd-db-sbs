# Suggested upstream issue: Go `Lookup` struct missing `abbrev_other`, silent save failure, batch size near SQLite variable limit

**Repo:** https://github.com/digitalpalidictionary/dpd-db
**Found while:** local fork build (`dpd-db-sbs`, thread `20260709_upstream_sync`, Stage 4 verification).
**Status:** fixed locally (not upstreamed, not registered as a fork divergence — see note at bottom).

---

## Bug 1 — `go_modules/dpdDb/model.go`: `Lookup` struct is missing the `abbrev_other` column

Commit `04b5f541e` (#77, "abbreviations: wire into goldendict exporter and webapp") added a new
`abbrev_other` column to the `Lookup` model in `db/models.py`:

```python
abbrev: Mapped[str] = mapped_column(default="")
abbrev_other: Mapped[str] = mapped_column(default="")
epd: Mapped[str] = mapped_column(default="")
```

The column is `NOT NULL` in the SQLite DDL (SQLAlchemy's `default=""` is Python-side only — there is
no SQL-level `DEFAULT` clause on the column).

The Go struct `go_modules/dpdDb/model.go` (`type Lookup struct`) was never updated to match — it still
only has:

```go
Abbrev        string `gorm:"column:abbrev"`
Epd           string `gorm:"column:epd"`
Rpd           string `gorm:"column:rpd"`
```

`go_modules/deconstructor/data/matchdata.go`'s `SaveToDb()` wipes and rebuilds the *entire* `lookup`
table through this struct:

```go
tx.Exec("DELETE FROM lookup")             // wipes every row
tx.CreateInBatches(updatedResults, 2000)  // re-inserts via the (incomplete) Lookup struct
tx.Commit()
```

Because the struct is missing `abbrev_other`, the generated `INSERT` omits that column entirely,
and SQLite rejects every row:

```
NOT NULL constraint failed: lookup.abbrev_other
```

**Effect:** the whole `lookup` table rebuild fails — not just `abbrev_other`. Every column normally
carried through this rebuild (`deconstructor`, `roots`, etc.) ends up empty after a `go run
go_modules/deconstructor/main.go` run, because the failed insert means no rows are written at all.

**Fix:** add the missing field to the struct:

```go
type Lookup struct {
	Key           string `gorm:"column:lookup_key"`
	Headwords     string `gorm:"column:headwords"`
	Roots         string `gorm:"column:roots"`
	Deconstructor string `gorm:"column:deconstructor"`
	Variant       string `gorm:"column:variant"`
	See           string `gorm:"column:see"`
	Spelling      string `gorm:"column:spelling"`
	Grammar       string `gorm:"column:grammar"`
	Help          string `gorm:"column:help"`
	Abbrev        string `gorm:"column:abbrev"`
	AbbrevOther   string `gorm:"column:abbrev_other"`
	Epd           string `gorm:"column:epd"`
	Rpd           string `gorm:"column:rpd"`
	Other         string `gorm:"column:other"`
	Sinhala       string `gorm:"column:sinhala"`
	Devanagari    string `gorm:"column:devanagari"`
	Thai          string `gorm:"column:thai"`
}
```

(This repo's fork also carries a local `tpd` column on `Lookup` for Tamil, which is why our local
copy of this struct has one extra field beyond this list. That field is fork-specific and not part
of this upstream report — only `abbrev_other` applies upstream.)

---

## Bug 2 — `go_modules/deconstructor/data/matchdata.go`: `SaveToDb()` ignores DB errors

In the same function, right after the `DELETE FROM lookup`:

```go
tx := db.Begin()
// defer dpdDb.Rollback(tx)

// wipe the table clean
tx.Exec("DELETE FROM lookup")

// add the updated rows
tx.CreateInBatches(updatedResults, 2000)
tx.Commit()
```

Neither `tx.CreateInBatches(...)` nor `tx.Commit()` checks `.Error`. Contrast this with the two
`tools.HardCheck(err)` calls earlier in the same function (around building `updatedResults`), which
do fail loudly. The `Rollback` call is also commented out.

**Effect:** when the insert fails (e.g. Bug 1, or any future NOT NULL/schema mismatch), the Go
program still exits with status 0 and prints its normal summary output (`added:`, `updated:`,
`deleted:`, `muted:`, timings) as if it succeeded. Any caller — including
`scripts/bash/generate_components.py`'s `run_script()`, which does check subprocess exit codes and
would otherwise halt the build — has no way to detect the failure. The broken/emptied `lookup` table
silently ships downstream (empty deconstructor dictionaries, empty roots lookups) with no error
anywhere in the build log.

**Fix:** check the errors and fail loudly, consistent with the `tools.HardCheck` pattern already used
elsewhere in this function:

```go
tx := db.Begin()

// wipe the table clean
tx.Exec("DELETE FROM lookup")

// add the updated rows
if err := tx.CreateInBatches(updatedResults, 1500).Error; err != nil {  // batch size: see Bug 3
	tx.Rollback()
	tools.HardCheck(err)
}
tools.HardCheck(tx.Commit().Error)
```

---

## Bug 3 — `SaveToDb()` batch size is one column away from SQLite's bound-variable limit

`tx.CreateInBatches(updatedResults, 2000)` inserts 2000 `Lookup` rows per statement. SQLite's default
bound-variable limit is 32766 (`SQLITE_MAX_VARIABLE_NUMBER`, since SQLite 3.32.0). With the current
16-column struct that's `2000 × 16 = 32000` variables per statement — already within ~2% of the
ceiling.

This was invisible until Bug 1 was fixed locally: adding just one more column (`abbrev_other`) to
reach 17 columns puts `2000 × 17 = 34000` over the limit, and the fork's local `Lookup` struct (which
carries an 18th, fork-only column) hits `2000 × 18 = 36000` and panics with `too many SQL variables`
on every real build (851k+ rows in the deconstructor's top-five map, so `CreateInBatches` always
produces full 2000-row batches).

This isn't a fork-specific problem — it will reproduce upstream the moment `abbrev_other` (already
present in `db/models.py`, see Bug 1) is added to the Go struct, or any further column is added to
`Lookup`. Recommend lowering the batch size with margin, e.g.:

```go
tx.CreateInBatches(updatedResults, 1500)  // 1500 × N columns stays comfortably under 32766
```

---

## Suggested issue title

> Go `Lookup` struct out of sync with `abbrev_other` column; `SaveToDb()` silently swallows errors;
> batch size one column away from SQLite's variable limit

## Suggested issue body

Use the three bug descriptions above verbatim, plus:

> Found this while investigating why a from-scratch build's `deconstructor` GoldenDict/MDict
> dictionaries came out near-empty — the Go deconstructor's `SaveToDb()` was hitting
> `NOT NULL constraint failed: lookup.abbrev_other` on every insert (added by #77) and exiting 0
> anyway, so the build never reported a problem. Fixing that surfaced a second, previously-latent
> issue: the 2000-row batch size is already at ~97% of SQLite's bound-variable ceiling with the
> current 16-column struct, so adding the missing `abbrev_other` column (17 columns) alone is enough
> to tip it over into `too many SQL variables`. All three fixes are small and localized to
> `go_modules/dpdDb/model.go` and `go_modules/deconstructor/data/matchdata.go`.

---

## Note on this fork's handling

All three fixes are applied locally in this fork's working tree (`go_modules/dpdDb/model.go`,
`go_modules/deconstructor/data/matchdata.go`) to unblock the local build. Per explicit instruction,
they are **not** registered in `kamma/upstream_sync/registry.json` as fork divergences — they are
treated as plain upstream bugs to be reported and fixed upstream, at which point the next sync will
pull the real fix in directly (the local edits should be dropped/reconciled against whatever upstream
lands, rather than tracked as a permanent local override).

**Going forward:** any further fix made locally to `go_modules/dpdDb/model.go` or
`go_modules/deconstructor/data/matchdata.go` for an upstream-caused (non-localization) defect should
be added to this same document as a new "Bug N" section, so the eventual upstream issue/PR captures
everything found during this fork's build in one place.

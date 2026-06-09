# spec.md — gui2 Runtime Font Scaling

## Overview

Add a one-shot Flet widget constructor patch in `gui2/main.py` that multiplies
explicit `size=` / `text_size=` kwargs by a configurable factor (`1.4`) at app
startup, scaling all text across every tab uniformly. Remove the outdated
file-level `gui2/font_scaling_helper.py` (a destructive source-rewriter with no
importers). Update sync docs for `main.py`.

The optional DPS normalization (reducing DPS-specific hardcoded sizes so all
tabs render at an identical visual size) is a **separate, deferred concern** —
see "DPS normalization (deferred / optional)" below. It is not part of the
core change and is only undertaken if the scaled app actually looks inconsistent.

## Verified findings (Flet 0.28.3)

The spec's "key unknown" — whether Flet constructors are patchable — is
**confirmed safe** on the installed Flet 0.28.3:

- `ft.Text`, `ft.TextStyle`, `ft.TextField`, `ft.Dropdown` are plain Python
  classes with normal `__init__` (not dataclasses, no `__slots__`, no C-level
  init). All four accept the relevant `size=` / `text_size=` kwarg.
- The monkeypatch was run empirically: `size=10 → 14`, `text_size=20 → 28`,
  unset stays `None`, and a `TextStyle` nested in a `Text` is **not**
  double-scaled.
- `gui2/font_scaling_helper.py` has zero importers; its registry entry is at
  `kamma/upstream_sync/registry.json` line 216.

## OS independence

The patch operates at the Python/Flet layer, rewriting widget kwargs in memory
at construction time — **before** anything reaches Flutter or the OS renderer.
There is no platform-specific code path, so it behaves identically on macOS,
Linux, and Windows; nothing needs per-OS handling. Flet 0.28 exposes no native
global font-scale knob (Flutter's `textScaler` / `MediaQuery` is not surfaced on
the `page` API), so the constructor patch is the idiomatic approach.

## What it should do

1. At module level in `gui2/main.py`, **immediately after `import flet as ft`
   (line 5) and before the `from gui2.* import ...` view imports (lines 7–12)**,
   define `_DPS_FONT_SCALE = 1.4` and a `_make_font_scaler` helper. Patch the
   `__init__` of `ft.Text`, `ft.TextStyle`, `ft.TextField`, and `ft.Dropdown`
   to multiply numeric `size=` / `text_size=` kwargs by the factor, using
   `round()`. No exclusions — every tab including DPS is scaled. (Views build
   widgets at runtime, not at import, so import order is not load-bearing; the
   top-of-file placement is kept as a safe invariant.)

2. Delete `gui2/font_scaling_helper.py` and remove its entry from
   `kamma/upstream_sync/registry.json` (`local_only_files`).

3. Add a new numbered Local Change item to the `gui2/main.py` section in
   `kamma/upstream_sync/smd/gui.md` documenting the font scale patch.

## DPS normalization (deferred / optional)

This is **not** part of the core change and conflates two goals: font scaling
(above) vs. cross-tab visual uniformity (here). DPS's larger hardcoded sizes may
be intentional, and a global 1.4× preserves whatever ratio exists today. So:

- Ship items 1–3 first, launch, and look at the scaled app.
- **Only if** DPS visibly looks inconsistent with the other tabs, normalize its
  explicit sizes down to upstream originals so the global scale renders them at
  a matching size:
  - `dps_view.py`: `text_size=17 → 14`, `size=15 (hint) → 10`
  - `dps_fields.py`: `size=15 → 12`
  - `icon_size=16` is unchanged (icons are not scaled).
- The arithmetic relies on `round()`: `14×1.4=19.6→20`, `12×1.4=16.8→17`.

## Assumptions & uncertainties

- Flet constructor patchability is **resolved, not an open risk** — verified on
  Flet 0.28.3 (see "Verified findings" above). If Flet is later upgraded to a
  version that moves these controls to dataclasses / `__slots__`, re-verify.
- `_DPS_FONT_SCALE = 1.4` is taken from the old helper. If the result looks
  too large after testing, adjust the constant (single tuning point).
- If DPS normalization is deferred, DPS fonts render proportionally larger than
  other tabs (e.g. `text_size=17 × 1.4 = 24`). This is acceptable unless it
  looks inconsistent — see "DPS normalization (deferred / optional)".
- `gui2/analysis_view.py` (local, not upstream) will be scaled — intentional.
- `icon_size=` is not patched — icons will look proportionally smaller; accepted.

## Constraints

- Must not modify any upstream gui2 file.
- `registry.json` and `smd/gui.md` must be updated atomically with the code
  change (Shadow Documentation Gate).
- DPS normalization (deferred / optional) only runs if, after manual inspection,
  DPS looks visibly inconsistent with the other tabs.
- All changed files must pass ruff, pyright, and pyrefly.

## How we'll know it's done

- App launches and text in all upstream tabs is visibly larger.
- DPS tab text is acceptable (matches other tabs if normalization was applied).
- `grep -r font_scaling_helper .` returns no hits.
- `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` passes.
- `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` passes.
- All quality gates pass on every modified file.

## What's not included

- UI toggle for the scale factor.
- Scaling `icon_size=`.
- Any other gui2 improvements.

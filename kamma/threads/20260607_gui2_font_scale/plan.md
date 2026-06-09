# plan.md — gui2 Runtime Font Scaling

## Verified before planning (Flet 0.28.3)

- `ft.Text`, `ft.TextStyle`, `ft.TextField`, `ft.Dropdown` are plain Python
  classes with normal `__init__` (not dataclasses, no `__slots__`). All accept
  the relevant `size=` / `text_size=` kwarg. The monkeypatch was run live:
  `size=10 → 14`, `text_size=20 → 28`, unset stays `None`, no double-scaling of
  a `TextStyle` nested in a `Text`.
- `gui2/font_scaling_helper.py` has **zero importers**; registry entry is at
  `kamma/upstream_sync/registry.json` line 216.
- **OS-independent**: the patch rewrites kwargs in memory before Flutter/OS
  rendering, so behaviour is identical on macOS, Linux, and Windows. Flet 0.28
  has no native global font-scale knob, so this is the idiomatic approach.

## Architecture Decisions

- **Patch site**: module level in `gui2/main.py`, immediately after
  `import flet as ft` (line 5) and **before** the `from gui2.* import ...` view
  imports (lines 7–12). Views build widgets at runtime, not at import, so import
  order is not load-bearing; top-of-file is kept as a safe invariant.
- **No exclusions**: all tabs including DPS are scaled. DPS normalization for
  visual uniformity is a separate, **deferred/optional** step (see Phase 3).
- **Widgets patched**: `ft.Text` (`size`), `ft.TextStyle` (`size`),
  `ft.TextField` (`text_size`), `ft.Dropdown` (`text_size`). `icon_size` is
  intentionally excluded. Scaling uses `round()`.
- **Scale factor**: `_DPS_FONT_SCALE = 1.4`. Adjust this constant only —
  no other changes needed to retune the scale.
- **No new file**: patch is ~12 lines inline in `main.py`. `font_scaling_helper.py`
  is deleted entirely.
- **Phase 3 is deferred/optional**: DPS normalization is a distinct concern
  (visual uniformity, not font scaling). Ship Phases 1, 2, 4 first; only do
  Phase 3 if the scaled app shows DPS visibly inconsistent with other tabs.

---

## Phase 1 — Cleanup

### Task 1.1 [x] — Delete `gui2/font_scaling_helper.py`
- Delete the file `gui2/font_scaling_helper.py`.
- → verify: `ls gui2/font_scaling_helper.py` returns "No such file".

### Task 1.2 [x] — Remove from `registry.json`
- Open `kamma/upstream_sync/registry.json`.
- Remove the `"gui2/font_scaling_helper.py"` entry from the `local_only_files`
  array (currently line ~216).
- → verify: `grep font_scaling_helper kamma/upstream_sync/registry.json`
  returns no output.

### Phase 1 Verification
- `grep -r font_scaling_helper . --include="*.py" --include="*.json" --include="*.md"` returns zero hits.

---

## Phase 2 — Implementation

### Task 2.1 [x] — Add runtime font patch to `gui2/main.py`
- Context: `gui2/main.py` is a `modified_upstream_files` entry (DISCUSS rule).
  Adding code here is within scope.
- Insert the following block immediately after `import flet as ft` (line 5) and
  **before** the `from gui2.* import ...` view imports (lines 7–12):

  ```python
  # DPS local: runtime font scaling — adjust _DPS_FONT_SCALE to retune
  _DPS_FONT_SCALE: float = 1.4


  def _make_font_scaler(original_init, attrs: tuple[str, ...], scale: float):
      def _scaled_init(self, *args, **kwargs):
          for attr in attrs:
              v = kwargs.get(attr)
              if isinstance(v, (int, float)):
                  kwargs[attr] = round(v * scale)
          original_init(self, *args, **kwargs)

      return _scaled_init


  ft.Text.__init__ = _make_font_scaler(ft.Text.__init__, ("size",), _DPS_FONT_SCALE)
  ft.TextStyle.__init__ = _make_font_scaler(
      ft.TextStyle.__init__, ("size",), _DPS_FONT_SCALE
  )
  ft.TextField.__init__ = _make_font_scaler(
      ft.TextField.__init__, ("text_size",), _DPS_FONT_SCALE
  )
  ft.Dropdown.__init__ = _make_font_scaler(
      ft.Dropdown.__init__, ("text_size",), _DPS_FONT_SCALE
  )
  ```

- → verify: `grep -n "_DPS_FONT_SCALE\|_make_font_scaler" gui2/main.py` shows
  entries.

### Task 2.2 [x] — Quality gates on `main.py`
- `uv run ruff check --fix gui2/main.py && uv run ruff format gui2/main.py`
- `uv run pyright gui2/main.py`
- `uv run --with pyrefly pyrefly check --min-severity warn gui2/main.py`
- → verify: all three exit 0.

### Phase 2 Notes
- ruff and pyright: ✅ clean.
- pyrefly: 2 pre-existing errors in untouched code (line 59: `page.theme.font_family`; line 334: `profiler` conditionally unbound). Not introduced by this change.

### Phase 2 Verification
After Phase 2 the user manually launches the app and confirms text is visibly
larger in upstream tabs (Global, Pass1, Pass2, etc.). At this point Phases 1, 2,
and 4 constitute a complete, shippable change. Phase 3 is only undertaken if the
user observes that the DPS tab looks visibly inconsistent with the other tabs.

---

## Phase 3 — Normalize DPS font sizes  *(executed — user confirmed DPS was inconsistent)*

User confirmed DPS tab was visually inconsistent after Phase 2. Scale factor also
changed from 1.4 → 1.5 (user adjustment). Normalization targets were recalculated
for 1.5×. Implementation went beyond original spec — additional files required.

### Task 3.1 [x] — Normalize `gui2/dps_view.py`
- `text_size=17 → 14` (3 occurrences), hint `size=15 → 14` (2 occurrences).
- Note: spec said size=15→10 (calibrated for 1.4×); recalculated to 14 for 1.5×.
- All pass. `grep "text_size=17\|size=15" gui2/dps_view.py` → 0 hits.

### Task 3.2 [x] — Normalize `gui2/dps_fields.py`
- Label `size=15 → 12` (matches upstream dpd_fields.py size=12 → 18 at 1.5×).
- Added: skip `text_size` in setattr loops for DpsExampleField and DpsMeaningField
  (see Task 3.4 context).

### Task 3.3 [x] — Quality gates on DPS files
- ruff, pyright: all passed on dps_view.py, dps_fields.py, dps_field_mapping.py.

### Task 3.4 [x] — Fix DpsExampleField / DpsMeaningField text size (beyond original scope)
Root cause discovered: `common_params` in `dps_field_mapping.py` had `text_size: 17`.
For DpsExampleField/DpsMeaningField, this was applied via `setattr()` AFTER
construction, bypassing the __init__ patch. Fix:
- `dps_field_mapping.py`: `text_size: 17 → 14` in `common_params`.
- `dps_fields.py`: skip `text_size` in both setattr loops so `DpdTextField`
  patch value (21) isn't overwritten.
- `main.py`: added `DpdTextField` post-init patch — if `text_size is None`,
  sets `text_size = round(14 * _DPS_FONT_SCALE)`.
- Also added `ft.TextTheme` + `ft.TabsTheme` to `App.__init__` so tabs,
  buttons, and other theme-driven text scale correctly.
- → verify: ⚠️ AWAITING USER CONFIRMATION that Example/Meaning fields now match.

---

## Phase 4 — Documentation

### Task 4.1 [x] — Update `kamma/upstream_sync/smd/gui.md`
- In the `gui2/main.py` section, append to **Local Changes**:

  ```
  5. Runtime font scaling patch (module level, top of file after
     `import flet as ft`): patches `ft.Text.__init__`, `ft.TextStyle.__init__`,
     `ft.TextField.__init__`, and `ft.Dropdown.__init__` via `_make_font_scaler`
     to multiply `size=` / `text_size=` kwargs by `_DPS_FONT_SCALE = 1.4`
     (using `round()`). No exclusions — all tabs are scaled uniformly. Adjust
     `_DPS_FONT_SCALE` in `main.py` to retune the app-wide font size. (If DPS
     normalization was applied: `dps_view.py` / `dps_fields.py` explicit sizes
     were reduced to upstream values so they render at a matching visual size
     after scaling — otherwise omit this sentence.)
  ```

- Append to **Watch For**:

  ```
  - If upstream adds new text-bearing widgets with explicit `size=` /
    `text_size=` args that should scale, add them to the `_make_font_scaler`
    calls in `main.py`.
  - If DPS adds new widgets with explicit sizes, use upstream-matching values
    (e.g. `text_size=14`, `size=10`) so the global scale renders them correctly.
  ```

- → verify: `grep "_DPS_FONT_SCALE" kamma/upstream_sync/smd/gui.md` returns
  a hit.

### Task 4.2 [x] — Registry and SMD validation
- `uv run python3 kamma/upstream_sync/scripts/validate_registry.py`
- `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py`
- → verify: both exit 0.

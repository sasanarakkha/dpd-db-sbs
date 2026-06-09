# Handoff — gui2 Runtime Font Scaling
_Written: 2026-06-07, end of session_

---

## Phases completed

### Phase 1 ✅
- Deleted `gui2/font_scaling_helper.py`.
- Removed its entry from `kamma/upstream_sync/registry.json`.

### Phase 2 ✅
- Added font scaling patch to `gui2/main.py` (module level, after all imports,
  before `class App`): patches `ft.Text`, `ft.TextStyle`, `ft.TextField`,
  `ft.Dropdown` via `_make_font_scaler`. Scale factor `_DPS_FONT_SCALE = 1.5`
  (user changed from spec's 1.4 during testing).
- Added `ft.TextTheme` + `ft.TabsTheme` to `App.__init__` (after
  `page.theme = ft.Theme()`) so tabs, buttons, radio labels, and TextFields
  without explicit sizes also scale through Flutter's theme system.
- Added `DpdTextField` post-init patch: if `text_size is None` after
  construction, sets `text_size = round(14 * _DPS_FONT_SCALE)`. Fixes all
  fields using `DpdTextField` as their main text area.
- User confirmed: tabs, buttons, field text, bottom rows all scaled correctly.

### Phase 3 ✅ (user confirmed DPS visually inconsistent → proceeded)
- `dps_view.py`: `text_size=17 → 14` (3×), hint `size=15 → 14` (2×).
- `dps_fields.py`: label `size=15 → 12`.
- `dps_field_mapping.py`: `common_params["text_size"]: 17 → 14`.
- `dps_fields.py`: skip `text_size` in the two `setattr` loops (DpsExampleField,
  DpsMeaningField) so the DpdTextField patch value isn't overwritten.

### Phase 4 ✅
- `kamma/upstream_sync/smd/gui.md`: Local Changes item 5 + Watch For bullets added.
- `validate_registry.py` + `verify_smd_coverage.py`: both passed.

---

## ⚠️ Awaiting user confirmation

The last fix (dps_field_mapping.py + dps_fields.py setattr skip) was applied but
**NOT yet confirmed** by the user. The user ended the session immediately after the
fix was applied. On next session, ask the user to confirm whether Example 1,
Example 2, Sbs Example 1, Ru Meaning etc. now match the other DPS fields.

If confirmed → mark plan.md Task 3.4 verify as passed, proceed to review.
If NOT confirmed → diagnose further (see Known Issues below).

---

## Files modified (complete list)

| File | Change |
|---|---|
| `gui2/font_scaling_helper.py` | DELETED |
| `kamma/upstream_sync/registry.json` | Removed font_scaling_helper entry |
| `gui2/main.py` | Font scale patch block + TextTheme/TabsTheme + DpdTextField patch |
| `kamma/upstream_sync/smd/gui.md` | Local Changes #5 + Watch For bullets |
| `gui2/dps_view.py` | text_size=17→14 (3×), hint size=15→14 (2×) |
| `gui2/dps_fields.py` | label size=15→12; skip text_size in 2 setattr loops |
| `gui2/dps_field_mapping.py` | common_params text_size=17→14 |

---

## Architecture of the scaling system (as built)

```
_DPS_FONT_SCALE = 1.5  (single tuning point in main.py)

Layer 1 — Constructor patch (explicit sizes):
  ft.Text.__init__      → scales size= kwarg
  ft.TextStyle.__init__ → scales size= kwarg
  ft.TextField.__init__ → scales text_size= kwarg
  ft.Dropdown.__init__  → scales text_size= kwarg

Layer 2 — DpdTextField post-init (fields without explicit text_size):
  DpdTextField.__init__ wrapper → sets text_size=round(14*scale) when None

Layer 3 — Theme (tabs, buttons, radio labels, etc.):
  page.theme.text_theme = ft.TextTheme(body_large=16, label_large=14, …)
  page.theme.tabs_theme = ft.TabsTheme(label_text_style=size=14, …)
  All sizes passed using MD3 originals (16, 14, etc.) → scaled by Layer 1
```

---

## Known issues / not fixed

- `dps_meaning_field.py`: `add_to_dict_field` has `text_size=15` → 23. This is
  a small helper sub-field ("Add Russian spelling"). User has not complained.
- `dps_example_field.py`: `bold_field` (`text_size=15` → 23), `book_dropdown`
  (`text_size=17` → 26), label_styles (`size=15` → 23). These are visible but
  user has not specifically complained about sub-field inconsistency.
- pyrefly: 2 pre-existing errors in main.py lines 59, 334 (untouched code).

---

## Next steps

1. Confirm the last fix worked (Example/Meaning fields match other DPS fields).
2. If sub-fields (bold, book dropdown in example fields) also need normalization,
   fix `dps_example_field.py` similarly: text_size=17→14, size=15→14.
3. Run `/kamma:3-review` in a fresh session.

# SMD: GUI

**File**: `gui2/main.py`
- **Category**: modified_upstream_files
- **Sync Rule**: DISCUSS
- **Why DISCUSS**: Imports `fast_api_utils_dps` (DPS-specific server launcher) instead of upstream's `fast_api_utils`, and adds `DpsView` and `AnalysisView` tabs. Blind porting removes DPS GUI entirely.
- **Local Changes**:
  1. `from tools.fast_api_utils_dps import start_dpd_server` (line ~11) replaces upstream's `fast_api_utils` import.
  2. `DpsView` tab (line ~91): `self.dps_view = DpsView(self.page, self.toolkit)`.
  3. `AnalysisView` tab (line ~92): `self.analysis_view = AnalysisView(...)`.
  4. Conditional imports for `DpsView`/`AnalysisView` inside the class body (lines ~26-27).
- **Watch For**:
  - Upstream GUI refactors that change the tab initialization pattern will break DPS tab injection — check constructor signature.
  - If upstream switches from `fast_api_utils` to another server module, `fast_api_utils_dps` must be updated to match the new API.
  - New upstream view tabs added to `main.py` should be reviewed to ensure DPS views are still appended correctly.

---


**File**: `gui2/pass2_add_view.py`
- **Category**: modified_upstream_files
- **Sync Rule**: PORT
- **Local Changes**:
  1. `from tools.fast_api_utils_dps import request_dpd_server` (line ~24) replaces upstream's `fast_api_utils` import for DPS server requests.
  2. All server request calls go through `request_dpd_server` from the DPS shadow module, ensuring DPS-specific server configuration (host/port/timeout) is used instead of upstream defaults.
- **Watch For**:
  - If upstream changes the function name in `fast_api_utils`, the `fast_api_utils_dps` shadow must be updated to match.
  - Upstream GUI refactors to `Pass2AddView` constructor or method signatures need manual review.

---

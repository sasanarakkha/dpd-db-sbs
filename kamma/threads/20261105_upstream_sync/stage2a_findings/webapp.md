# Webapp upstream diff analysis (be49bffe2c2c..c54f942ee3f6)

Global notes
- Shared upstream modules the new upstream webapp code needs but local HEAD lacks (all are plain upstream Tier-1 copies, must be pulled): `tools/search_deadline.py` (new), `tools/server_mode.py` (new), `tools/version.py` (adds `make_permalink`; local has no such symbol), `tools/paths.py` (adds `webapp_cc_icons_path` etc.), `tools/tipitaka_db.py` (adds `limit` kwarg), `tools/bold_definitions_search.py` (+2 lines, `limit` kwarg), `exporter/webapp/static/cc_icons.svg` (new, referenced by toolkit.py at import), `tools/configger.py` (`show_tbw` default "no"), `db/models.py` (`SuttaInfo.s_4nt_link` property; `dv_pts` kept), new pip dep `brotli` (precompressed_index.py).
- Upstream new files: `exporter/webapp/precompressed_index.py` (IndexStaticFiles, publish_index; imports `exporter.webapp.response_encoding.accepts_encoding`, brotli, anyio), `exporter/webapp/response_encoding.py` (encode_search_response), `tools/prepare_webapp_lookup.py` (new, standalone script; no importer found in repo), `generate_search_index.py` now calls `publish_index` (writes search_index.json + gz/br sidecars). `exporter/webapp/generate_search_index.py` is NOT shadowed (no `_ru` copy), so it is just an upstream copy.
- Only upstream `main.py` imports precompressed_index/response_encoding. `toolkit.py` imports neither (it imports `ProjectPaths().webapp_cc_icons_path`, read at module import time -> FileNotFoundError if cc_icons.svg missing).
- IMPORTANT: shadows main_ru.py / toolkit_ru.py import upstream `exporter.webapp.toolkit.make_dpd_html` (SBS routes use it) and `exporter.webapp.preloads`. So upstream toolkit.py changes affect SBS routes directly.
- Registry entries: `exporter/webapp/data_classes.py` and `static/app.js` are `modified_upstream_files` (PORT); `data_classes_ru.py`, `toolkit_ru.py`, `main_ru.py`, `ru_templates/` in `russian_copies` (PORT); `sbs_templates/` entry at registry.json ~line 1165; `tools/fast_api_utils_dps.py` in `inspired_by_upstream` (inspired_only).

---
### exporter/webapp/main.py -> exporter/webapp/main_ru.py

1. Commits: cbece3dd5 #277 serve precompressed search_index.json; 13b6a7e90 #277 Brotli for large /search_json; 9065e68f9 #268 bound search memory and time, searches take turns; e8a92b6d3 #261 move license constants to toolkit; df11da4e2 #262 cite: short permalinks; ac0251128 #261 cc licence in html results + json; 6c3e91ef4 #157 pyrefly gate (pyrefly ignore comment); 326612139 #252 sutta info show_tbw toggle.

2. Upstream changes (hunks):
- New imports: `anyio`, `RedirectResponse`, `IndexStaticFiles` (precompressed_index), `OperationalError`, `starlette.convertors.{Convertor, register_url_convertor}`, `encode_search_response`, `LICENSE_LINK_HEADER, LICENSE_NOTICE` from toolkit, `BUSY_MESSAGE, SearchStopped, regex_deadline, sub` from tools.search_deadline, `config_test` from tools.configger. `StaticFiles` import removed.
- CORS middleware: added `expose_headers=["Link"]`.
- `app.mount("/static", IndexStaticFiles(...))` replaces StaticFiles.
- `templates.env.globals["show_tbw"] = config_test("dictionary","show_tbw","yes")`.
- `/search_html` and `/gd`: `headers=LICENSE_LINK_HEADER` on TemplateResponse.
- `/search_json`: response now includes `"license": LICENSE_NOTICE`; returns `encode_search_response(request, JSONResponse(..., headers=LICENSE_LINK_HEADER))`; removed bogus `Accept-Encoding: gzip` header.
- `/bd_search`: new `BD_DISPLAY_LIMIT = 100`; search wrapped in `regex_deadline()`, `limit=BD_DISPLAY_LIMIT+1`, highlight uses `sub` (deadline-aware) and `re.escape(q2)` when option=="plain"; catches `(SearchStopped, OperationalError)` and shows `deadline.stopped.message`; "100+" count; trimming moved inside.
- `/tt_search`: strips q, empty q returns `{"total":0,"results":[]}`; books de-duplicated; `regex_deadline()` + `limit=limit+1`; `SearchStopped` returns error JSON.
- `/audio`: Range regex bounded `bytes=(\d{1,15})-(\d{0,15})`.
- New: `LOOKUP_PATHS/LOOKUP_RUNNING=2/LOOKUP_MAX_WAITING=20/LOOKUP_WAIT_SECONDS=20`, `lookup_limiter = anyio.CapacityLimiter`, `lookup_busy_response()`, `@app.middleware("http") lookups_take_turns` (limits /search_json, /search_html, /gd).
- New: `HeadwordIdConvertor` + `register_url_convertor("headword_id", ...)` + route `@app.get("/{headword_id:headword_id}") permalink_page` -> `RedirectResponse(f"/?q={id}", 308)`.

3. Shadow main_ru.py status (HEAD still the old form; imports plain `StaticFiles`, no limiter, old bd/tt code):
- PORT: CORS `expose_headers=["Link"]` (anchor: `app.add_middleware(CORSMiddleware...)`); IndexStaticFiles mount (anchor `app.mount("/static"...)`) -- only if search_index.json precompression wanted (requires brotli dep + precompressed_index.py + response_encoding.py pulled; both are plain upstream files). main_ru serves same static dir/search_index.json.
- PORT: `templates_ru.env.globals["show_tbw"]` and `templates_sbs.env.globals["show_tbw"]` (needed once ru/sbs dpd_headword.html gets `and show_tbw`; undefined -> falsy hides TBW Legacy). Needs `config_test` import.
- PORT: license header/body on `db_search_json_ru`, `db_search_json_sbs`, `db_search_gd_ru`, `db_search_gd_sbs`, `db_search_html_sbs` (add `LICENSE_LINK_HEADER`, `"license": LICENSE_NOTICE`, `encode_search_response`). Note: toolkit LICENSE_HTML appended only inside upstream `make_dpd_html`; `make_dpd_html_ru` needs the equivalent (see toolkit section). DECISION for owner: licence text in RU is English / upstream-attributed; keep as upstream for strict parity.
- PORT: `lookups_take_turns` middleware + constants + `lookup_busy_response`. Must extend `LOOKUP_PATHS` with the shadow paths: `/sbs/search_json`, `/sbs/gd`, `/sbs/search_html` (upstream paths `/search_json`, `/gd` exist in main_ru; `/search_html` does NOT exist in main_ru, only `/sbs/search_html`). BUSY branch keys on `path == "/search_json"`; need `/sbs/search_json` too. BUSY_MESSAGE is English; RU localisation optional (UNCERTAIN whether wanted).
- PORT: `db_search_bd` regex_deadline/limit/escape/SearchStopped (main_ru version has RU message strings "результатов найдено" - keep, layer on top). Must keep Russian messages; deadline message from `tools.search_deadline` is English.
- PORT: `tt_search` strip/dedupe/limit/regex_deadline (identical code in main_ru).
- PORT: audio Range regex bound (identical code in main_ru).
- PORT: `HeadwordIdConvertor` + `permalink_page`. Shadow note: redirects to `/?q=<id>` = RU home (fine; SBS has no permalinks). Also toolkit change makes bare number always headword-id (see toolkit).
- SKIP: pyrefly ignore comment is attached to upstream `templates.env.globals`; if porting show_tbw to main_ru, add same pyrefly comment (pre-completion gate requires pyrefly clean).
- Shadow-only code to preserve: `/sbs*` routes, `headwords_clean_set_ru`, `dpd_release_version`, `rupth`, `templates_ru/templates_sbs`, `__main__` uvicorn("main_ru:app").

4. Structural refactor check: mostly feature additions. Minor: removed `Accept-Encoding: gzip` bogus response header; `re.sub` -> `sub` from search_deadline; bd search body restructured inside `with regex_deadline()`. No type-hint modernisation / os->pathlib / print->pr found.

5. Breakage risk if shadow NOT updated: main_ru.py itself imports only symbols that still exist upstream (`make_dpd_html`, preloads fns, `search_all_cst_texts`, `search_books`, `CSSManager`, `ProjectPaths`). Old call signatures still valid (new `limit` kwargs default None). So main_ru imports/runs unchanged. Risks arise only indirectly: (a) toolkit.py new top-level read of `cc_icons.svg` (needs file + `paths.py` attr); (b) SBS routes call upstream `make_dpd_html`, which now needs `ProjectPaths.webapp_cc_icons_path`. If tools/paths.py is not also updated -> AttributeError at import of main_ru (via toolkit). Pull paths.py + cc_icons.svg together.

---
### exporter/webapp/toolkit.py -> exporter/webapp/toolkit_ru.py

1. Commits: 08035b066 #277 indexed case-insensitive lookup; 9065e68f9 #268 bound search memory/time; e8a92b6d3 #261 license constants to toolkit; df11da4e2 #262 cite permalinks; 05f5d7326 #261 drop author name from cc notice; 540bdd874 styled tooltips, dropped cc rollover; ac0251128 #261 cc licence; 6c3e91ef4 #157 pyrefly.

2. Upstream changes:
- Import `literal_column` added.
- New module constants: `LICENSE_URL, LICENSE_NAME, LICENSE_HOLDER, LICENSE_ATTRIBUTION, _CC_ICONS` (reads `ProjectPaths().webapp_cc_icons_path` at import), `LICENSE_HTML`, `LICENSE_LINK_HEADER`, `LICENSE_NOTICE`.
- `make_dpd_html`: `only_suggestions` flag; Lookup query changed from `ilike(q)` to `lookup_key.collate("NOCASE").in_((q, q+"."))` ordered by `literal_column("lookup.rowid")`, with NUL-byte fallback using escaped `ilike`; `if lookup_results and not q.isdecimal()` (bare numbers skip lookup table); `elif q.isnumeric()` -> `q.isdecimal()`, `int(q)` only if `len(q)<=18`; `only_suggestions=True` after each `find_closest_matches` fallback; `LICENSE_HTML` appended when `dpd_html and not only_suggestions`.
- Dead code removed: the entire unreachable duplicate block after the retry loop (~190 lines), replaced by `raise RuntimeError(f"make_dpd_html exhausted {retries} retries ...")`.
- `find_closest_matches`: `ascii_to_unicode_dict[q]` -> `.get(q, [])`.

3. Shadow toolkit_ru.py status (anchors in `make_dpd_html_ru`):
- Still has the old `ilike` lookup (lines ~71-72), `q.isnumeric()` (231), the dead duplicate block after the retry loop (~290-483) incl. a second `ilike` (295) and `q = q.casefold()`, `find_closest_matches` using `ascii_to_unicode_dict[q]` (486+).
- PORT: NOCASE indexed lookup + NUL fallback; `not q.isdecimal()` gate; `isdecimal`/18-digit guard; `.get(q, [])` in local `find_closest_matches`; `only_suggestions` + LICENSE_HTML append (import `LICENSE_HTML` from `exporter.webapp.toolkit`; do not duplicate constants -- upstream moved constants to toolkit specifically for reuse); remove dead duplicate block and replace with the RuntimeError raise (dead-code removal = structural, shadow should mirror). Shadow-only: `joinedload(.ru)` eager loading, `RpdData`/`Lookup.rpd`, `templates_ru`, RU "no results" text -- preserve.
- Note: shadow's dead block contains `q.casefold()`, which is not applied in the live loop (check; UNCERTAIN whether live branch lowercases q - upstream doesn't; NOCASE handles ASCII only, same as upstream).

4. Structural refactor check: YES - (a) dead code removal (unreachable post-loop duplicate of whole body) + explicit RuntimeError, (b) `isnumeric`->`isdecimal`, (c) `find_closest_matches` `.get`. No type-hint/pathlib/print changes.

5. Breakage risk: toolkit_ru.py imports `data_classes_ru`, `tools.exporter_functions`, `pali_sort_key`, `paths`, `paths_ru`, `variants_manager`; none removed upstream in this range for its used names (not verified for tools.exporter_functions / variants_manager changes - out of my domain; UNCERTAIN). Not updating toolkit_ru does not break import. Pulling upstream toolkit.py verbatim requires `cc_icons.svg` + `paths.py` `webapp_cc_icons_path`; shared by SBS routes. Existing behaviour for RU would stay on old ilike lookup (works but slower/inconsistent with SBS).

---
### exporter/webapp/data_classes.py -> data_classes_ru.py (and data_classes.py itself)

1. Commits: df11da4e2 #262 cite: short permalinks.
2. Upstream change: `from tools.version import make_permalink`; `HeadwordData.__init__` adds `self.permalink = make_permalink(i.id)` (used by new feedback section in dpd_headword.html).
3. Local `data_classes.py` (registered modified_upstream_files): has local edits: `from tools.configger import config_test`; `self.ru`/`self.sbs` via `convert_newlines`; `show_ru_data`; extended `string_columns` (`link`, ru_*, sbs_* etc.). Upstream hunk touches two disjoint lines (import line placed between date_and_time and meaning_construction; one line after `self.date`) -> text merge should be clean. PORT both lines. Registry `local_changes` text (line numbers) will drift; update if it mentions `self.date` area (lines ~18/26).
   Shadow `data_classes_ru.py`: `HeadwordData.__init__` (line 12-33) has no `permalink`. PORT: add `self.permalink = make_permalink(i.id)` + import, required only if ru_templates/dpd_headword.html adopts upstream's Permalink row (template uses `d.permalink`; undefined in Jinja renders empty href silently, no crash).
4. Structural refactor check: none found.
5. Breakage risk: upstream `make_permalink` exists only in new upstream `tools/version.py` (local lacks it) -> pulling data_classes.py without tools/version.py raises ImportError at import of data_classes (shared by toolkit.py/SBS and main_ru). `tools/version.py` imports `tools.uposatha_day`, `tools.configger.config_update`, `tools.paths` (assume pulled together). data_classes_ru unaffected until ported.

---
### exporter/webapp/templates/dpd_headword.html -> ru_templates/ and sbs_templates/

1. Commits: 3ae112bf9 feedback sync wording; 196f0e734 #271 offer-help form; a5249fd37 #262 how-to-cite link, permalink pics; 904891e2f families headings agree in number; fd2978211 capitalize permalink; df11da4e2 #262; 1ca07cae2 pts refs from pts-cst concordance, drop dv pts source; 326612139 #252 show_tbw; 9ab176943 #251 s.4nt.org link.

2. Upstream hunks:
 a. `{% if d.su.tbw_legacy %}` -> `{% if d.su.tbw_legacy and show_tbw %}` (needs jinja global `show_tbw`).
 b. New row `{% if d.su.s_4nt_link %}` s.4nt.org after SuttaCentral section (needs `SuttaInfo.s_4nt_link` in db/models.py upstream).
 c. PTS concordance: moved `dv_pts` out of the `dv_exists` block into its own "Pali Text Society" heading block; DV catalogue heading now separate (`{% if d.su.dv_exists %}` heading only).
 d. Whitespace cleanup (trailing spaces).
 e. Family compound heading: singular/plural `{% if d.fc[0].count == 1 %}compound which contains{% else %}compounds which contain{% endif %}`; `jump` link ⤴ moved outside the `{% endif %}` so it shows in the singular case too.
 f. Feedback: Jinja comment about 3 sync locations; new `Permalink` row (`d.permalink`); "Did you spot a mistake in the dictionary?" shortened (dropped "Have something to add?"); new "How to cite" paragraph (https://digitalpalidictionary.github.io/how_to_cite/); "Get involved" mailto replaced by "Contribute to DPD" link (contributing/#offer-your-help).

3. Local targets:
 - RU (ru_templates/dpd_headword.html): tbw_legacy at line ~425 (inside combined links, different markup, anchor "dhamma.gift (BW)") -> PORT a (add `and show_tbw`, requires main_ru global). s_4nt link: absent -> PORT b (RU localize label; skip-able, RU shadow has its own SuttaCentral layout - check the SuttaCentral block). PTS/DV (lines 641-660): same old structure -> PORT c. Family compound heading (line ~1275 "составных содержащих", ~1309-1311 uses its own RU singular/plural already) -> upstream fix e largely SKIP (RU has own wording); verify the ⤴ jump link placement near lines 1314/1319 (RU has jump in both?). Feedback (line 1460+) is fully RU-rewritten (Google forms, translation text) -> PORT f only partially: Permalink row (needs `d.permalink` in data_classes_ru), RU "How to cite" optional; SKIP "Contribute to DPD" if RU keeps own contact links (rationale: RU feedback block is locale-specific). Needs owner decision (UNCERTAIN).
 - SBS (sbs_templates/dpd_headword.html): tbw_legacy line 449 -> PORT a. s_4nt absent -> PORT b. PTS/DV lines 724-745 -> PORT c. Family heading line 1487 "compounds which contains" -> PORT e (count==1 fix) plus ⤴ move at line 1526 (inside `{% else %}` currently -> move out). Feedback: "ID" line 1691, text at ~1724 "Did you spot a mistake in the dictionary? Have something to add?" and "Get involved" mailto at ~1747 -> PORT f fully (SBS feedback is close to upstream): Permalink row, shortened text, How to cite, Contribute to DPD. SBS has extra SBS-specific mistake links ("Did you spot a mistake in SBS examples?") -> keep.

4. Structural refactor check: moderate - section reorder (PTS block split from DV block) and family heading restructure; no pure rename/move of templates.

5. Breakage risk: if templates NOT updated, nothing breaks (old template markup still renders). If templates ARE updated: `show_tbw` undefined (falsy) unless set in main_ru; `d.permalink` undefined unless data_classes_ru updated; `d.su.s_4nt_link` requires upstream db/models.py `SuttaInfo.s_4nt_link` property (also in `local db/models.py`? verified absent at HEAD; local db/models.py is in a different domain). SBS routes use upstream `HeadwordData` (data_classes.py) so permalink arrives via that port.

---
### exporter/webapp/templates/home.html -> ru_templates/home.html and sbs_templates/home.html

1. Commits: bd036092c repoint pa auk translations link to opentipitaka; 2fac2ceca #265 favicon declared svg; 8a61998d6 google fonts via link instead of css @import; 540bdd874 styled tooltips (title -> data-title); 01cae9412 #262 how to cite docs.

2. Upstream hunks:
 a. `<head>`: add preconnect fonts.googleapis.com / fonts.gstatic.com + Google Fonts stylesheet link (Inter, Source Serif 4) before dpd.css (CSS no longer @imports fonts: dpd.css/home.css changed, 27+6 lines, see static diff; those CSS files are shared and not shadowed).
 b. `<link rel="icon" type="image/svg+xml" ...>` (was image/png).
 c. History clear button: `title="Clear history"` -> `data-title="Clear history"`.
 d. Footer: "read the docs" link gets `data-title`; new "how to cite" link; new `<span data-title="the release you are using">{{ dpd_release_version }}</span>`; GitHub link `title=` -> `data-title=`.
 e. TT footer: Pa Auk link -> `https://www.opentipitaka.org/` "OpenTipitaka".
 (dpd_release_version already passed by main_ru's home routes.)

3. Local:
 - RU: head lines 8-13 (no font links; `image/png` icon) -> PORT a, b. Clear button line 124 `title="Отчистить историю"` -> PORT c as `data-title` (keep RU text) since dpd.css tooltip styling now keys on data-title (UNCERTAIN: check static/dpd.css diff lines for `[data-title]`; `title` still works natively but loses styled tooltip). Footer lines 217-230 (RU text, own links to devamitta/dpd.rus + sasanarakkha) -> d: PORT data-title attrs (title -> data-title on github link line 224 and line 52 / 57 title attrs), SKIP "how to cite" link unless owner wants (points to upstream docs; RU has own docs) and SKIP version span only if already elsewhere (RU footer lacks it). TT footer (lines 366-370) is RU text with CST/SuttaCentral only; no Pa Auk reference -> e SKIP. 
 - SBS: head line 13 same as RU -> PORT a, b. Line 124 `title="Clear history"` -> PORT c. Footer lines 217-225 and 300-306 "read the docs" -> PORT d (data-title, how to cite, version span). Pa Auk link absent (grep) -> e: check SBS TT footer; no match found -> SKIP.
 
4. Structural refactor check: none found (attribute rename title->data-title is a UI behaviour change, tied to CSS tooltip commit 540bdd874).

5. Breakage risk: none if not updated. Font link removal from CSS (shared dpd.css/home.css pulled from upstream) means that if ru/sbs templates are NOT updated to include the Google Fonts `<link>` tags, the pages lose Inter/Source Serif 4 webfont (fallback fonts only, no crash). Same for `home_simple.html` (see below). Also old `title=` attrs would show native tooltips and no styled tooltip; cosmetic.

---
### exporter/webapp/templates/home_simple.html -> ru_templates/home_simple.html and sbs_templates/home_simple.html

1. Commits: 1d6a5db11 #264 drop unused serif import, link fonts in summary template.
2. Upstream: adds preconnect (googleapis, gstatic crossorigin) and Google Fonts stylesheet link (Inter 400;700 only) in `<head>` after `<title>`.
3. Local: both ru and sbs home_simple.html have no font links (head lines 1-10; they use `favicon.ico` link). PORT both (same 3 lines after `<title>`). Used by `/gd` (and `/sbs/gd`) for GoldenDict/MDict; CSS no longer self-imports font (home_simple.css changed upstream, shared).
4. Structural refactor: none.
5. Breakage risk: none (cosmetic font fallback).

---
### exporter/webapp/static/app.js (registered modified_upstream_files)

1. Commits: 305b33513 #277 keep browser History entries to navigation state.
2. Upstream changes: new `navigationState(source)` (allowlisted history state); `initializeApp` seeds `history.replaceState(navigationState(), ...)`; `switchTab` refetches results when `tab.needsRefetch`; new `hasActiveQuery()`, `searchURL()`; `updateURL` now pushes `navigationState()`; `handlePopState` rewritten; `clearHistory` pushes `navigationState()`.
3. Local app.js edits (git diff OLD..HEAD): language-aware search URL in `performSearch` (`/sbs/search_json` when `<html lang="en">`), language-aware `startMessage` in `render()` (en->sbs link, ru branch), a few comment/whitespace diffs. Upstream hunks are in different regions: initializeApp (after tt.language assignment), switchTab, updateURL/handlePopState, clearHistory -> a 3-way merge is expected to apply cleanly; the SBS link anchor (`sasanarakkha.github.io/study-tools/dict/sbs-pali-dictionary`) and `searchUrl` code are untouched. Verify: `updateDropdown`/`findFirstMatch` whitespace-only local edits don't conflict.
   PORT all; after merge confirm SBS dictionary link in `render()` and `/sbs/search_json` remain (registry watch_for).
   UNCERTAIN/CHECK: handlePopState refetch uses `performSearch(false)`, which uses the lang-aware URL -> OK for SBS/RU.
4. Structural refactor check: YES-ish: handlePopState rewrite, URL construction split into `searchURL()` (function extraction); no type hints applicable.
5. Breakage risk: none server-side. `precompressed` search_index.json is fetched via /static/search_index.json; app.js is unchanged for that (upstream app.js has no sidecar logic), so no JS dependence on IndexStaticFiles. Other upstream static changes (dpd.css +27, home.css/home_simple.css, tipitaka_translations.js 16 lines, logos svg, cc_icons.svg) are shared static files; `tipitaka_translations.js` change not analysed here (outside the assigned list; UNCERTAIN whether RU/SBS rely on it).

---
### tools/fast_api_utils.py -> tools/fast_api_utils_dps.py (inspired_only)

1. Commits: ee4655240 #215 gui2 web-mode multi-user groundwork; 5875fdc0e #157 tools cleanup/refactor; f5358f3fe #157 gui2 lazy managers, defer server start.
2. Upstream changes: docstring; `import os`; `from tools.server_mode import is_headless_server` (new upstream module); new `_api_port()` reading env `DPD_API_PORT` (default "8080"); `start_dpd_server() -> None` returns early if headless, drops `--reload --reload-dir` flags, uses `_api_port()`; `request_dpd_server` returns early if headless and uses `_api_port()`; `request_bold_def_server` REMOVED.
3. Shadow fast_api_utils_dps.py (44 lines): launches `main_ru:app` on 127.0.0.1:8080, redirects to `/sbs/`. sync_rule `inspired_only` -> SKIP by default (registry says do not blind-port; port split intentional). Optional/OWNER DECISION: `request_bold_def_server` removal -- check whether shadow still defines it and whether gui2 callers (gui2/dps_view.py etc.) use it (not verified; grep before any removal). `--reload` removal and headless/env-port behaviour are upstream-only multi-user features; SKIP.
4. Structural refactor check: YES - function removal (`request_bold_def_server`), return type hint added to `start_dpd_server`, helper `_api_port`. Shadow is inspired_only, so no mandatory port, but upstream gui2 callers no longer call `request_bold_def_server`.
5. Breakage risk: shadow is self-contained (does not import upstream fast_api_utils), so pulling upstream verbatim does not break it. Callers: gui2/main.py and gui2/pass2_add_view.py import from `fast_api_utils_dps` (per registry), so unaffected. Upstream gui2 files, if pulled, may no longer import `request_bold_def_server` from upstream module; if any local gui2 file imports `request_bold_def_server` from `fast_api_utils` (upstream name) it would break -> grep needed (not done; UNCERTAIN).

---
### Summary of required pull set / ordering
1. Shared infra first: tools/paths.py, tools/version.py, tools/search_deadline.py, tools/server_mode.py, tools/tipitaka_db.py, tools/bold_definitions_search.py, tools/configger.py, db/models.py (s_4nt_link), exporter/webapp/static/cc_icons.svg, precompressed_index.py, response_encoding.py, brotli dependency (pyproject/uv).
2. Then upstream data_classes.py (merge with local edits), toolkit.py, main.py, app.js (merge), static css/js.
3. Then shadow ports: main_ru.py (show_tbw global, CORS expose, license headers, take-turns middleware w/ /sbs paths, bd/tt hardening, permalink route), toolkit_ru.py (NOCASE lookup, isdecimal, dead-code removal, only_suggestions + LICENSE_HTML), data_classes_ru.py (permalink), ru/sbs templates (see sections).
4. registry.json notes may need updating if local_changes line refs drift (data_classes.py, app.js entries) and `validate_registry.py` must pass.

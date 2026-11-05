# Docs Translation Queue

Stage 1 prep (`prep_analyzer.py`) appends `docs/` paths changed in the upstream sync range to
this checklist. Drain this queue in a separate session after the code sync is stable —
translation is independent of the code sync commit gate.

## Usage

During Stage 1 prep, `prep_analyzer.py` appends each changed `docs/` path here as an unchecked item.
ADVANCED reviews and assigns a translation strategy (full translation, targeted update, or
no-translate redirect). Items are checked off as translations land.

## Pending

- [ ] docs/bibliography.md
- [ ] docs/contact.md
- [ ] docs/contributing/code.md
- [ ] docs/contributing/index.md
- [ ] docs/contributing/pali.md
- [x] docs/contributing/resources.md
- [ ] docs/features/sutta_info.md
- [x] docs/how_to_cite.md
- [ ] docs/index.md
- [x] docs/install/koreader.md
- [x] docs/integrations/add_your_app.md
- [ ] docs/integrations/dhamma_gift.md
- [x] docs/integrations/epitaka.md
- [x] docs/integrations/sutamaya.md
- [ ] docs/integrations/tpr.md
- [ ] docs/license.md
- [ ] docs/newsletters.md
- [ ] docs/other_dicts.md
- [x] docs/pics/dpdict.net/dpdict_feedback_permalink_dark.png
- [x] docs/pics/dpdict.net/dpdict_feedback_permalink_light.png
- [x] docs/pics/epitaka/lookup-phone-dark.png
- [x] docs/pics/epitaka/lookup-phone-light.png
- [x] docs/pics/epitaka/main-view-dark.png
- [x] docs/pics/epitaka/main-view-light.png
- [x] docs/pics/koreader/database_status_dark.png
- [x] docs/pics/koreader/database_status_light.png
- [x] docs/pics/koreader/database_status_menu_dark.png
- [x] docs/pics/koreader/database_status_menu_light.png
- [x] docs/pics/koreader/hero_dark.png
- [x] docs/pics/koreader/hero_light.png
- [x] docs/pics/koreader/lookup_dark.png
- [x] docs/pics/koreader/lookup_light.png
- [x] docs/pics/koreader/main_dark.png
- [x] docs/pics/koreader/main_light.png
- [ ] docs/pics/newsletters/055d6c99f31c.jpg
- [ ] docs/pics/newsletters/2026-10/epitaka-android.png
- [ ] docs/pics/newsletters/2026-10/epitaka-app.jpg
- [ ] docs/pics/newsletters/38dec4f8be4b.jpg
- [ ] docs/pics/newsletters/4e4cf3b3d2f6.jpg
- [ ] docs/pics/newsletters/983c769bb4d2.jpg
- [ ] docs/pics/newsletters/c957ad0fd41a.jpg
- [ ] docs/pics/newsletters/cfc409b522d4.jpg
- [ ] docs/pics/newsletters/d9fdfd5353b9.jpg
- [ ] docs/pics/newsletters/e0a09c53d3e5.jpg
- [x] docs/pics/sutamaya/library-phone-dark.png
- [x] docs/pics/sutamaya/library-phone-light.png
- [x] docs/pics/sutamaya/lookup-phone-dark.png
- [x] docs/pics/sutamaya/lookup-phone-light.png
- [x] docs/pics/sutamaya/settings-dark.png
- [x] docs/pics/sutamaya/settings-light.png
- [ ] docs/technical/api_endpoints.md
- [ ] docs/technical/project_folder_structure.md
- [ ] docs/technical/style_guide_for_dpd_entries.md
- [ ] docs/technical/tipitaka_source_files.md
- [ ] docs/technical/local_server_setup.md
- [ ] docs/technical/quick_start.md
- [ ] docs/technical/use_db.md
<!-- Stage 1 prep appends items here, e.g.:
- [ ] docs/changelog.md  (no-translate — mostly Pali data; use redirect pattern)
- [ ] docs/technical/dpd_headwords_table.md  (full translation needed)
-->

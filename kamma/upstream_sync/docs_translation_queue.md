# Docs Translation Queue

Stage 1 prep (`prep_analyzer.py`) appends `docs/` paths changed in the upstream sync range to
this checklist. Drain this queue in a separate session after the code sync is stable —
translation is independent of the code sync commit gate.

## Usage

During Stage 1 prep, `prep_analyzer.py` appends each changed `docs/` path here as an unchecked item.
ADVANCED reviews and assigns a translation strategy (full translation, targeted update, or
no-translate redirect). Items are checked off as translations land.

## Pending

- [x] docs/bibliography.md
- [x] docs/contact.md
- [x] docs/contributing/code.md
- [x] docs/contributing/index.md
- [x] docs/contributing/pali.md
- [x] docs/contributing/resources.md
- [x] docs/features/sutta_info.md
- [x] docs/how_to_cite.md
- [x] docs/index.md
- [x] docs/install/koreader.md
- [x] docs/integrations/add_your_app.md
- [x] docs/integrations/dhamma_gift.md
- [x] docs/integrations/epitaka.md
- [x] docs/integrations/sutamaya.md
- [x] docs/integrations/tpr.md
- [x] docs/license.md
- [x] docs/newsletters.md
- [x] docs/other_dicts.md
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
- [x] docs/pics/newsletters/055d6c99f31c.jpg
- [x] docs/pics/newsletters/2026-10/epitaka-android.png
- [x] docs/pics/newsletters/2026-10/epitaka-app.jpg
- [x] docs/pics/newsletters/38dec4f8be4b.jpg
- [x] docs/pics/newsletters/4e4cf3b3d2f6.jpg
- [x] docs/pics/newsletters/983c769bb4d2.jpg
- [x] docs/pics/newsletters/c957ad0fd41a.jpg
- [x] docs/pics/newsletters/cfc409b522d4.jpg
- [x] docs/pics/newsletters/d9fdfd5353b9.jpg
- [x] docs/pics/newsletters/e0a09c53d3e5.jpg
- [x] docs/pics/sutamaya/library-phone-dark.png
- [x] docs/pics/sutamaya/library-phone-light.png
- [x] docs/pics/sutamaya/lookup-phone-dark.png
- [x] docs/pics/sutamaya/lookup-phone-light.png
- [x] docs/pics/sutamaya/settings-dark.png
- [x] docs/pics/sutamaya/settings-light.png
- [x] docs/technical/api_endpoints.md
- [x] docs/technical/project_folder_structure.md
- [x] docs/technical/style_guide_for_dpd_entries.md
- [x] docs/technical/tipitaka_source_files.md
- [x] docs/technical/local_server_setup.md
- [x] docs/technical/quick_start.md
- [x] docs/technical/use_db.md
<!-- Stage 1 prep appends items here, e.g.:
- [x] docs/changelog.md  (no-translate — mostly Pali data; use redirect pattern)
- [x] docs/technical/dpd_headwords_table.md  (full translation needed)
-->

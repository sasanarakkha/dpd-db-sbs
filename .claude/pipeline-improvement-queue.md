# Pipeline Improvement Queue

Pointer: 70

## Scripts (76 total, local unique_paths)

### db/families

- [x] 1. db/families/family_set_ru_update.py

### gui2

- [x] 2. gui2/dps_ai_service.py
- [x] 3. gui2/dps_db_helpers.py
- [>] 4. gui2/dps_field_mapping.py
- [x] 5. gui2/dps_process_additions.py
- [x] 6. gui2/dps_process_corrections.py

### scripts/change_in_db

- [x] 8. scripts/change_in_db/add_row_to_table.py
- [x] 9. scripts/change_in_db/apply_all_additions.py
- [x] 10. scripts/change_in_db/apply_all_corrections.py
- [x] 11. scripts/change_in_db/change_in_db.py
- [x] 12. scripts/change_in_db/class_relation.py
- [x] 13. scripts/change_in_db/copy_examples.py
- [x] 14. scripts/change_in_db/copy_ru_meaning_raw_to_ru_meaning.py
- [x] 15. scripts/change_in_db/fill_dhp_examples.py
- [x] 16. scripts/change_in_db/preview_dhp_changes.py
- [x] 17. scripts/change_in_db/replace_in_db.py
- [x] 18. scripts/change_in_db/sbs_class_sutta_linker.py
- [x] 19. scripts/change_in_db/dhp_examples_copy.py
- [x] 20. scripts/change_in_db/source_cleanup.py
- [x] 21. scripts/change_in_db/update_examples_from_csv.py
- [x] 22. scripts/change_in_db/update_ru_db_from_csv.py
- [x] 23. scripts/change_in_db/update_sbs_chants_in_db.py
- [x] 24. scripts/change_in_db/update_yojana_km.py
- [x] 25. scripts/change_in_db/vib_rule_workflow.py

### scripts/export

- [x] 26. scripts/export/sbs_anki_updater.py
- [x] 27. scripts/export/sbs_anki_apkg.py
- [x] 28. scripts/export/sbs_anki_deck_config.py
- [x] 29. scripts/export/sbs_anki_collection_verifier.py
- [x] 30. scripts/export/sbs_anki_revert.py

### scripts/moving

- [x] 31. scripts/moving/copy_dpd_for_classes.py
- [x] 32. scripts/moving/copy_dpdsbs_from_sbs2filesrv.py — unified into distribute.py
- [x] 33. scripts/moving/copy_dpdsbs_from_share2sbs.py — unified into distribute.py
- [x] 34. scripts/moving/copy_rudpd_from_share2filesrv.py — unified into distribute.py
- [x] 35. scripts/moving/move_mdict.py — unified into distribute.py
- [x] 36. scripts/moving/move_mdict_ru.py — unified into distribute.py
- [x] 37. scripts/moving/unzip_classes_to_filesrv.py — unified into distribute.py
- [x] 38. scripts/moving/unzip_dpd_sbs_to_filesrv.py — unified into distribute.py
- [x] 39. scripts/moving/unzip_dpd_to_filesrv.py — unified into distribute.py
- [x] 40. scripts/moving/unzip_dpd_to_gd.py — unified into distribute.py
- [x] 41. scripts/moving/unzip_dpd_to_share.py — unified into distribute.py
- [x] 42. scripts/moving/unzip_rudpd_to_filesrv.py — unified into distribute.py

### scripts/other

- [x] 43. scripts/other/add_combined_view.py
- [x] 44. scripts/other/ai_batch_api.py — renamed to ai_batch_openai_meaning.py
- [x] 45. scripts/other/ai_batch_deepseek_meaning.py — archived
- [x] 46. scripts/other/ai_check_russian_meanings.py
- [x] 47. scripts/other/ai_generate_translation.py
- [x] 48. scripts/other/ai_individual_word_ru.py — archived
- [x] 49. scripts/other/ai_sentences_extracting.py — archived
- [x] 50. scripts/other/ai_translate_evaluator.py — archived
- [x] 51. scripts/other/backup_corrections_additions.py — archived (already in scripts/dps_archive/, queue was stale)
- [x] 52. scripts/other/extract_id_from_docs.py — archived
- [x] 53. scripts/other/extract_sentences_from_sc_db.py — archived
- [x] 54. scripts/other/replace_sandhi_txt.py
- [x] 55. scripts/other/tpr_db_tester.py — archived
- [x] 56. scripts/other/uppickle_and_edit.py | archived

### scripts/work_with_csv

- [x] 57. scripts/work_with_csv/additions_processor.py
- [x] 58. scripts/work_with_csv/anki_class_grammar.py
- [x] 59. scripts/work_with_csv/check_class_data.py — already archived (commit ec21b027e), queue was stale
- [x] 60. scripts/work_with_csv/compare_changed_id.py — already archived (commit ec21b027e), queue was stale
- [x] 61. scripts/work_with_csv/filter_one_list_from_another.py — already archived (commit ec21b027e), queue was stale
- [x] 62. scripts/work_with_csv/pat_for_anki.py
- [x] 63. scripts/work_with_csv/replace_new_id.py
- [x] 64. scripts/work_with_csv/xlsx2csv.py

### tools

- [x] 65. tools/ai_batch_processor.py
- [x] 66. tools/ai_json_parser.py
- [x] 67. tools/ai_llm_factory.py — archived
- [x] 68. tools/ai_meaning_checker.py
- [x] 69. tools/ai_openai_manager.py — archived
- [ ] 70. tools/ai_related.py
- [ ] 71. tools/ask.py
- [ ] 72. tools/deepseek.py
- [ ] 73. tools/duplicates.py
- [ ] 74. tools/file_utils.py
- [ ] 75. tools/sbs_table_functions.py
- [ ] 76. tools/tools_for_ru_exporter.py

---

## Decisions log

<!-- Format: YYYY-MM-DD | #N script | passed / changed / skipped / deferred | note -->
2026-06-07 | #1 db/families/family_set_ru_update.py | changed | compiled regex to module constants, extracted _clean_translated_lines helper, atomic TSV write, -> None annotation, removed stale comments
2026-06-07 | #2 gui2/dps_ai_service.py | changed | type hints (TYPE_CHECKING guard for DpsFields, DpdHeadword), lemma_1 or "" guard, textwrap.dedent on both prompt f-strings, synonyms via instruction var not .replace(), str(e)->e, removed WHAT comments
2026-06-07 | #3 gui2/dps_db_helpers.py | changed | Optional[X] → X | None, removed typing.Optional import, removed coding header, inlined multi-line filter() calls
2026-06-08 | #4 gui2/dps_field_mapping.py | deferred | GUI work in progress on this file; revisit when done
2026-06-08 | #5 gui2/dps_process_additions.py | changed | print()->pr.*, main()->None, encoding='utf-8' on open(), sorted(list())->sorted(), save guard try/except OSError, remove WHAT-comments
2026-06-08 | #6 gui2/dps_process_corrections.py | changed | print()->pr.*, encoding='utf-8' on open(), try/except OSError on write, sorted(processed_ids) redundant cast, set[int]/list[int] type hints, remove WHAT-comments
2026-06-08 | #8 scripts/change_in_db/add_row_to_table.py | changed | console: Console param → pr.*, Literal["SBS","Russian"] type, id str→int, sa_inspect for column validation, dead elif/else removed, WHAT comments removed, __main__-only imports moved inside block
2026-06-08 | #9 scripts/change_in_db/apply_all_additions.py | changed | removed dead load_id_map_from_additions_added + process_additions_added_and_update_tsvs (TODO resolved), print()→pr.green() summary, process_file Path arg, ==ebt_count, ->None on all functions
2026-06-08 | #10 scripts/change_in_db/apply_all_corrections.py | changed | print()×4→pr.green() in summary, fields_updated_log→any_changed bool, encoding="utf-8" on open(), ->None on both functions, WHAT comment removed
2026-06-08 | #11 scripts/change_in_db/change_in_db.py | changed | console→pr.*, type[Any]+str hints, fix filter_and_add .key bug, fix update_notes None TypeError, __word__→word, drop unused counter, remove dead update_sbs_source_2 block, numbered menu in __main__
2026-06-08 | #12 scripts/change_in_db/class_relation.py | changed | console→pr.*, Optional→int|None, word: DpdHeadword type hint, hoist 8 module-level constants, remove ~60 commented-out prints, fix word.sbs guard in filling_sbs_class, simplify debug if/if/if→if/else, remove int() wraps, deduplicate cons set, __main__ guard
2026-06-09 | #13 scripts/change_in_db/copy_examples.py | changed | extract _copy_dpd_fields() helper, _SOURCE_FIELDS constant, remove commented-out sbs_source_3/4, drop redundant or_() single-pred, __word__→word, remove 8 WHAT comments, fix module docstring
2026-06-09 | #14 scripts/change_in_db/copy_ru_meaning_raw_to_ru_meaning.py | changed | remove Console import, add Path/Session types, extract _LITERAL_SEP/_CHUNK_SIZE constants, batch N+1→chunked .in_() query, remove remove_duplicates() helper, drop dead else branch, remove WHAT/stale comments, fix redundant markup in pr calls, fix unbound id_file_path in except
2026-06-09 | #15 scripts/change_in_db/fill_dhp_examples.py | passed | clean — follows all conventions, pr.* output, Path, modern type hints, no dead code
2026-06-09 | #16 scripts/change_in_db/preview_dhp_changes.py | changed | TypedDicts (InputVerse/AnalysisOption/TokenAnalysis/VerseAnalysis/ProposedChange), decompose main() into 4 sub-functions, cast at external dict[str,Any] boundaries, json.loads(path.read_text()), report_path.write_text(), remove 6 WHAT-comments; 8 golden-master tests added
2026-06-09 | #17 scripts/change_in_db/replace_in_db.py | changed | removed generic filter_and_replace(InstrumentedAttribute, ...) → hardcoded main(); fixed crash (SBS.sbs_example_4 never existed → sbs_example_1); re.sub→str.replace; Console/print()→pr.*; ->None; __main__ guard; db_session.close(); 6 golden-master tests added
2026-06-09 | #18 scripts/change_in_db/sbs_class_sutta_linker.py | changed | one-time job already done — moved to scripts/dps_archive/
2026-06-09 | #19 scripts/change_in_db/dhp_examples_copy.py | changed | module-level DB → inside dhp(), remove unused Russian join, fix outerjoin+joinedload conflict (eliminates dedup block), remove N+1 in-loop SBS query, extract _find_dhp_source_idx() helper, unify two duplicate branches, rich print→pr.*, setattr→direct, compile regex
2026-06-09 | #20 scripts/change_in_db/source_cleanup.py | changed | list[str]→tuple[str,...] for SOURCE_FIELDS and EXEMPTS, add db_session.close()
2026-06-14 | #21 scripts/change_in_db/update_examples_from_csv.py | passed | already archived to scripts/dps_archive/ before review cycle reached it — unfinished script with placeholder "suttas" mode, not in registry
2026-06-14 | #22 scripts/change_in_db/update_ru_db_from_csv.py | changed | not in use — moved to scripts/dps_archive/ via git mv
2026-06-14 | #23 scripts/change_in_db/update_sbs_chants_in_db.py | changed | query SBS directly (drop DpdHeadword+joinedload), remove dead guard, rename result→found, extract attr vars, remove or "" redundancy, explicit None checks, type annotations
2026-06-14 | #24 scripts/change_in_db/update_yojana_km.py | changed | collapse dead if/else in Phase 2 printing, add re.Match[str]/->str type hints to 4 closure callbacks; golden-master tests added (5 tests, 28+50+54+32 fixture cases); word2number approach rejected — returns wrong value for "one million one hundred and seventy-six thousand" (1176001 vs 1176000)
2026-06-14 | #25 scripts/change_in_db/vib_rule_workflow.py | changed | dict[str, Any] return type, Session annotation on db_session, Path.stem+re.match in suggest_next_pat_file, encoding='utf-8' on 5 read/write_text calls, short-circuit GUI pause when words list is empty; 20 tests added
2026-06-14 | #26 scripts/export/sbs_anki_updater.py | changed | os→pathlib (4 places, drop os import), datetime to module level, Note/DpdHeadword type hints on update_note_values, dict[str,Any] on row param, type params on all bare dict/list signatures, deck_selector dedup→dict.fromkeys; 22 tests added
2026-06-15 | #27 scripts/export/sbs_anki_apkg.py | changed | os→pathlib: makedirs→mkdir, path.join→/, exportInto(str(path))
2026-06-15 | #28 scripts/export/sbs_anki_deck_config.py | changed | _to_br() helper, _SBS_TOOLS singleton, _base_db_fields() factory (1233→885 lines), str(root_group) type fix, meaning_1 or meaning_2, type annotations; 36 golden-master tests added
2026-06-16 | #29 scripts/export/sbs_anki_collection_verifier.py | changed | JSON snapshot (sbs_anki_schema_snapshot.json) replaces Python-dict EXPECTED_COLLECTION (~470 lines removed from deck_config), extract _find_mismatches() helper, fix silent field-reorder bug, remove os/rich.print, pathlib+pr.*, generate_report() dumps JSON; 7 tests added
2026-06-18 | #30 scripts/export/sbs_anki_revert.py | changed | reviewer cross-check skipped (gemini-3.1-pro-preview and gemini-2.5-pro both QUOTA_EXHAUSTED, ~19h reset) — proceeded on explicit user approval; main()->None; pre-commit gate forced fixing 2 pre-existing findings: chmod +x (EXE001 shebang-not-executable), except Exception->except OSError (BLE001); same EXE001/BLE001 pattern confirmed present in already-passed #29, out of scope to retrofit there
2026-06-18 | #31 scripts/moving/copy_dpd_for_classes.py | changed | Path.cwd()->Path(__file__).resolve() anchoring fix, print()->pr.yellow_title/green/red, extracted safe_copy() helper (user-requested: catch OSError per-copy and print red on failure instead of crashing), main()+__main__ guard, module docstring; 5 tests added (tests/scripts/moving/test_copy_dpd_for_classes.py); live smoke test hit expected sys.exit(1) early-exit path (dest network share not mounted on this machine) — confirms path anchoring correct, matches old behavior
2026-06-18 | #32-42 scripts/moving/{unzip,copy,move}_*.py | changed | user-requested unification — all 11 highly-duplicated unzip/copy/move scripts merged into single scripts/moving/distribute.py with shared primitives (_unzip/_copy_file/_copy_tree/_move_file/_copy_pair/_require_dirs) and one task function per old script, dispatched via argparse `task` positional; Path.cwd()->Path(__file__).resolve() anchoring fix applied to all; raw ANSI prints->pr.*; 4 bash callers updated (push_dpd.sh x5, make_dpd.sh x2, make_ru_dpd.sh, update_decks.sh); 10 old files git rm'd, copy_dpd_for_classes.py (#31) intentionally excluded (DB+bash-script copy, not zip/dict distribution); 24 tests added (tests/scripts/moving/test_distribute.py), all real-filesystem/tmp_path, no mocks; live smoke test of unzip_dpd_to_filesrv actually ran against the real mounted fileserver share (network share was mounted, unlike #31) — extracted real dpd-goldendict.zip/dpd-mdict.zip into production Golden Dictionary/MDict folders; user confirmed this was the intended current build and caused no problem; registry.json/SMD required no update since scripts/moving/ is tracked as a directory wildcard
2026-06-18 | #43 scripts/other/add_combined_view.py | changed | approve all — moved pth/engine from module scope into main(), rich.Console->pr.yellow_title(), main()->None, replaced 80 hand-written COALESCE(...) AS lines with (table,column,alias) data list + _build_select_clause() generator (reviewer's logging+Dict/List/Tuple suggestion rejected, kept pr.* and modern hints); 3 tests added against fixture mechanically regex-extracted from the original SQL (golden master); live run confirmed 80 columns, same order, in real dpd.db
2026-06-18 | #44 scripts/other/ai_batch_api.py | changed | user-requested rename to ai_batch_openai_meaning.py + consolidation into single run_batch_workflow() (upload->poll->save to db); _get_openai_client() isinstance-based helper replaces 6x duplicated client-validation + nested _openai_* functions; upload_and_create_batch returns batch_id; check_batch_status typed Batch|None; id->record_id (builtin shadow fix); simplified dead skip_empty branch; pre-commit forced chmod+x (EXE001) + narrowed 6 blind except Exception->openai.OpenAIError/OSError/(TypeError,AttributeError) (BLE001); reviewer's BatchProcessor dataclass/class redesign rejected as out of scope; 1 test added (serialize_request_counts — only network-free pure function); live run skipped by user choice (would create real billed OpenAI batch job)
2026-06-18 | #45 scripts/other/ai_batch_deepseek_meaning.py | archived | broken — depends on langchain_deepseek, which is not installed/declared anywhere in pyproject.toml, so the module cannot import; functionality (RU meaning+notes translation, lang=ru) is already fully covered by scripts/other/ai_generate_translation.py (mode=meaning/note) via AIManager, which already lists deepseek as a configured provider in tools/ai_models.json; only unique trait was concurrent batch dispatch via LangChain's RunnableMap.batch(), but DeepSeek has no real async Batch API (unlike OpenAI's /v1/batches used in #44) so that's just client-side concurrency, generically addable to ai_generate_translation.py later if wanted, not unique to this file; also silently discarded the ru_example_raw field it asked the LLM to produce — moved to archive/ai_batch_deepseek_meaning.py
2026-06-18 | #46 scripts/other/ai_check_russian_meanings.py | changed | moved pth/db_session module-level globals into main() (side-effect-free imports), main()->None, fixed import order, removed dead --output arg (parsed but never used) and dead --individual flag (user-confirmed: no caller anywhere passes it; use_batch simplified to args.batch), replaced 8-branch if-elif mode-message chain with _MODE_NOTES dict lookup, except Exception # noqa: BLE001 (top-level CLI boundary, same pattern as #29/#30/#44), pre-commit forced chmod +x (EXE001); 4 tests added for _MODE_NOTES (only pure logic in this CLI wrapper — rest is DB/argparse/AI plumbing delegated to tools/ai_meaning_checker.py, queued separately as #68); tools/ai_meaning_checker.py itself untouched (out of scope, reviewed when #68 comes up); live run (--limit 1 --no-auto-invalidate) completed successfully against real dpd.db and a live AI call, report written to configured temp/ai_meaning_check/ output dir
2026-06-18 | #47 scripts/other/ai_generate_translation.py | changed | print()->pr.* (19 sites), os.path.join/glob.glob->pathlib (drop os/glob imports), module globals provider/model renamed to default_provider/default_model removing globals()["model"] anti-pattern (collided with same-named function params), id->word_id builtin shadow in read_exclude_ids_from_tsv; note-mode in translation_generate now creates missing Russian row instead of crashing on word.ru.ru_notes (if->elif for consistency with meaning/lit) — caveat: every row in the live DB already has a Russian row so this guard is currently unreachable, defensive only; PIPELINE_CONFIG/strategy-pattern rewrite (reviewer suggestion) and module-level db_session/main() wrapping (pattern from #43/#44/#46) both rejected as too invasive given db_session is read at module scope by many functions, not just __main__; read_exclude_ids_from_json's unused mode/lang params left as-is — fixing the glob pattern would break existing tests/test_tamil_translation.py which uses arbitrary filenames, and the function isn't wired into the main flow anyway; existing tests/test_tamil_translation.py (10 tests, pre-existing from the Tamil thread) re-verified passing, no new test added (note-mode fix isn't testable without mocking the AI call, against project no-mocks rule); live smoke test of all mode/lang/--remove/--json --dry-run combos clean; live run (--mode note --limit 1, real AI call, user-approved) succeeded, wrote real Russian note to dpd.db
2026-06-18 | #48 scripts/other/ai_individual_word_ru.py | archived | single-word interactive CLI superseded by ai_generate_translation.py
2026-06-18 | #49 scripts/other/ai_sentences_extracting.py | archived | standalone AI sentence extraction script; user chose archive over review (batch + same modes); not unique enough to keep in active path
2026-06-18 | #50 scripts/other/ai_translate_evaluator.py | archived | evaluation harness for manual model comparison — not a recurring workflow, can re-run ad-hoc via ai_generate_translation.py if needed
2026-06-18 | #51 scripts/other/backup_corrections_additions.py | archived | already in scripts/dps_archive/, queue was stale — fixed
2026-06-18 | #52 scripts/other/extract_id_from_docs.py | archived | buggy (writes ids instead of unique_ids) — user chose archive over fix
2026-06-18 | #53 scripts/other/extract_sentences_from_sc_db.py | archived | user chose archive over improvement
2026-06-18 | #54 scripts/other/replace_sandhi_txt.py | archived | already in scripts/dps_archive/ — queue was stale
2026-06-18 | #55 scripts/other/tpr_db_tester.py | archived | standalone TPR HTML validation utility — not referenced by any workflow or caller; ad-hoc manual QA tool only
2026-06-18 | #56 scripts/other/uppickle_and_edit.py | archived | broken (references non-existent DPSPaths.dps_save_state_path), functionally inert (edit/save code commented out), no callers
2026-06-19 | #57 scripts/work_with_csv/additions_processor.py | changed | fixed real bug — replace_ids_in_tsv was substring-matching id_add against the WHOLE line instead of the first (id) column, so an id_add digit-string could silently corrupt unrelated numeric content in other columns (e.g. id_add "408" colliding with sutta ref "DHP408"); fixed to match only column 0, same pattern as apply_all_additions.py's replace_old_ids_in_tsv_files (#9); Dict/Set->dict/set, open()->Path.read_text/write_text, print()->pr.*, set(.keys())->set(); duplication with #9's TSV-replace logic noted but not extracted (would require editing #9, out of scope); 6 tests added (tests/scripts/work_with_csv/test_additions_processor.py), one of which fails against the pre-fix code on purpose to document the bug, then passes after the fix; live run against real db/backup_tsv/{sbs,russian}.tsv confirmed no-op (all current additions already marked processed) with zero file diffs
2026-06-19 | #58 scripts/work_with_csv/anki_class_grammar.py | changed | fixed real bug: current_date/current_date_year computed at module-import time not run time; moved DPSPaths/ProjectPaths instantiation (which create dirs on init) out of module scope into main(); removed dead commented-out moving_grammar() call; print()->pr.amber/pr.white, extracted _warn_invalid_sheet/_write_field_list helpers (deduplicated 3 near-identical open()-write blocks); check_duplicate_ids dict-as-set->set; fixed B023 lambda-closure bug (second_column_name captured by reference, bound via default-arg); type hints throughout; reviewer's SHEET_CATEGORIES data-driven redesign and full make_grammar_csvs decomposition rejected as too invasive (strict parity); 2 tests added (tests/scripts/work_with_csv/test_anki_class_grammar.py, synthetic xlsx fixture, no mocks); live run against real downloaded grammar.xlsx (via scripts/bash/download_grammar.sh) succeeded - 286/713/1321 rows across the three output CSVs, exit 0
2026-06-19 | #59 scripts/work_with_csv/check_class_data.py | archived | file already moved to scripts/dps_archive/ in commit ec21b027e, not in registry.json — queue entry was stale, no review needed
2026-06-19 | #60 scripts/work_with_csv/compare_changed_id.py | archived | same as #59, already archived in commit ec21b027e — queue was stale
2026-06-19 | #61 scripts/work_with_csv/filter_one_list_from_another.py | archived | same as #59, already archived in commit ec21b027e — queue was stale
2026-06-19 | #62 scripts/work_with_csv/pat_for_anki.py | changed | approve all
2026-06-19 | #63 scripts/work_with_csv/replace_new_id.py | archived | stale — no active callers, functionality covered by additions_processor.py (#57) and apply_all_additions.py (#9) — found and fixed 2 real pandas-3.0 incompatibilities discovered while building golden-master fixtures: (1) df.iloc[:,0]=...astype(str) in-place mutation raised LossySetitemError/TypeError whenever the flag column was numeric-inferred; (2) df_processed.loc[:,"test"]=scalar raised ValueError on a zero-row DataFrame; root-caused both to pd.read_csv inferring int64/float64 on the numeric-looking first column, fixed at the source via dtype=str+keep_default_na=False rather than patching downstream (also fixes a third, silent bug this exposed: "1.0" != "1" meant the filter matched zero rows whenever the column was numeric, even before the crash); restructure: extracted _filter_input_rows/_build_feedback_column/_build_web_link_column/_write_field_list helpers, df.reindex(columns=COLUMNS_TO_KEEP, fill_value="") replaces manual per-column copy loop, single datetime.now().astimezone() replaces 3x datetime.today() calls (DTZ002, race-condition risk); BLE001 narrowed to (ParserError,OSError,UnicodeDecodeError/KeyError) per call site; removed one redundant cast(dict[str,str], dict(zip(...))) (verified via pyright), kept cast(Any, source_to_link) for pandas-stubs .map() and 2x cast(pd.Series, ...) for pandas-stubs .apply() ambiguity (pyright requires these, pyrefly calls them "redundant" — user approved keeping per project's "approve pyrefly warnings" exception); chmod +x (EXE001), import sort, encoding="utf-8" on open(); 8 tests added (tests/scripts/work_with_csv/test_pat_for_anki.py + fixtures.json), 5 golden-master against unedited code + 3 literal new-behavior cases documenting where old code crashed; live run against realistic numeric-flag-column input + real shared_data/sbs_csvs/pat_links.tsv succeeded, field-list-pat.md regenerated byte-identical in sibling study-tools repo
2026-06-19 | #64 scripts/work_with_csv/xlsx2csv.py | changed | console (rich)->pr.red/green/amber; Union[Font,None]->Font|None with cast() for openpyxl StyleProxy/MergedCell stub mismatches; narrowed 3 blanket except Exception to specific exceptions per call site (OSError/KeyError/ValueError on load, ValueError/AttributeError per-row, OSError on write); removed stale WHAT-comments; open()->Path.open(); reviewer's "dead elif isinstance(part,str)" claim disproven by fixture (mixed bold/plain rich text needs it) and its raise-SystemExit restructuring rejected as a behavior change; 4 golden-master tests added (tests/scripts/work_with_csv/test_xlsx2csv.py); live run via temp synthetic xlsx succeeded, exit 0, byte-correct output
2026-06-20 | #65 tools/ai_batch_processor.py | changed | List/Optional->list/X|None, print()->pr.*, removed stray debug print(prompt); deleted mark_as_checked_safe (try/except around set.add() that can't raise, callers ignored its return value) -> checked_ids.add() inline; deduped ComparisonResult construction across process_batch_results/parse_ai_response into new _comparison_result_from_dict() helper reusing extract_headword_id; removed unused batch_size param from process_batch_results; extracted _log_parse_failure() helper (was duplicated twice verbatim); fixed latent UnboundLocalError on `i`/`batch_num` in compare_meanings_batch's finally block when comparisons is empty (init i=0/batch_num=0 before loop); moved signal/re imports to module top; reviewer's Strategy-pattern/Enum/TypedDict rewrite of create_comparison_prompt rejected as too invasive (matches prior #43/#47/#58 precedent against redesigns); no entry point - live run not applicable; 16 tests added (tests/tools/test_ai_batch_processor.py) covering extract_headword_id, _comparison_result_from_dict, process_batch_results, create_comparison_prompt (3 modes), parse_ai_response (JSON + manual fallback); confirmed no external callers of removed/changed signatures (tools/ai_meaning_checker.py only calls compare_meanings_batch/compare_meanings_individual, unaffected)
2026-06-20 | #66 tools/ai_json_parser.py | changed | Optional[str]->str|None, print()->pr.green() (5 sites), narrowed 3 overly-broad except clauses (1x tuple incl. redundant Exception, 2x bare Exception) to except json.JSONDecodeError (only raise source in each block, traced); user explicitly asked about genericizing beyond the "comparisons" schema, recommended against it (single caller, no second use case to design against) and user agreed; reviewer's from-scratch ~50-line rewrite rejected (risks silently dropping recovery paths for real AI-output malformations this code was built to handle, no way to verify against original failure cases); no entry point - live run not applicable; 13 tests added (tests/tools/test_ai_json_parser.py), no fixture file (pure string logic, no DB dependency), captured green against unedited source first per protocol
2026-06-20 | #67 tools/ai_llm_factory.py | archived | broken (unimportable) — depends on langchain_deepseek, not installed/declared anywhere in pyproject.toml (no langchain deps at all); only caller was scripts/dps_archive/ai_sentences_extracting.py, itself already archived in #49; functionality (LangChain-based OpenAI/DeepSeek chat wrapper + batch_processing via RunnableMap) fully superseded by tools/ai_manager.py's AIManager; same pattern as #45 (ai_batch_deepseek_meaning.py); moved to archive/ai_llm_factory.py via git mv; removed tools/ai_llm_factory.py line from registry.json unique_paths (no SMD entry existed for it); validate_registry.py and verify_smd_coverage.py both pass
2026-06-20 | #68 tools/ai_meaning_checker.py | changed | List/Optional->list/X|None, print()->pr.*, os.path/os.makedirs->pathlib; removed module-level db_session creation at import time (side-effect-free imports) -- db_session now only created in __main__ block; run_analysis() now requires explicit db_session param (only real caller, ai_check_russian_meanings.py #46, already always passed one) -- removes globals()["db_session"] fallback antipattern; removed dead mark_as_checked() (zero callers anywhere, confirmed via grep); deduplicated clean_ru_meaning_raw_for_mismatches/clean_ru_notes_for_mismatches into _clean_field_for_mismatches() helper; except Exception->except OSError on save_checked_ids + clean loop; reviewer's Strategy-pattern/Enum/ModeConfig rewrite of the 8-mode if-elif chains rejected as too invasive (same precedent as #43/#47/#58/#65); 11 golden-master tests added (tests/tools/test_ai_meaning_checker.py), captured against unedited code first per protocol, covering all 8 modes + load_list_ids + unknown-mode ValueError; live run (--mode meaning --limit 1 --no-auto-invalidate) succeeded against real dpd.db with a live AI call, report written and content verified byte-identical in format to pre-refactor output
2026-06-20 | #69 tools/ai_openai_manager.py | archived | direct-OpenAI-SDK wrapper class, zero callers anywhere in repo (grep across .py/.json/.md); AIManager routes all OpenAI-model requests through tools/ai_open_router.py's OpenRouterManager instead, confirmed no import of this module from ai_manager.py; superseded, same pattern as #45/#48/#49/#50/#67; moved to archive/ai_openai_manager.py via git mv; removed tools/ai_openai_manager.py line from registry.json unique_paths (no SMD entry existed for it, same as #67); validate_registry.py and verify_smd_coverage.py both pass

# Pipeline Improvement Queue

Pointer: 25

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
- [ ] 25. scripts/change_in_db/vib_rule_workflow.py

### scripts/export

- [ ] 26. scripts/export/sbs_anki_updater.py
- [ ] 27. scripts/export/sbs_anki_apkg.py
- [ ] 28. scripts/export/sbs_anki_deck_config.py
- [ ] 29. scripts/export/sbs_anki_collection_verifier.py
- [ ] 30. scripts/export/sbs_anki_revert.py

### scripts/moving

- [ ] 31. scripts/moving/copy_dpd_for_classes.py
- [ ] 32. scripts/moving/copy_dpdsbs_from_sbs2filesrv.py
- [ ] 33. scripts/moving/copy_dpdsbs_from_share2sbs.py
- [ ] 34. scripts/moving/copy_rudpd_from_share2filesrv.py
- [ ] 35. scripts/moving/move_mdict.py
- [ ] 36. scripts/moving/move_mdict_ru.py
- [ ] 37. scripts/moving/unzip_classes_to_filesrv.py
- [ ] 38. scripts/moving/unzip_dpd_sbs_to_filesrv.py
- [ ] 39. scripts/moving/unzip_dpd_to_filesrv.py
- [ ] 40. scripts/moving/unzip_dpd_to_gd.py
- [ ] 41. scripts/moving/unzip_dpd_to_share.py
- [ ] 42. scripts/moving/unzip_rudpd_to_filesrv.py

### scripts/other

- [ ] 43. scripts/other/add_combined_view.py
- [ ] 44. scripts/other/ai_batch_api.py
- [ ] 45. scripts/other/ai_batch_deepseek_meaning.py
- [ ] 46. scripts/other/ai_check_russian_meanings.py
- [ ] 47. scripts/other/ai_generate_translation.py
- [ ] 48. scripts/other/ai_individual_word_ru.py
- [ ] 49. scripts/other/ai_sentences_extracting.py
- [ ] 50. scripts/other/ai_translate_evaluator.py
- [ ] 51. scripts/other/backup_corrections_additions.py
- [ ] 52. scripts/other/extract_id_from_docs.py
- [ ] 53. scripts/other/extract_sentences_from_sc_db.py
- [ ] 54. scripts/other/replace_sandhi_txt.py
- [ ] 55. scripts/other/tpr_db_tester.py
- [ ] 56. scripts/other/uppickle_and_edit.py

### scripts/work_with_csv

- [ ] 57. scripts/work_with_csv/additions_processor.py
- [ ] 58. scripts/work_with_csv/anki_class_grammar.py
- [ ] 59. scripts/work_with_csv/check_class_data.py
- [ ] 60. scripts/work_with_csv/compare_changed_id.py
- [ ] 61. scripts/work_with_csv/filter_one_list_from_another.py
- [ ] 62. scripts/work_with_csv/pat_for_anki.py
- [ ] 63. scripts/work_with_csv/replace_new_id.py
- [ ] 64. scripts/work_with_csv/xlsx2csv.py

### tools

- [ ] 65. tools/ai_batch_processor.py
- [ ] 66. tools/ai_json_parser.py
- [ ] 67. tools/ai_llm_factory.py
- [ ] 68. tools/ai_meaning_checker.py
- [ ] 69. tools/ai_openai_manager.py
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

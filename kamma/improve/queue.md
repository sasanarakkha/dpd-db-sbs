# Pipeline Improvement Queue

Pointer: 136

## Scripts (144 total, local unique_paths)

### db/families

- [x] 1. db/families/family_set_ru_update.py

### gui2

- [x] 2. gui2/dps_ai_service.py
- [x] 3. gui2/dps_db_helpers.py
- [x] 4. gui2/dps_field_mapping.py
- [x] 5. gui2/dps_process_additions.py
- [x] 6. gui2/dps_process_corrections.py

### scripts/change_in_db

- [x] 8. scripts/change_in_db/add_row_to_table.py
- [x] 9. scripts/change_in_db/apply_all_additions.py
- [x] 10. scripts/change_in_db/apply_all_corrections.py
- [x] 11. scripts/change_in_db/change_in_db.py | archived
- [x] 12. scripts/change_in_db/class_relation.py | passed (approach-only)
- [x] 13. scripts/change_in_db/copy_examples.py | changed (approach-only)
- [x] 14. scripts/change_in_db/copy_ru_meaning_raw_to_ru_meaning.py | archived
- [x] 15. scripts/change_in_db/fill_dhp_examples.py | passed
- [x] 16. scripts/change_in_db/preview_dhp_changes.py — already archived to scripts/dps_archive/ (commit 482becb05), queue was stale
- [x] 17. scripts/change_in_db/replace_in_db.py | archived
- [x] 18. scripts/change_in_db/sbs_class_sutta_linker.py — already archived (commit 3f8ac54a0), queue was stale
- [x] 19. scripts/change_in_db/dhp_examples_copy.py
- [x] 20. scripts/change_in_db/source_cleanup.py
- [x] 21. scripts/change_in_db/update_examples_from_csv.py | archived
- [x] 22. scripts/change_in_db/update_ru_db_from_csv.py | archived
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

- [x] 31. scripts/moving/copy_dpd_for_classes.py — merged into distribute.py
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
- [x] 70. tools/ai_related.py
- [x] 71. tools/ask.py
- [x] 72. tools/deepseek.py
- [x] 73. tools/duplicates.py
- [x] 74. tools/file_utils.py — archived
- [x] 75. tools/sbs_table_functions.py
- [x] 76. tools/tools_for_ru_exporter.py | changed

### scripts/rus_exporter

- [x] 77. scripts/rus_exporter/anki_config_github_release.py | changed (unified into set_config.py)
- [x] 78. scripts/rus_exporter/check_tpr_download_index.py | changed
- [x] 79. scripts/rus_exporter/config_github_local_dpd_rus.py | changed (unified into set_config.py)
- [x] 80. scripts/rus_exporter/config_github_local_dpd_sbs.py | changed (unified into set_config.py)
- [x] 81. scripts/rus_exporter/config_github_release_dpd_rus.py | changed (unified into set_config.py)
- [x] 82. scripts/rus_exporter/config_github_release_dpd_sbs.py | changed (unified into set_config.py)
- [x] 83. scripts/rus_exporter/config_github_release_dpd_ta.py | changed (unified into set_config.py)
- [x] 84. scripts/rus_exporter/config_github_server_dpd_sbs.py | changed (unified into set_config.py)
- [x] 85. scripts/rus_exporter/docs_add_indexes.py | removed from queue — shadow copy
- [x] 86. scripts/rus_exporter/docs_check_ru.py | changed
- [x] 87. scripts/rus_exporter/ru_config_github_release.py | changed (unified into set_config.py)
- [x] 88. scripts/rus_exporter/ru_zip_goldendict_mdict.py | removed from queue — shadow copy
- [x] 89. scripts/rus_exporter/zip_dpd_rus.py — unified into zip_dpd.py --locale rus
- [x] 90. scripts/rus_exporter/zip_dpd_sbs.py — unified into zip_dpd.py --locale sbs
- [x] 91. scripts/rus_exporter/zip_dpd_ta.py — unified into zip_dpd.py --locale ta

### db/backup_tsv

- [x] 94. db/backup_tsv/backup_all.py | archived

### scripts/bash

- [x] 95. scripts/bash/check_new_words.sh | archived
- [x] 96. scripts/bash/copy_dpd_to_server → copy_dpd_to_server.sh | changed
- [x] 97. scripts/bash/copy_tpr_db.sh | changed
- [x] 98. scripts/bash/download_dpd.sh | changed
- [x] 99. scripts/bash/download_pali_classes.sh | changed
- [x] 100. scripts/export/for_release.py | changed
- [x] 101. scripts/bash/manual_update_mac_dict.sh | changed
- [x] 102. scripts/bash/move_class.sh | changed
- [x] 103. scripts/bash/move_decks.sh | changed
- [x] 104. scripts/bash/pali_vocab_push.sh | changed
- [x] 105. scripts/bash/push_from_temp.sh | archived
- [x] 106. scripts/bash/rebuild_db.sh | changed
- [x] 107. scripts/bash/sbs-update-db.sh | archived
- [x] 108. scripts/bash/stage_study_tools.sh | changed
- [x] 109. scripts/bash/upload_study_tools.sh | changed
- [x] 110. scripts/bash/download_grammar.sh | changed
- [x] 111. scripts/bash/push_dpd.sh | changed
- [x] 112. scripts/bash/update_decks.sh | changed

### scripts/cl_dps

> Personal CLI commands invoked from PATH. Zero grep callers is expected —
> do not flag for archiving on that basis. Review for quality improvements instead.

- [x] 114. scripts/cl_dps/decks | changed
- [x] 115. scripts/cl_dps/dpd-anki | changed
- [x] 116. scripts/cl_dps/dpd-build-db | passed
- [x] 117. scripts/cl_dps/dpd-gui2 | passed
- [x] 118. scripts/cl_dps/dpd-kamma-sync | changed
- [x] 119. scripts/cl_dps/dpd-makedict | changed
- [x] 120. scripts/cl_dps/dpd-push | changed
- [x] 121. scripts/cl_dps/dpd-review-comments | changed
- [x] 122. scripts/cl_dps/dpd-upstream-push | archived
- [x] 123. scripts/cl_dps/dpd-upstream-push-corrections | changed
- [x] 124. scripts/cl_dps/dpd-upstream-push-latest | changed
- [x] 125. scripts/cl_dps/dpd-vib-rule | changed
- [x] 126. scripts/cl_dps/dpd-webapp | skipped

### scripts/export (additional)

- [x] 127. scripts/export/anki_csv.py | changed
- [x] 128. scripts/export/dps_anki_updater.py | improved (module-level → main(), dead code removed, simplify make_data_dict, print→pr, pathlib, modern types, 12 tests)
- [x] 129. scripts/export/extract_ebt_text.py | archived
- [x] 130. scripts/export/filter_from_db.py | archived
- [x] 131. scripts/export/filtering_and_backup.py | archived
- [x] 132. scripts/export/list_of_words_from_txt.py | changed (simplify make_decon_word_list, fix docstring/encoding/types, 6 regression tests)
- [x] 133. scripts/export/list_of_words_from_txt_old.py | archived
- [x] 134. scripts/export/save_all_sutta_names.py | archived
- [x] 135. scripts/export/save_all_words_alphabetically.py | archived
- [ ] 136. scripts/export/save_all_words_sorted_by_family.py
- [ ] 137. scripts/export/save_csv_for_audio.py
- [ ] 138. scripts/export/save_filtered_words.py
- [ ] 139. scripts/export/save_russian_for_collaborator.py
- [ ] 140. scripts/export/sbs_anki_fields_check.py
- [ ] 141. scripts/export/sbs_anki_templates.py
- [ ] 142. scripts/export/sbs_anki_update_seed.py
- [ ] 143. scripts/export/sbs_example_dupes.py
- [ ] 144. scripts/export/sourse_atth_sbs_mula.py
- [ ] 145. scripts/export/vocab_abbrev_pali_course.py

### tools (additional)

- [ ] 146. tools/meaning_snapshot_ru.py

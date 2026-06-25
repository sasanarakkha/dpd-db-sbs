# Pipeline Improvement Queue

> **Note:** Items #1-24 are intentionally left unchecked `[ ]` even though they already
> have full review entries in the Decisions log below. Do NOT treat this as a stale
> checkbox bug and do NOT check them off without re-reviewing. Between reviewing #25 and
> #26 the skill itself was updated to add the "Approach suggestion" angle (a 5th review
> angle: is there a significantly simpler/more elegant way to achieve the same result).
> #1-24 were reviewed under the old skill version and never got that angle applied. When
> the Pointer reaches them again, apply ONLY the approach-suggestion angle — do not
> re-litigate the refactor work already logged (type hints, pr.* conversion, dead code,
> etc.), that part is done and should not be redone.

Pointer: 15

## Scripts (146 total, local unique_paths)

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
- [ ] 15. scripts/change_in_db/fill_dhp_examples.py
- [ ] 16. scripts/change_in_db/preview_dhp_changes.py
- [ ] 17. scripts/change_in_db/replace_in_db.py
- [ ] 18. scripts/change_in_db/sbs_class_sutta_linker.py
- [ ] 19. scripts/change_in_db/dhp_examples_copy.py
- [ ] 20. scripts/change_in_db/source_cleanup.py
- [ ] 21. scripts/change_in_db/update_examples_from_csv.py
- [ ] 22. scripts/change_in_db/update_ru_db_from_csv.py
- [ ] 23. scripts/change_in_db/update_sbs_chants_in_db.py
- [ ] 24. scripts/change_in_db/update_yojana_km.py
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
- [x] 70. tools/ai_related.py
- [x] 71. tools/ask.py
- [x] 72. tools/deepseek.py
- [x] 73. tools/duplicates.py
- [x] 74. tools/file_utils.py — archived
- [x] 75. tools/sbs_table_functions.py
- [ ] 76. tools/tools_for_ru_exporter.py

### scripts/rus_exporter

- [ ] 77. scripts/rus_exporter/anki_config_github_release.py
- [ ] 78. scripts/rus_exporter/check_tpr_download_index.py
- [ ] 79. scripts/rus_exporter/config_github_local_dpd_rus.py
- [ ] 80. scripts/rus_exporter/config_github_local_dpd_sbs.py
- [ ] 81. scripts/rus_exporter/config_github_release_dpd_rus.py
- [ ] 82. scripts/rus_exporter/config_github_release_dpd_sbs.py
- [ ] 83. scripts/rus_exporter/config_github_release_dpd_ta.py
- [ ] 84. scripts/rus_exporter/config_github_server_dpd_sbs.py
- [ ] 85. scripts/rus_exporter/docs_add_indexes.py
- [ ] 86. scripts/rus_exporter/docs_check_ru.py
- [ ] 87. scripts/rus_exporter/ru_config_github_release.py
- [ ] 88. scripts/rus_exporter/ru_zip_goldendict_mdict.py
- [ ] 89. scripts/rus_exporter/zip_dpd_rus.py
- [ ] 90. scripts/rus_exporter/zip_dpd_sbs.py
- [ ] 91. scripts/rus_exporter/zip_dpd_ta.py

### scripts/change_in_db (new additions)

- [ ] 92. scripts/change_in_db/rearrange_sbs_gatha_lines.py
- [ ] 93. scripts/change_in_db/sbs_dpd_example_transfers.py

### db/backup_tsv

- [ ] 94. db/backup_tsv/backup_all.py

### scripts/bash

- [ ] 95. scripts/bash/check_new_words.sh
- [ ] 96. scripts/bash/copy_dpd_to_server
- [ ] 97. scripts/bash/copy_tpr_db.sh
- [ ] 98. scripts/bash/download_dpd.sh
- [ ] 99. scripts/bash/download_pali_classes.sh
- [ ] 100. scripts/bash/for_release.py
- [ ] 101. scripts/bash/manual_update_mac_dict.sh
- [ ] 102. scripts/bash/move_class.sh
- [ ] 103. scripts/bash/move_decks.sh
- [ ] 104. scripts/bash/pali_vocab_push.sh
- [ ] 105. scripts/bash/push_from_temp.sh
- [ ] 106. scripts/bash/rebuild_db.sh
- [ ] 107. scripts/bash/sbs-update-db.sh
- [ ] 108. scripts/bash/stage_study_tools.sh
- [ ] 109. scripts/bash/upload_study_tools.sh
- [ ] 110. scripts/bash/download_grammar.sh
- [ ] 111. scripts/bash/push_dpd.sh
- [ ] 112. scripts/bash/update_decks.sh

### scripts/cl

- [ ] 113. scripts/cl/dpd-gui2

### scripts/cl_dps

- [ ] 114. scripts/cl_dps/decks
- [ ] 115. scripts/cl_dps/dpd-anki
- [ ] 116. scripts/cl_dps/dpd-build-db
- [ ] 117. scripts/cl_dps/dpd-gui2
- [ ] 118. scripts/cl_dps/dpd-kamma-sync
- [ ] 119. scripts/cl_dps/dpd-makedict
- [ ] 120. scripts/cl_dps/dpd-push
- [ ] 121. scripts/cl_dps/dpd-review-comments
- [ ] 122. scripts/cl_dps/dpd-upstream-push
- [ ] 123. scripts/cl_dps/dpd-upstream-push-corrections
- [ ] 124. scripts/cl_dps/dpd-upstream-push-latest
- [ ] 125. scripts/cl_dps/dpd-vib-rule
- [ ] 126. scripts/cl_dps/dpd-webapp

### scripts/export (additional)

- [ ] 127. scripts/export/anki_csv.py
- [ ] 128. scripts/export/dps_anki_updater.py
- [ ] 129. scripts/export/extract_ebt_text.py
- [ ] 130. scripts/export/filter_from_db.py
- [ ] 131. scripts/export/filtering_and_backup.py
- [ ] 132. scripts/export/list_of_words_from_txt.py
- [ ] 133. scripts/export/list_of_words_from_txt_old.py
- [ ] 134. scripts/export/save_all_sutta_names.py
- [ ] 135. scripts/export/save_all_words_alphabetically.py
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


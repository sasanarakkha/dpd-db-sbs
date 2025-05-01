"""Render tab to edit a Russian and SBS tables in the database."""

from gui.functions_db_dps import load_sbs_index
from gui.completion_combo import CompletionCombo
from tools.sbs_table_functions import sbs_category_list

def make_tab_edit_dps(dpspth, sg):

    sbs_index = load_sbs_index(dpspth)
    pali_chant_list = [i.pali_chant for i in sbs_index]
    anki_class_list = [str(i) for i in range(1, 60)]
    class_list = [str(i) for i in range(2, 30)]
    sbs_example_number = [str(i) for i in range(1, 5)]
    dps_patimokkha_list = ["pat", "vib"]

    dpd_background = "#1c1e23"
    dpd_text = "#0a9ce4"
    ru_background = "#32363f"
    ru_text = "white"
    sbs_background = "#272a31"
    sbs_text = "white"

    dps_layout = [
        [
            sg.Text("show fields", size=(15, 1)),
            sg.Radio(
                "all", "group1",
                key="dps_show_fields_all",
                enable_events=True,
                tooltip="Show the fields relevant to the type of word"),
            sg.Radio(
                "no sbs", "group1",
                key="dps_show_fields_no_sbs",
                enable_events=True,
                tooltip="Show the fields relevant to the type of word"),
        ],
        [
            sg.Text("id and lemma_1", size=(15, 1)),
            sg.Input(
                key="dps_dpd_id", size=(7, 1),
                text_color=dpd_text,
                background_color=dpd_background),
            sg.Input(
                key="dps_lemma_1", size=(43, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("grammar", size=(15, 1)),
            sg.Input(
                key="dps_grammar",
                size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
            sg.Text("", size=(100, 1)),
            sg.Input(
                key="dps_pos",
                text_color=dpd_text,
                visible=False,
                background_color=dpd_background),
            sg.Input(
                key="dps_verb",
                text_color=dpd_text,
                visible=False,
                background_color=dpd_background),
            sg.Input(
                key="dps_suffix",
                text_color=dpd_text,
                visible=False,
                background_color=dpd_background),
            sg.Input(
                key="dps_meaning_lit",
                text_color=dpd_text,
                visible=False,
                background_color=dpd_background),
            sg.Input(
                key="dps_meaning_1",
                text_color=dpd_text,
                visible=False,
                background_color=dpd_background),
        ],
        [
            sg.Text("meaning", size=(15, 1)),
            sg.Multiline(
                key="dps_meaning",
                size=(50, 2),
                enable_events=True,
                text_color=dpd_text,
                background_color=dpd_background),
            sg.Text(
                "", key="dps_repetition_meaning_error", size=(50, 1), text_color="red"),
        ],
        [
            sg.Text("suggestion", size=(15, 1)),
            sg.Multiline(
                key="dps_ru_online_suggestion",
                size=(50, 3),
                enable_events=True,
                background_color=dpd_background),
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button("Synonym", key="dps_synonym_translate_button", font=(None, 13)),
            sg.Button("AI low", key="dps_ai_translate_button_1", font=(None, 13)),
            sg.Button("AI high", key="dps_ai_translate_button_2", font=(None, 13)),
            sg.Button("Copy", key="dps_copy_meaning_button", font=(None, 13)),
            sg.Text("ex:"),
            CompletionCombo(
                sbs_example_number,
                key="sbs_example_for_suggestion",
                default_value="0",
                size=(2, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background,
                tooltip="Choose sbs_example to consider when sending a request to AI. Default '0' is dpd_example_1"),
            sg.Text(
                "", key="dps_ru_meaning_suggestion_error", size=(50, 1), text_color="red"),
        ],
        [
            sg.Text("russian*", size=(15, 1)),
            sg.Multiline(
                key="dps_ru_meaning",
                size=(50, 2),
                enable_events=True,
                tooltip="type Russian meaning",
                text_color=ru_text,
                background_color=ru_background),
            sg.Text(
                "", key="dps_ru_meaning_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("ru_add_spelling", size=(15, 1)),
            sg.Input(
                key="dps_ru_add_spelling", size=(25, 1), enable_events=True,
                tooltip="Add a word to the user russian dictionary."),
            sg.Button("Add", key="dps_ru_add_spelling_button", font=(None, 13)),
            sg.Button("Edit", key="dps_ru_edit_spelling_button", font=(None, 13)),
            sg.Button("Check", key="dps_ru_check_spelling_button", font=(None, 13)),
        ],
        [
            sg.Text("russian lit", size=(15, 1)),
            sg.Input(
                key="dps_ru_meaning_lit",
                size=(50, 1),
                enable_events=True,
                tooltip="type Russian literal meaning",
                text_color=ru_text,
                background_color=ru_background),
            sg.Text(
                "", key="dps_ru_meaning_lit_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("russian cognate", size=(15, 1)),
            sg.Input(
                key="dps_ru_cognate",
                size=(50, 1),
                enable_events=True,
                tooltip="Russian word which close sounding",
                text_color=ru_text,
                background_color=ru_background),
            sg.Text(
                "", key="dps_ru_cognate_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs meaning", size=(15, 1)),
            sg.Multiline(
                key="dps_sbs_meaning",
                size=(50, 2),
                enable_events=True,
                tooltip="type meaning in SBS PER",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_meaning_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("root", size=(15, 1)),
            sg.Input(
                key="dps_root",
                size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("base or comp", size=(15, 1)),
            sg.Input(
                key="dps_base_or_comp",
                size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("constr", size=(15, 1)),
            sg.Input(
                key="dps_constr_or_comp_constr",
                size=(50, 2),
                tooltip="",
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("ru_synonym", size=(15, 1)),
            sg.Input(
                key="dps_synonym",
                size=(50, 1), enable_events=True,
                text_color=dpd_text,
                background_color=dpd_background),
            sg.Text(
                "", key="dps_synonym_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("syn&ant", size=(15, 1)),
            sg.Input(
                key="dps_synonym_antonym",
                size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("set", size=(15, 1)),
                    sg.Input(
                key="dps_family_set",
                size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("notes", size=(15, 1)),
            sg.Multiline(
                key="dps_notes",
                size=(50, 3),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("suggestion", size=(15, 1)),
            sg.Multiline(
                key="dps_notes_online_suggestion",
                size=(50, 2),
                enable_events=True,
                background_color=dpd_background),
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button("AI", key="dps_notes_ai_translate_button", font=(None, 13)),
            sg.Button("Copy", key="dps_notes_copy_meaning_button", font=(None, 13)),
            sg.Text(
                "", key="dps_ru_notes_suggestion_error", size=(40, 1), text_color="red"),
        ],
        [
            sg.Text("russian note", size=(15, 1)),
            sg.Multiline(
                key="dps_ru_notes",
                size=(50, 2),
                enable_events=True,
                tooltip="",
                text_color=ru_text,
                background_color=ru_background),
            sg.Text(
                "", key="dps_ru_notes_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs note", size=(15, 1)),
            sg.Multiline(
                key="dps_sbs_notes",
                size=(50, 2),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_notes_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("dpd_source_1", size=(15, 1)),
            sg.Input(
                key="dps_source_1", size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("dpd_sutta_1", size=(15, 1)),
            sg.Input(
                key="dps_sutta_1", size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("dpd_example_1", size=(15, 5)),
            sg.Multiline(
                key="dps_example_1", size=(49, 5),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("ex_1 copy to", size=(15, 1)),
            sg.Button("sbs_ex_1", key="dps_copy_ex_1_to_1_button", font=(None, 13)),
            sg.Button("sbs_ex_2", key="dps_copy_ex_1_to_2_button", font=(None, 13)),
            sg.Button("dhp", key="dps_copy_ex_1_to_dhp_button", font=(None, 13)),
            sg.Button("pat", key="dps_copy_ex_1_to_pat_button", font=(None, 13)),
            sg.Button("vib", key="dps_copy_ex_1_to_vib_button", font=(None, 13)),
            sg.Button("class", key="dps_copy_ex_1_to_class_button", font=(None, 13)),
            sg.Button("disc", key="dps_copy_ex_1_to_discourses_button", font=(None, 13)),
        ],
        [
            sg.Text("dpd_source_2", size=(15, 1)),
            sg.Input(
                key="dps_source_2", size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("dpd_sutta_2", size=(15, 1)),
            sg.Input(
                key="dps_sutta_2", size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("dpd_example_2", size=(15, 5)),
            sg.Multiline(
                key="dps_example_2", size=(49, 5),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("ex_2 copy to", size=(15, 1)),
            sg.Button("sbs_ex_1", key="dps_copy_ex_2_to_1_button", font=(None, 13)),
            sg.Button("sbs_ex_2", key="dps_copy_ex_2_to_2_button", font=(None, 13)),
            sg.Button("dhp", key="dps_copy_ex_2_to_dhp_button", font=(None, 13)),
            sg.Button("pat", key="dps_copy_ex_2_to_pat_button", font=(None, 13)),
            sg.Button("vib", key="dps_copy_ex_2_to_vib_button", font=(None, 13)),
            sg.Button("class", key="dps_copy_ex_2_to_class_button", font=(None, 13)),
            sg.Button("disc", key="dps_copy_ex_2_to_discourses_button", font=(None, 13)),
        ],
        [
            sg.Text("sbs_source_1", size=(15, 1)),
            sg.Input(
                key="dps_sbs_source_1",
                size=(50, 1),
                enable_events=True,
                tooltip="Sutta code using DPR system",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_source_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs_sutta_1", size=(15, 1)),
            sg.Input(
                key="dps_sbs_sutta_1",
                size=(50, 1),
                enable_events=True,
                tooltip="Sutta name",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_sutta_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs_example_1", size=(15, 1)),
            sg.Multiline(
                key="dps_sbs_example_1",
                size=(50, 4),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_example_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                key="dps_bold_1", size=(20, 1),
                tooltip="Bold the word"),
            sg.Button("Bold", key="dps_bold_1_button", font=(None, 13)),
            sg.Button(
                "Find",
                key="dps_another_eg_1",
                tooltip="Find another sutta example",
                font=(None, 13)),
            sg.Button("Lwr", key="dps_example_1_lower", font=(None, 13)),
            sg.Button("Clean", key="dps_example_1_clean", font=(None, 13)),
            sg.Button("S", key="dps_stash_ex_1_button", font=(None, 13)),
            sg.Button("L", key="dps_unstash_ex_1_button", font=(None, 13)),
            sg.Button("Cl", key="dps_remove_example_1_button", font=(None, 13)),
            sg.Button("Sw", key="dps_swap_ex_1_with_2_button", font=(None, 13)),
            sg.Text("", key="dps_bold_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs_chant_pali_1", size=(15, 1)),
            CompletionCombo(
                pali_chant_list,
                key="dps_sbs_chant_pali_1",
                size=(50, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_chant_pali_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs_chant_eng_1", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chant_eng_1",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chapter_1", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chapter_1",
                size=(50, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background,
                tooltip=""),
        ],
        [
            sg.Text("ex_1 copy to", size=(15, 1)),
            sg.Button("dhp", key="dps_copy_sbs_1_to_dhp_button", font=(None, 13)),
            sg.Button("pat", key="dps_copy_sbs_1_to_pat_button", font=(None, 13)),
            sg.Button("vib", key="dps_copy_sbs_1_to_vib_button", font=(None, 13)),
            sg.Button("class", key="dps_copy_sbs_1_to_class_button", font=(None, 13)),
            sg.Button("disc", key="dps_copy_sbs_1_to_discourses_button", font=(None, 13)),
            sg.Text(
                "", key="dps_buttons_ex_1_error", size=(50, 1), text_color="red"),
        ],
        [
            sg.Text("sbs_source_2", size=(15, 1)),
            sg.Input(
                key="dps_sbs_source_2",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_source_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs_sutta_2", size=(15, 1)),
            sg.Input(
                key="dps_sbs_sutta_2",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_sutta_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs_example_2", size=(15, 1)),
            sg.Multiline(
                key="dps_sbs_example_2",
                size=(50, 4),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_example_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                key="dps_bold_2", size=(20, 1),
                tooltip="Bold the word"),
            sg.Button("Bold", key="dps_bold_2_button", font=(None, 13)),
            sg.Button(
                "Find",
                key="dps_another_eg_2",
                tooltip="Find another sutta example",
                font=(None, 13)),
            sg.Button("Lwr", key="dps_example_2_lower", font=(None, 13)),
            sg.Button("Clean", key="dps_example_2_clean", font=(None, 13)),
            sg.Button("S", key="dps_stash_ex_2_button", font=(None, 13)),
            sg.Button("L", key="dps_unstash_ex_2_button", font=(None, 13)),
            sg.Button("Cl", key="dps_remove_example_2_button", font=(None, 13)),
        ],
        [
            sg.Text("sbs_chant_pali_2", size=(15, 1)),
            CompletionCombo(
                pali_chant_list,
                key="dps_sbs_chant_pali_2",
                size=(50, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_chant_pali_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs_chant_eng_2", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chant_eng_2",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chapter_2", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chapter_2",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("ex_2 copy to", size=(15, 1)),
            sg.Button("dhp", key="dps_copy_sbs_2_to_dhp_button", font=(None, 13)),
            sg.Button("pat", key="dps_copy_sbs_2_to_pat_button", font=(None, 13)),
            sg.Button("vib", key="dps_copy_sbs_2_to_vib_button", font=(None, 13)),
            sg.Button("class", key="dps_copy_sbs_2_to_class_button", font=(None, 13)),
            sg.Button("disc", key="dps_copy_sbs_2_to_discourses_button", font=(None, 13)),
            sg.Text(
                "", key="dps_buttons_ex_2_error", size=(50, 1), text_color="red"),
        ],
        [
            sg.Text("dhp_source", size=(15, 1)),
            sg.Input(
                key="dps_dhp_source",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_dhp_source_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("dhp_sutta", size=(15, 1)),
            sg.Input(
                key="dps_dhp_sutta",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_dhp_sutta_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("dhp_example", size=(15, 1)),
            sg.Multiline(
                key="dps_dhp_example",
                size=(50, 4),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_dhp_example_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                key="dps_bold_dhp", size=(20, 1),
                tooltip="Bold the word"),
            sg.Button("Bold", key="dps_bold_dhp_button", font=(None, 13)),
            sg.Button(
                "Find",
                key="dps_another_eg_dhp",
                tooltip="Find another sutta example",
                font=(None, 13)),
            sg.Button("Lwr", key="dps_example_dhp_lower", font=(None, 13)),
            sg.Button("Clean", key="dps_example_dhp_clean", font=(None, 13)),
            sg.Button("S", key="dps_stash_ex_dhp_button", font=(None, 13)),
            sg.Button("L", key="dps_unstash_ex_dhp_button", font=(None, 13)),
            sg.Button("Cl", key="dps_remove_example_dhp_button", font=(None, 13)),
        ],
        [
            sg.Text("pat_source", size=(15, 1)),
            sg.Input(
                key="dps_pat_source",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_pat_source_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("pat_sutta", size=(15, 1)),
            sg.Input(
                key="dps_pat_sutta",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_pat_sutta_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("pat_example", size=(15, 1)),
            sg.Multiline(
                key="dps_pat_example",
                size=(50, 4),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_pat_example_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                key="dps_bold_pat", size=(20, 1),
                tooltip="Bold the word"),
            sg.Button("Bold", key="dps_bold_pat_button", font=(None, 13)),
            sg.Button(
                "Find",
                key="dps_another_eg_pat",
                tooltip="Find another sutta example",
                font=(None, 13)),
            sg.Button("Lwr", key="dps_example_pat_lower", font=(None, 13)),
            sg.Button("Clean", key="dps_example_pat_clean", font=(None, 13)),
            sg.Button("S", key="dps_stash_ex_pat_button", font=(None, 13)),
            sg.Button("L", key="dps_unstash_ex_pat_button", font=(None, 13)),
            sg.Button("Cl", key="dps_remove_example_pat_button", font=(None, 13)),
        ],
        [
            sg.Text("vib_source", size=(15, 1)),
            sg.Input(
                key="dps_vib_source",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_vib_source_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("vib_sutta", size=(15, 1)),
            sg.Input(
                key="dps_vib_sutta",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_vib_sutta_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("vib_example", size=(15, 1)),
            sg.Multiline(
                key="dps_vib_example",
                size=(50, 4),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_vib_example_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                key="dps_bold_vib", size=(20, 1),
                tooltip="Bold the word"),
            sg.Button("Bold", key="dps_bold_vib_button", font=(None, 13)),
            sg.Button(
                "Find",
                key="dps_another_eg_vib",
                tooltip="Find another sutta example",
                font=(None, 13)),
            sg.Button("Lwr", key="dps_example_vib_lower", font=(None, 13)),
            sg.Button("Clean", key="dps_example_vib_clean", font=(None, 13)),
            sg.Button("S", key="dps_stash_ex_vib_button", font=(None, 13)),
            sg.Button("L", key="dps_unstash_ex_vib_button", font=(None, 13)),
            sg.Button("Cl", key="dps_remove_example_vib_button", font=(None, 13)),
        ],
        [
            sg.Text("class_source", size=(15, 1)),
            sg.Input(
                key="dps_class_source",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_class_source_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("class_sutta", size=(15, 1)),
            sg.Input(
                key="dps_class_sutta",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_class_sutta_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("class_example", size=(15, 1)),
            sg.Multiline(
                key="dps_class_example",
                size=(50, 4),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_class_example_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                key="dps_bold_class", size=(20, 1),
                tooltip="Bold the word"),
            sg.Button("Bold", key="dps_bold_class_button", font=(None, 13)),
            sg.Button(
                "Find",
                key="dps_another_eg_class",
                tooltip="Find another sutta example",
                font=(None, 13)),
            sg.Button("Lwr", key="dps_example_class_lower", font=(None, 13)),
            sg.Button("Clean", key="dps_example_class_clean", font=(None, 13)),
            sg.Button("S", key="dps_stash_ex_class_button", font=(None, 13)),
            sg.Button("L", key="dps_unstash_ex_class_button", font=(None, 13)),
            sg.Button("Cl", key="dps_remove_example_class_button", font=(None, 13)),
        ],
        [
            sg.Text("discourses_source", size=(15, 1)),
            sg.Input(
                key="dps_discourses_source",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_discourses_source_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("discourses_sutta", size=(15, 1)),
            sg.Input(
                key="dps_discourses_sutta",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_discourses_sutta_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("discourses_example", size=(15, 1)),
            sg.Multiline(
                key="dps_discourses_example",
                size=(50, 4),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_discourses_example_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                key="dps_bold_discourses", size=(20, 1),
                tooltip="Bold the word"),
            sg.Button("Bold", key="dps_bold_discourses_button", font=(None, 13)),
            sg.Button(
                "Find",
                key="dps_another_eg_discourses",
                tooltip="Find another sutta example",
                font=(None, 13)),
            sg.Button("Lwr", key="dps_example_discourses_lower", font=(None, 13)),
            sg.Button("Clean", key="dps_example_discourses_clean", font=(None, 13)),
            sg.Button("S", key="dps_stash_ex_discourses_button", font=(None, 13)),
            sg.Button("L", key="dps_unstash_ex_discourses_button", font=(None, 13)),
            sg.Button("Cl", key="dps_remove_example_discourses_button", font=(None, 13)),
            sg.Button("Arch", key="dps_archive_button", font=(None, 13)),
        ],
        [
            sg.Text("sbs_source_3", size=(15, 1)),
            sg.Input(
                key="dps_sbs_source_3",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_source_3_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs_sutta_3", size=(15, 1)),
            sg.Input(
                key="dps_sbs_sutta_3",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_sutta_3_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs_example_3", size=(15, 1)),
            sg.Multiline(
                key="dps_sbs_example_3",
                size=(50, 4),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_example_3_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("ex_3 copy to", size=(15, 1)),
            sg.Button("dhp", key="dps_copy_sbs_3_to_dhp_button", font=(None, 13)),
            sg.Button("pat", key="dps_copy_sbs_3_to_pat_button", font=(None, 13)),
            sg.Button("vib", key="dps_copy_sbs_3_to_vib_button", font=(None, 13)),
            sg.Button("class", key="dps_copy_sbs_3_to_class_button", font=(None, 13)),
            sg.Button("disc", key="dps_copy_sbs_3_to_discourses_button", font=(None, 13)),
            sg.Text(
                "", key="dps_buttons_ex_3_error", size=(10, 1), text_color="red"),
        ],
        [
            sg.Text("sbs_source_4", size=(15, 1)),
            sg.Input(
                key="dps_sbs_source_4",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_source_4_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs_sutta_4", size=(15, 1)),
            sg.Input(
                key="dps_sbs_sutta_4",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_sutta_4_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sbs_example_4", size=(15, 1)),
            sg.Multiline(
                key="dps_sbs_example_4",
                size=(50, 4),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
            sg.Text(
                "", key="dps_sbs_example_4_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("ex_4 copy to", size=(15, 1)),
            sg.Button("dhp", key="dps_copy_sbs_4_to_dhp_button", font=(None, 13)),
            sg.Button("pat", key="dps_copy_sbs_4_to_pat_button", font=(None, 13)),
            sg.Button("vib", key="dps_copy_sbs_4_to_vib_button", font=(None, 13)),
            sg.Button("class", key="dps_copy_sbs_4_to_class_button", font=(None, 13)),
            sg.Button("disc", key="dps_copy_sbs_4_to_discourses_button", font=(None, 13)),
            sg.Text(
                "", key="dps_buttons_ex_4_error", size=(10, 1), text_color="red"),
        ],
        [
            sg.Text("sbs_class_anki", size=(15, 1)),
            CompletionCombo(
                anki_class_list,
                key="dps_sbs_class_anki",
                default_value="",
                size=(3, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background,
                tooltip="which class from Anki deck for Pāli Class"),
            sg.Text("", size=(6, 1)),
            sg.Text("sbs_class "),
            CompletionCombo(
                class_list,
                key="dps_sbs_class",
                default_value="",
                size=(3, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background,
                tooltip="related to which class from the Pāli Course"),
        ],
        [
            sg.Text("sbs_category", size=(15, 1)),
            CompletionCombo(
                sbs_category_list,
                key="dps_sbs_category",
                default_value="",
                size=(6, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background,
                tooltip="which sutta from sutta anki deck"),
            sg.Text("", size=(3, 1)),
            sg.Text("sbs_patimokkha "),
            CompletionCombo(
                dps_patimokkha_list,
                key="dps_sbs_patimokkha",
                default_value="",
                size=(4, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background,
                tooltip="related to Bhikkhu Pātimokkha or Bhikkhu Vibhaṅga"),
        ],
        [
            sg.Text("", size=(55, 1))
        ],
    ]

    tab_edit_dps = [
        [
            sg.Column(
                dps_layout,
                scrollable=True,
                vertical_scroll_only=True,
                expand_y=True,
                expand_x=True,
                size=(None, 850),
            ),
        ],
        [
            sg.HSep(),
        ],
        [
            # db buttons
            sg.Text("db buttons", size=(15, 1)),
            sg.Input(
                "",
                key="dps_id_or_lemma_1",
                size=(15, 1),
                enable_events=True,
                tooltip="enter id or lemma_1"
                ),
            sg.Button(
                "Get word",
                key="dps_id_or_lemma_1_button",
                tooltip="click to fetch word from db",
                font=(None, 11),
                ),
            sg.Text("", size=(2, 1)),
            sg.Button(
                "Test", 
                key="dps_test_internal_button",
                tooltip="Run internal tests",
                font=(None, 11),
                ),
            sg.Button(
                "Update DB", 
                key="dps_update_db_button",
                tooltip="Add a sbs or ru info into the db",
                font=(None, 11),
                ),
            sg.Button(
                "Next Ru", 
                key="dps_show_next_word_ru",
                tooltip="Show next word with meaning_1 and ru_meaning empty",
                font=(None, 11),
                ),
            sg.Button(
                "Next Note", 
                key="dps_show_next_note_ru",
                tooltip="Show next word with notes and ru_notes empty",
                font=(None, 11),
                ),
        ],
        [
            # gui buttons
            sg.Text("gui buttons", size=(15, 1)),
            sg.Button(
                "Clear", 
                key="dps_clear_button", 
                tooltip="Clear all the fields",
                font=(None, 11),
                ),
            sg.Button(
                "Reset", 
                key="dps_reset_button",
                tooltip="Reset all fields as they was before editing",
                font=(None, 11),
                ),
            sg.Button(
                "Stash", key="dps_stash_button",
                tooltip="Stash the word to edit it again later",
                font=(None, 11),
                ),
            sg.Button(
                "Unstash", key="dps_unstash_button",
                tooltip="Unstash a word to edit it again",
                font=(None, 11),
                ),
            sg.Button(
                "Open Tests", key="dps_open_tests_button",
                tooltip="Open TSV file of DPS internal tests",
                font=(None, 11),
                ),
            sg.Button(
                "Log", key="dps_open_log_in_terminal_button",
                tooltip="Open log of GUI in the terminal",
                font=(None, 11),
                ),
            sg.Button(
                "Summary", 
                key="dps_summary_button", 
                tooltip="See a summary of filled fields",
                font=(None, 11),
                ),
            sg.Button(
                "HTML", key="dps_html_summary_button",
                tooltip="See a html summary of a DPS data of the word in db",
                font=(None, 11),
                ),
        ],
    ]

    return tab_edit_dps

# -*- coding: utf-8 -*-
import flet as ft
from gui2.dps_example_field import DpsExampleField
from gui2.dps_meaning_field import DpsMeaningField

common_params = {
    "border_color": ft.Colors.BLUE_200,
    "border_radius": 20,
    "text_size": 17,
    "expand": True,
}

def create_params(specific_params):
    params = common_params.copy()
    params.update(specific_params)
    return params

dps_field_mapping = {
    "dps_id": {"control": ft.TextField, "params": create_params({"disabled": False})},
    "dps_lemma_1": {"control": ft.TextField, "params": create_params({"disabled": False})},
    "dps_grammar": {"control": ft.TextField, "params": create_params({"disabled": False})},
    "dps_meaning": {"control": ft.TextField, "params": create_params({"multiline": True, "min_lines": 2, "disabled": False})},
    "dps_suggestion": {"control": ft.TextField, "params": create_params({"multiline": True, "min_lines": 3})},
    "dps_ru_meaning": {"control": DpsMeaningField, "params": create_params({"multiline": True, "min_lines": 2, "tooltip": "type Russian meaning"})},
    "dps_ru_meaning_lit": {"control": DpsMeaningField, "params": create_params({"tooltip": "type Russian literal meaning"})},
    "dps_ru_cognate": {"control": ft.TextField, "params": create_params({"tooltip": "Russian word which close sounding"})},
    "dps_sbs_meaning": {"control": ft.TextField, "params": create_params({"multiline": True, "min_lines": 2, "tooltip": "type meaning in SBS PER"})},
    "dps_root": {"control": ft.TextField, "params": create_params({"disabled": False})},
    "dps_constriction": {"control": ft.TextField, "params": create_params({"disabled": False})},
    "dps_synonym_antonym": {"control": ft.TextField, "params": create_params({"disabled": False})},
    "dps_notes": {"control": ft.TextField, "params": create_params({"multiline": True, "min_lines": 3, "disabled": False})},
    "dps_notes_suggestion": {"control": ft.TextField, "params": create_params({"multiline": True, "min_lines": 2})},
    "dps_ru_notes": {"control": ft.TextField, "params": create_params({"multiline": True, "min_lines": 2})},
    "dps_sbs_notes": {"control": ft.TextField, "params": create_params({"multiline": True, "min_lines": 2})},
    "dps_source_1": {"control": ft.TextField, "params": create_params({"disabled": False})},
    "dps_sutta_1": {"control": ft.TextField, "params": create_params({"disabled": False})},
    "dps_example_1": {"control": DpsExampleField, "params": create_params({"multiline": True, "min_lines": 5, "disabled": False})},
    "dps_source_2": {"control": ft.TextField, "params": create_params({"disabled": False})},
    "dps_sutta_2": {"control": ft.TextField, "params": create_params({"disabled": False})},
    "dps_example_2": {"control": DpsExampleField, "params": create_params({"multiline": True, "min_lines": 5, "disabled": False})},
    "dps_sbs_source_1": {"control": ft.TextField, "params": create_params({"tooltip": "Sutta code using DPR system"})},
    "dps_sbs_sutta_1": {"control": ft.TextField, "params": create_params({"tooltip": "Sutta name"})},
    "dps_sbs_example_1": {"control": DpsExampleField, "params": create_params({"multiline": True, "min_lines": 4})},
    "dps_sbs_chant_pali_1": {"control": ft.TextField, "params": create_params({})},
    "dps_sbs_chant_eng_1": {"control": ft.TextField, "params": create_params({})},
    "dps_sbs_chapter_1": {"control": ft.TextField, "params": create_params({})},
    "dps_sbs_source_2": {"control": ft.TextField, "params": create_params({})},
    "dps_sbs_sutta_2": {"control": ft.TextField, "params": create_params({})},
    "dps_sbs_example_2": {"control": DpsExampleField, "params": create_params({"multiline": True, "min_lines": 4})},
    "dps_sbs_chant_pali_2": {"control": ft.TextField, "params": create_params({})},
    "dps_sbs_chant_eng_2": {"control": ft.TextField, "params": create_params({})},
    "dps_sbs_chapter_2": {"control": ft.TextField, "params": create_params({})},
    "dps_dhp_source": {"control": ft.TextField, "params": create_params({})},
    "dps_dhp_sutta": {"control": ft.TextField, "params": create_params({})},
    "dps_dhp_example": {"control": DpsExampleField, "params": create_params({"multiline": True, "min_lines": 4})},
    "dps_pat_source": {"control": ft.TextField, "params": create_params({})},
    "dps_pat_sutta": {"control": ft.TextField, "params": create_params({})},
    "dps_pat_example": {"control": DpsExampleField, "params": create_params({"multiline": True, "min_lines": 4})},
    "dps_vib_source": {"control": ft.TextField, "params": create_params({})},
    "dps_vib_sutta": {"control": ft.TextField, "params": create_params({})},
    "dps_vib_example": {"control": DpsExampleField, "params": create_params({"multiline": True, "min_lines": 4})},
    "dps_class_source": {"control": ft.TextField, "params": create_params({})},
    "dps_class_sutta": {"control": ft.TextField, "params": create_params({})},
    "dps_class_example": {"control": DpsExampleField, "params": create_params({"multiline": True, "min_lines": 4})},
    "dps_class_example_translation": {"control": ft.TextField, "params": create_params({})},
    "dps_discourses_source": {"control": ft.TextField, "params": create_params({})},
    "dps_discourses_sutta": {"control": ft.TextField, "params": create_params({})},
    "dps_discourses_example": {"control": DpsExampleField, "params": create_params({"multiline": True, "min_lines": 4})},
    "dps_extra_source": {"control": ft.TextField, "params": create_params({})},
    "dps_extra_sutta": {"control": ft.TextField, "params": create_params({})},
    "dps_extra_example": {"control": DpsExampleField, "params": create_params({"multiline": True, "min_lines": 4})},
    "dps_sbs_class_anki": {"control": ft.TextField, "params": create_params({"tooltip": "which class from Anki deck for Pāli Class"})},
    "dps_sbs_class": {"control": ft.TextField, "params": create_params({"tooltip": "related to which class from the Pāli Course"})},
    "dps_sbs_category": {"control": ft.TextField, "params": create_params({"tooltip": "which sutta from sutta anki deck"})},
    "dps_sbs_patimokkha": {"control": ft.TextField, "params": create_params({"tooltip": "related to Bhikkhu Pātimokkha or Bhikkhu Vibhaṅga"})},
    
    # Hidden test-only fields (not displayed in GUI but available for testing)
    "dps_meaning_1": {"control": ft.TextField, "params": create_params({"disabled": True, "visible": False})},
    "dps_pos": {"control": ft.TextField, "params": create_params({"disabled": True, "visible": False})},
    "dps_verb": {"control": ft.TextField, "params": create_params({"disabled": True, "visible": False})},
    "dps_suffix": {"control": ft.TextField, "params": create_params({"disabled": True, "visible": False})},
    "dps_meaning_lit": {"control": ft.TextField, "params": create_params({"disabled": True, "visible": False})},
    "dps_family_set": {"control": ft.TextField, "params": create_params({"disabled": True, "visible": False})},
}

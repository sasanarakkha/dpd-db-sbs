from typing import Any

import flet as ft

from gui2.dps_example_field import DpsExampleField
from gui2.dps_meaning_field import DpsMeaningField

FieldDef = dict[str, Any]

common_params: dict[str, Any] = {
    "border_color": ft.Colors.BLUE_200,
    "border_radius": 20,
    "text_size": 14,
    "expand": True,
}


def create_params(specific_params: dict[str, Any]) -> dict[str, Any]:
    params = common_params.copy()
    params.update(specific_params)
    return params


def text_field(**overrides: Any) -> FieldDef:
    return {"control": ft.TextField, "params": create_params(overrides)}


def multiline_field(min_lines: int = 2, **overrides: Any) -> FieldDef:
    return text_field(multiline=True, min_lines=min_lines, **overrides)


def example_field(min_lines: int = 4, **overrides: Any) -> FieldDef:
    return {
        "control": DpsExampleField,
        "params": create_params(
            {"multiline": True, "min_lines": min_lines, **overrides}
        ),
    }


def meaning_field(**overrides: Any) -> FieldDef:
    return {"control": DpsMeaningField, "params": create_params(overrides)}


def hidden_text_field() -> FieldDef:
    return text_field(disabled=True, visible=False)


def standalone_triplet(prefix: str) -> dict[str, FieldDef]:
    """Generate the source/sutta/example triplet shared by dhp/pat/vib/discourses/extra/class."""
    return {
        f"{prefix}_source": text_field(),
        f"{prefix}_sutta": text_field(),
        f"{prefix}_example": example_field(4),
    }


dps_field_mapping: dict[str, FieldDef] = {
    "dps_id": text_field(),
    "dps_lemma_1": text_field(),
    "dps_grammar": text_field(),
    "dps_meaning": multiline_field(2),
    "dps_suggestion": multiline_field(3),
    "dps_ru_meaning": meaning_field(
        multiline=True, min_lines=2, tooltip="type Russian meaning"
    ),
    "dps_ru_meaning_lit": meaning_field(tooltip="type Russian literal meaning"),
    "dps_ru_cognate": text_field(tooltip="Russian word which close sounding"),
    "dps_sbs_meaning": multiline_field(2, tooltip="type meaning in SBS PER"),
    "dps_root": text_field(),
    "dps_constriction": text_field(),
    "dps_synonym_antonym": text_field(),
    "dps_notes": multiline_field(3),
    "dps_notes_suggestion": multiline_field(2),
    "dps_ru_notes": multiline_field(2),
    "dps_sbs_notes": multiline_field(2),
    "dps_source_1": text_field(),
    "dps_sutta_1": text_field(),
    "dps_example_1": example_field(5),
    "dps_source_2": text_field(),
    "dps_sutta_2": text_field(),
    "dps_example_2": example_field(5),
    "dps_sbs_source_1": text_field(tooltip="Sutta code using DPR system"),
    "dps_sbs_sutta_1": text_field(tooltip="Sutta name"),
    "dps_sbs_example_1": example_field(4),
    "dps_sbs_chant_pali_1": text_field(),
    "dps_sbs_chant_eng_1": text_field(),
    "dps_sbs_chapter_1": text_field(),
    "dps_sbs_source_2": text_field(),
    "dps_sbs_sutta_2": text_field(),
    "dps_sbs_example_2": example_field(4),
    "dps_sbs_chant_pali_2": text_field(),
    "dps_sbs_chant_eng_2": text_field(),
    "dps_sbs_chapter_2": text_field(),
    **standalone_triplet("dps_dhp"),
    **standalone_triplet("dps_pat"),
    **standalone_triplet("dps_vib"),
    **standalone_triplet("dps_class"),
    "dps_class_example_translation": text_field(),
    "dps_class_extra": {
        "control": ft.Dropdown,
        "params": create_params(
            {
                "options": [ft.dropdown.Option(" ", " "), ft.dropdown.Option("extra")],
                "tooltip": "select 'extra' for extra examples",
            }
        ),
    },
    "dps_class_anki": text_field(tooltip="which class from Anki deck for Pāli Class"),
    **standalone_triplet("dps_discourses"),
    **standalone_triplet("dps_extra"),
    # Hidden test-only fields (not displayed in GUI but available for testing)
    "dps_meaning_1": hidden_text_field(),
    "dps_pos": hidden_text_field(),
    "dps_verb": hidden_text_field(),
    "dps_suffix": hidden_text_field(),
    "dps_meaning_lit": hidden_text_field(),
    "dps_family_set": hidden_text_field(),
}

# -*- coding: utf-8 -*-
import flet as ft
from db.models import DpdHeadword, Russian, SBS
from gui2.dps_field_mapping import dps_field_mapping
from gui2.dps_example_field import DpsExampleField
from gui2.dps_example_stash_manager import DpsExampleStashManager
from gui2.dps_ai_service import translate_with_ai_from_gui
from gui2.toolkit import ToolKit
from tools.meaning_construction import make_meaning_combo
from typing import Any

class DpsFields:
    def __init__(self, view, db_session, toolkit: ToolKit):
        from gui2.dps_view import DpsView
        self.view: DpsView = view
        self.db_session = db_session
        self.toolkit = toolkit
        self.fields: dict[str, ft.TextField | ft.Checkbox | ft.Dropdown | DpsExampleField] = {}
        # Create shared stash manager for all DPS example fields
        self.shared_stash_manager = DpsExampleStashManager(self.toolkit)
        self._build_fields()

    def _build_fields(self):
        # Using a mapping to create fields
        for field_name, properties in dps_field_mapping.items():
            control_type = properties.get("control", ft.TextField)
            params = properties.get("params", {})
            
            # Special handling for DpsExampleField
            if control_type == DpsExampleField:
                # Create DpsExampleField with shared stash manager
                example_field = DpsExampleField(
                    ui=self.view,
                    field_name=field_name,
                    dps_fields=self,
                    toolkit=self.toolkit,
                    stash_manager=self.shared_stash_manager,
                )
                
                # Apply ALL parameters to the internal text field
                text_field = example_field.text_field
                for key, value in params.items():
                    if hasattr(text_field, key):
                        setattr(text_field, key, value)
                
                self.fields[field_name] = example_field
            else:
                # Standard Flet controls
                self.fields[field_name] = control_type(**params)

    def _set_field_value(self, field: Any, value: object) -> None:
        """Set the .value of a control with proper type handling.

        This avoids assigning a str to a Checkbox.value which expects bool | None.
        """
        # Lazy import for type checking without circular imports
        if isinstance(field, ft.Checkbox):
            field.value = bool(value)
        elif isinstance(field, ft.Dropdown):
            # Dropdown.value expects str | None in flet; allow direct assignment
            # Coerce value to str when it's not None to satisfy type checkers
            field.value = str(value) if value is not None else None
        elif isinstance(field, DpsExampleField):
            field.text_field.value = str(value)
        elif isinstance(field, (ft.TextField, ft.Text)):
            field.value = str(value)
        else:
            if hasattr(field, "value"):
                try:
                    setattr(field, "value", value)
                except Exception:
                    setattr(field, "value", str(value))

    def add_to_ui(self, parent_control: ft.Column):
        # Create one row per field with a separate label
        for field_name, field_control in self.fields.items():
            # Skip hidden fields (those with visible=False)
            if hasattr(field_control, 'visible') and field_control.visible is False:
                continue
                
            # Create a label from the field name
            label_text = field_name.replace("dps_", "").replace("_", " ").title()
            label = ft.Text(
                label_text,
                color=ft.Colors.GREY_500,
                size=12,
                width=150,
                selectable=True,
            )

            # Add AI buttons for specific fields
            controls = [label, field_control]
            
            # Add AI button for Russian meaning suggestion
            if field_name == "dps_ru_online_suggestion":
                ai_button = ft.ElevatedButton(
                    "AI",
                    on_click=lambda e, mode="meaning": self._handle_ai_click(e, mode),
                    width=50,
                    height=30,
                    tooltip="Generate Russian translation using AI"
                )
                controls.append(ai_button)
                synonym_button = ft.ElevatedButton(
                    "Syn",
                    on_click=lambda e, mode="meaning": self._handle_ai_click(e, mode, True),
                    width=50,
                    height=30,
                    tooltip="Generate list of Synonyms using AI"
                )
                controls.append(synonym_button)
            
            # Add AI button for notes suggestion
            elif field_name == "dps_notes_online_suggestion":
                ai_button = ft.ElevatedButton(
                    "AI",
                    on_click=lambda e, mode="note": self._handle_ai_click(e, mode),
                    width=50,
                    height=30,
                    tooltip="Generate Russian notes translation using AI"
                )
                controls.append(ai_button)

            row = ft.Row(
                controls=controls,
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            parent_control.controls.append(row)

    def populate_dps_tab(self, headword: DpdHeadword, ru_word: Russian | None, sbs_word: SBS | None):
        """Populate DPS tab with data from the database models."""
        def _update_field(key, value):
            if key in self.fields and value is not None:
                self._set_field_value(self.fields[key], value)

        # Populate DPD info
        _update_field("dps_dpd_id", headword.id)
        _update_field("dps_lemma_1", headword.lemma_1)

        if ru_word and ru_word.ru_meaning_raw:
            _update_field("dps_ru_online_suggestion", ru_word.ru_meaning_raw)

        # Copy dpd values for tests
        _update_field("dps_pos", headword.pos)
        _update_field("dps_family_set", headword.family_set)
        _update_field("dps_suffix", headword.suffix)
        _update_field("dps_verb", headword.verb)
        _update_field("dps_meaning_lit", headword.meaning_lit)
        _update_field("dps_meaning_1", headword.meaning_1)

        # Grammar
        grammar_parts = [headword.grammar]
        if headword.neg: 
            grammar_parts.append(headword.neg)
        if headword.verb: 
            grammar_parts.append(headword.verb)
        if headword.trans: 
            grammar_parts.append(headword.trans)
        if headword.plus_case: 
            grammar_parts.append(f"({headword.plus_case})")
        _update_field("dps_grammar", ", ".join(filter(None, grammar_parts)))

        # Meaning
        meaning = make_meaning_combo(headword)
        if not headword.meaning_1:
            meaning = f"(meaning_2) {meaning}"
        _update_field("dps_meaning", meaning)

        # Russian fields
        if ru_word:
            for key in ru_word.__table__.columns.keys():
                _update_field(f"dps_{key}", getattr(ru_word, key, ""))

        # SBS fields
        if sbs_word:
            for key in sbs_word.__table__.columns.keys():
                _update_field(f"dps_{key}", getattr(sbs_word, key, ""))

        # Root
        if headword.rt:
            root_text = f"{headword.root_key} {headword.rt.root_has_verb} {headword.rt.root_group} {headword.root_sign} ({headword.rt.root_meaning} {headword.rt.root_ru_meaning})"
            if headword.rt.sanskrit_root_ru_meaning:
                root_text += f" sk {headword.rt.sanskrit_root_ru_meaning}"
            _update_field("dps_root", root_text)

        # Other combined fields
        _update_field("dps_base_or_comp", headword.root_base or headword.compound_type)
        _update_field("dps_constr_or_comp_constr", headword.compound_construction or headword.construction)
        syn_ant = []
        if headword.synonym: 
            syn_ant.append(f"(syn) {headword.synonym}")
        if headword.antonym: 
            syn_ant.append(f"(ant): {headword.antonym}")
        _update_field("dps_synonym_antonym", " ".join(syn_ant))
        _update_field("dps_notes", headword.notes)
        _update_field("dps_source_1", headword.source_1)
        _update_field("dps_sutta_1", headword.sutta_1)
        _update_field("dps_example_1", headword.example_1)
        _update_field("dps_source_2", headword.source_2)
        _update_field("dps_sutta_2", headword.sutta_2)
        _update_field("dps_example_2", headword.example_2)

        self.view.page.update()


    def _handle_ai_click(self, e: ft.ControlEvent, mode: str, synonyms: bool = False):
        """Handle AI button click - run AI translation directly (no threading)"""
        # Show loading message
        self.view.update_message(f"AI generating {mode} translation...")
        self.view.page.update()  # Force UI update to show loading message
        
        # Call AI function directly (will block UI temporarily)
        result = translate_with_ai_from_gui(self, mode, synonyms)
        
        if result and not result.startswith("Error:"):
            # Update the appropriate field based on mode
            if mode == "meaning":
                    target_field = self.fields["dps_ru_online_suggestion"]
                    self._set_field_value(target_field, result)
            elif mode == "note":
                    target_field = self.fields["dps_notes_online_suggestion"]
                    self._set_field_value(target_field, result)
            
            self.view.update_message(f"AI {mode} translation completed")
        else:
            # Show error message
            self.view.update_message(f"AI error: {result}")
        
        self.view.page.update()


    def clear_all_fields(self):
        for field in self.fields.values():
            if isinstance(field, (ft.TextField, ft.Text)):
                field.value = ""
                field.error_text = None
            elif isinstance(field, ft.Checkbox):
                field.value = False
            elif isinstance(field, ft.Dropdown):
                field.value = None
            elif isinstance(field, DpsExampleField):
                field.value = ""
                field.error_text = None
        self.view.page.update()

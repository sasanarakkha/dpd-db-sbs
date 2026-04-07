# -*- coding: utf-8 -*-
import flet as ft
import copy
from db.models import DpdHeadword, Russian, SBS
from gui2.dps_field_mapping import dps_field_mapping
from gui2.dps_example_field import DpsExampleField
from gui2.dps_example_stash_manager import DpsExampleStashManager
from gui2.dps_ai_service import translate_with_ai_from_gui
from gui2.dps_meaning_field import DpsMeaningField
from gui2.toolkit import ToolKit
from tools.meaning_construction import make_meaning_combo
from tools.tsv_read_write import read_tsv_dot_dict
from tools.ru_spelling import RuSpellChecker
from typing import Any


class DpsFields:
    def __init__(self, view, db_session, toolkit: ToolKit):
        from gui2.dps_view import DpsView

        self.view: DpsView = view
        self.db_session = db_session
        self.toolkit = toolkit
        self.fields: dict[
            str,
            ft.TextField
            | ft.Checkbox
            | ft.Dropdown
            | DpsExampleField
            | DpsMeaningField,
        ] = {}
        self.field_rows: dict[str, ft.Row] = {}
        # Create shared stash manager for all DPS example fields
        self.shared_stash_manager = DpsExampleStashManager(self.toolkit)
        # Initialize spell checker for Russian fields
        self.russian_spellchecker = RuSpellChecker()
        self._sbs_index_data = []
        self._sbs_chant_options = []
        self._load_sbs_index()
        self._build_fields()

    def _load_sbs_index(self):
        """Load SBS index data for chant dropdowns."""
        try:
            self._sbs_index_data = read_tsv_dot_dict(self.view.dpspth.sbs_index_path)
            pali_chants = sorted(
                [i.pali_chant for i in self._sbs_index_data if i.pali_chant]
            )
            # Add empty option at the beginning for clearing dropdowns
            self._sbs_chant_options = [ft.dropdown.Option(key=" ", text=" ")] + [
                ft.dropdown.Option(key=chant, text=chant) for chant in pali_chants
            ]
        except Exception as e:
            print(f"Error loading SBS index: {e}")

    def _build_fields(self):
        # Using a mapping to create fields
        for field_name, properties in dps_field_mapping.items():
            control_type = properties.get("control", ft.TextField)
            params = copy.deepcopy(properties.get("params", {}))

            if field_name in ["dps_sbs_chant_pali_1", "dps_sbs_chant_pali_2"]:
                control_type = ft.Dropdown
                params["options"] = self._sbs_chant_options

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

            # Special handling for DpsMeaningField
            elif control_type == DpsMeaningField:
                # Create DpsMeaningField with Russian spell checker
                meaning_field = DpsMeaningField(
                    ui=self.view,
                    field_name=field_name,
                    dps_fields=self,
                    spellchecker=self.russian_spellchecker,
                )

                # Apply parameters to the internal meaning field
                for key, value in params.items():
                    if hasattr(meaning_field.meaning_field, key):
                        setattr(meaning_field.meaning_field, key, value)

                self.fields[field_name] = meaning_field

            else:
                # Standard Flet controls
                if control_type == ft.Dropdown:
                    # Ensure all dropdowns have proper empty option handling
                    if "options" not in params:
                        # If no options are provided, add an empty option
                        params["options"] = [ft.dropdown.Option(" ", " ")]

                    # Check if this is a dropdown that should have an empty option
                    if params["options"] and not any(
                        opt.key == " " for opt in params["options"]
                    ):
                        # If options exist but no empty option, add one at the beginning
                        params["options"] = [ft.dropdown.Option(" ", " ")] + params[
                            "options"
                        ]

                    if field_name in ["dps_sbs_chant_pali_1", "dps_sbs_chant_pali_2"]:
                        params["on_change"] = self._handle_sbs_chant_change
                    params["editable"] = True
                    params["enable_filter"] = True

                self.fields[field_name] = control_type(**params)

    def _set_field_value(self, field: Any, value: object) -> None:
        """Set the .value of a control with proper type handling.

        This avoids assigning a str to a Checkbox.value which expects bool | None.
        """
        # Lazy import for type checking without circular imports
        if isinstance(field, ft.Checkbox):
            field.value = bool(value)
        elif isinstance(field, ft.Dropdown):
            # Special handling for dropdowns to ensure proper option matching
            if value is None:
                # For None values, set to empty string to match the empty option
                field.value = ""
            else:
                # Coerce value to str when it's not None to satisfy type checkers
                field.value = str(value)
        elif isinstance(field, DpsExampleField):
            field.text_field.value = str(value)
        elif isinstance(field, DpsMeaningField):
            field.value = str(value)
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
            if hasattr(field_control, "visible") and field_control.visible is False:
                continue

            # Create a label from the field name
            label_text = field_name.replace("dps_", "").replace("_", " ").title()
            label = ft.Text(
                label_text,
                color=ft.Colors.GREY_500,
                size=15,
                width=150,
                selectable=True,
            )

            # Add AI buttons for specific fields
            controls = [label, field_control]

            # Add AI button for Russian meaning suggestion
            if field_name == "dps_suggestion":
                ai_button = ft.ElevatedButton(
                    "AI",
                    on_click=lambda e, mode="meaning": self._handle_ai_click(e, mode),
                    width=50,
                    height=30,
                    tooltip="Generate Russian translation using AI",
                )
                controls.append(ai_button)
                synonym_button = ft.ElevatedButton(
                    "Syn",
                    on_click=lambda e, mode="meaning": self._handle_ai_click(
                        e, mode, True
                    ),
                    width=50,
                    height=30,
                    tooltip="Generate list of Synonyms using AI",
                )
                controls.append(synonym_button)
                copy_split_button = ft.ElevatedButton(
                    "Copy",
                    on_click=self._handle_copy_split_click,
                    width=80,
                    height=30,
                    tooltip="Copy and split content from suggestion to meaning fields",
                )
                controls.append(copy_split_button)

            # Add AI button for notes suggestion
            elif field_name == "dps_notes_suggestion":
                ai_button = ft.ElevatedButton(
                    "AI",
                    on_click=lambda e, mode="note": self._handle_ai_click(e, mode),
                    width=50,
                    height=30,
                    tooltip="Generate Russian notes translation using AI",
                )
                controls.append(ai_button)
                copy_notes_button = ft.ElevatedButton(
                    "Copy",
                    on_click=self._handle_copy_notes_click,
                    width=80,
                    height=30,
                    tooltip="Copy content from suggestion to ru_notes field",
                )
                controls.append(copy_notes_button)

            row = ft.Row(
                controls=controls,
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            parent_control.controls.append(row)
            self.field_rows[field_name] = row

    def populate_dps_tab(
        self, headword: DpdHeadword, ru_word: Russian | None, sbs_word: SBS | None
    ):
        """Populate DPS tab with data from the database models."""

        def _update_field(key, value):
            if key in self.fields and value is not None:
                self._set_field_value(self.fields[key], value)

        # Populate DPD info
        _update_field("dps_id", headword.id)
        _update_field("dps_lemma_1", headword.lemma_1)

        if ru_word and ru_word.ru_meaning_raw:
            _update_field("dps_suggestion", ru_word.ru_meaning_raw)

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
        if headword.compound_type:
            _update_field("dps_constriction", headword.compound_construction)
        else:
            _update_field("dps_constriction", headword.construction)

        syn_ant = []
        if headword.synonym:
            syn_ant.append(f"(syn): {headword.synonym}")
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
                target_field = self.fields["dps_suggestion"]
                self._set_field_value(target_field, result)
            elif mode == "note":
                target_field = self.fields["dps_notes_suggestion"]
                self._set_field_value(target_field, result)

            self.view.update_message(f"AI {mode} translation completed")
        else:
            # Show error message
            self.view.update_message(f"AI error: {result}")

        self.view.page.update()

    def _handle_copy_split_click(self, e: ft.ControlEvent):
        """Handle Copy & Split button click - split Russian suggestion into meaning and literal meaning"""
        # Get the content to be split and copied
        suggestion_field = self.fields["dps_suggestion"]
        content = (
            str(suggestion_field.value) if suggestion_field.value is not None else ""
        )

        if not content:
            self.view.update_message("Russian suggestion field is empty")
            return

        # Split content based on delimiters
        delimiters = ["досл.", "букв.", "|", "буквально", "дословно", "лит."]

        for delimiter in delimiters:
            if delimiter in content:
                parts = content.split(delimiter, 1)
                before_delimiter = parts[0].rstrip("; ").strip()
                after_delimiter = parts[1].strip() if len(parts) > 1 else ""

                # Update the target fields
                meaning_field = self.fields["dps_ru_meaning"]
                lit_meaning_field = self.fields["dps_ru_meaning_lit"]

                # Update the GUI for meaning_key and lit_meaning_key
                self._set_field_value(meaning_field, before_delimiter)
                self._set_field_value(lit_meaning_field, after_delimiter)
                self.view.update_message("Content copied and split successfully")
                return

        # If none of the delimiters are found, just update the meaning field
        meaning_field = self.fields["dps_ru_meaning"]
        self._set_field_value(meaning_field, content)
        self.view.update_message("Content copied (no delimiter found)")
        return

    def _handle_copy_notes_click(self, e: ft.ControlEvent):
        """Handle Copy button click for notes - copy suggestion to ru_notes field."""
        # Get the content to be copied
        suggestion_field = self.fields["dps_notes_suggestion"]
        content = (
            str(suggestion_field.value) if suggestion_field.value is not None else ""
        )

        if not content:
            self.view.update_message("Notes suggestion field is empty")
            return

        # Update the target field
        ru_notes_field = self.fields["dps_ru_notes"]
        self._set_field_value(ru_notes_field, content)
        self.view.update_message("Content copied to Russian Notes")

    def _handle_sbs_chant_change(self, e: ft.ControlEvent):
        """Update chant_eng and chapter when a pali_chant is selected."""
        selected_chant = e.control.value
        field_name = next(
            (name for name, ctrl in self.fields.items() if ctrl == e.control), None
        )

        if not selected_chant or not field_name:
            return

        # Determine the index (1 or 2) from the field name
        index = field_name.split("_")[-1]

        # If empty option is selected, clear the related fields
        if selected_chant == " ":
            eng_chant_field = self.fields.get(f"dps_sbs_chant_eng_{index}")
            chapter_field = self.fields.get(f"dps_sbs_chapter_{index}")

            if eng_chant_field:
                self._set_field_value(eng_chant_field, "")
            if chapter_field:
                self._set_field_value(chapter_field, "")
            self.view.page.update()
            return

        # Find the corresponding data for non-empty selections
        for item in self._sbs_index_data:
            if item.pali_chant == selected_chant:
                eng_chant_field = self.fields.get(f"dps_sbs_chant_eng_{index}")
                chapter_field = self.fields.get(f"dps_sbs_chapter_{index}")

                if eng_chant_field:
                    self._set_field_value(eng_chant_field, item.english_chant)
                if chapter_field:
                    self._set_field_value(chapter_field, item.chapter)
                self.view.page.update()
                return

    def filter_fields(self, visible_fields: list[str] | None) -> None:
        """
        Filters the visibility of fields in the UI.
        If visible_fields is None, all fields are shown.
        Otherwise, only fields in the list are shown.
        """
        for field_name, row in self.field_rows.items():
            if visible_fields is None:
                row.visible = True
            else:
                row.visible = field_name in visible_fields

    def clear_all_fields(self):
        for field_name, field in self.fields.items():
            if isinstance(field, (ft.TextField, ft.Text)):
                field.value = ""
                field.error_text = None
            elif isinstance(field, ft.Checkbox):
                field.value = False
            elif isinstance(field, ft.Dropdown):
                field.value = (
                    None  # For all dropdowns, None is the correct way to clear
                )
            elif isinstance(field, DpsExampleField):
                field.value = ""
                field.error_text = None
                # Clear additional fields within DpsExampleField
                if hasattr(field, "word_to_find_field"):
                    field.word_to_find_field.value = ""
                    field.word_to_find_field.error_text = None
                if hasattr(field, "book_dropdown"):
                    field.book_dropdown.value = None
                if hasattr(field, "bold_field"):
                    field.bold_field.value = ""
                if hasattr(field, "counter_field"):
                    field.counter_field.value = ""
            elif isinstance(field, DpsMeaningField):
                field.value = ""
                field.error_text = None
                # Clear the "Add spelling" field
                if hasattr(field, "add_to_dict_field"):
                    field.add_to_dict_field.value = ""
        self.view.page.update()

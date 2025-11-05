# -*- coding: utf-8 -*-
import copy
import csv

import flet as ft

from db.models import DpdHeadword, Russian, SBS
from sqlalchemy import or_
from gui2.dpd_fields_functions import clean_lemma_1
from gui2.dps_fields import DpsFields
from gui2.dps_db_helpers import fetch_ru, fetch_sbs
from gui2.dps_fields_lists import VIB_FIELDS, CLASS_FIELDS
from gui2.dps_example_field import DpsExampleField
from gui2.history import HistoryManager
from gui2.mixins import PopUpMixin
from gui2.toolkit import ToolKit
from tools.paths_dps import DPSPaths
from tools.fast_api_utils import request_dpd_server

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class DpsView(ft.Column, PopUpMixin):
    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
    ) -> None:
        # Main container column - does not scroll, expands vertically
        super().__init__(
            expand=True,  # Main column expands
            controls=[],  # Controls defined below
            spacing=5,
        )

        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit

        self._db = self.toolkit.db_manager
        self.dpspth = DPSPaths()
        
        # Initialize DPS-specific history manager
        self.dps_history_manager = HistoryManager(self.toolkit, max_size=25)
        # Override the history path to be DPS-specific
        self.dps_history_manager._history_path = self.dpspth.history_json_path
        # Reload history from the correct file after setting the path
        self.dps_history_manager._load()
        self.dps_history_manager.register_refresh_callback(self._update_history_dropdown)

        # Initialize DPS test manager
        from gui2.dps_test_manager import DpsTestManager
        self.dps_test_manager = DpsTestManager(self._db)  # type: ignore
        # Don't load tests here - load them when Test button is clicked

        self.dps_fields: DpsFields
        self.headword: DpdHeadword | None = None
        self.headword_original: DpdHeadword | None = None
        self.ru_word: Russian | None = None
        self.sbs_word: SBS | None = None
        self.tests_passed: bool = False
        
        # Load translation examples from CSV file
        self._formatted_translation_hint = self._load_translation_examples()

        self._message_field = ft.TextField(
            "",
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
            border=ft.InputBorder.OUTLINE,
            color=ft.Colors.BLUE_200,
            expand_loose=True,
            expand=True,
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=15),
            hint_text="Messages",
            read_only=True,
            text_size=17,
            width=700,
        )

        self._enter_id_or_lemma_field = ft.TextField(
            "",
            autofocus=True,
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
            expand_loose=True,
            expand=True,
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=15),
            hint_text="Enter ID or Lemma",
            on_submit=self._click_edit_headword,
            text_size=17,
            width=400,
        )

        self._history_dropdown = ft.Dropdown(
            hint_text="History",
            hint_style=ft.TextStyle(color=ft.Colors.BLUE_200),
            options=[],
            expand=True,
            expand_loose=True,
            border_radius=20,
            text_size=17,
            on_change=self._handle_history_selection,
        )

        # Create hint button for translation examples
        self._translation_hint_button = ft.IconButton(
            icon=ft.Icons.INFO,
            icon_size=16,
            tooltip=self._formatted_translation_hint,
            style=ft.ButtonStyle(
                padding=ft.padding.all(4),
                overlay_color=ft.Colors.TRANSPARENT
            )
        )

        types_of_comp = """
            acc - dutiyā
            instr - tatiyā
            dat - catutthā
            abl - pañcamī
            gen - chaṭṭhī
            loc - sattamī
            """

        # Create hint button for types_of_comp
        self._types_of_comp_button = ft.IconButton(
            icon=ft.Icons.INFO,
            icon_size=16,
            tooltip=types_of_comp,
            style=ft.ButtonStyle(
                padding=ft.padding.all(4),
                overlay_color=ft.Colors.TRANSPARENT
            )
        )

        self._next_ru_button = ft.ElevatedButton(
            "Next Ru",
            on_click=self._click_next_ru,
            tooltip="Find next word with raw Russian meaning to be edited",
            width=150,
        )

        self._next_note_button = ft.ElevatedButton(
            "Next Note",
            on_click=self._click_next_note,
            tooltip="Find next word with Russian note to be edited",
            width=150,
        )

        self._clear_button = ft.ElevatedButton(
            "Clear All",
            on_click=self._click_clear_all,
            tooltip="Clear all fields",
            width=150,
        )

        # --- Field Filter Radio Buttons ---
        self._filter_radios = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="all", label="All"),
                    ft.Radio(value="vib", label="Vib"),
                    ft.Radio(value="class", label="Class"),
                ]
            ),
            value="all",  # Default selection
            on_change=self._handle_filter_change,
        )

        self._top_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self._enter_id_or_lemma_field,
                            self._translation_hint_button,
                            self._types_of_comp_button,
                            self._next_ru_button,
                            self._next_note_button,
                            self._clear_button,
                            self._history_dropdown,
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row([self._message_field, self._filter_radios]),
                ],
            ),
            border=ft.Border(
                top=ft.BorderSide(1, HIGHLIGHT_COLOUR),
                bottom=ft.BorderSide(1, HIGHLIGHT_COLOUR),
            ),
            padding=10,
            alignment=ft.alignment.center,
        )

        self._middle_section = self._build_middle_section()

        # Initialize history dropdown (without internal update call to avoid timing errors)
        self._update_history_dropdown()

        self._bottom_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Test",
                                on_click=self._click_run_tests,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Update DB",
                                on_click=self._click_update_db,
                                width=BUTTON_WIDTH,
                            ),
                        ],
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.all(10),
        )

        self.controls = [
            self._top_section,
            self._middle_section,
            self._bottom_section,
        ]


    def _load_translation_examples(self) -> str:
        """Load and format translation examples from CSV file for tooltip display."""
        try:
            csv_path = self.dpspth.translation_example_path
            if not csv_path.exists():
                return "Translation examples file not found."
            
            formatted_lines = []
            with open(csv_path, 'r', encoding='utf-8') as file:
                # The file is TSV format with tabs
                reader = csv.DictReader(file, delimiter='\t')
                for row in reader:
                    pos = row.get('pos', '').strip()
                    examples = row.get('examples', '').strip()
                    if pos and examples:
                        formatted_lines.append(f"{pos}: {examples}")
            
            if formatted_lines:
                return "\n".join(formatted_lines)
            else:
                return "No translation examples found in file."
                
        except Exception as e:
            return f"Error loading translation examples: {str(e)}"

    def update_message(self, message: str) -> None:
        self._message_field.value = message
        self.page.update()


    def _handle_filter_change(self, e: ft.ControlEvent) -> None:
        """Handles changes in the field filter RadioGroup."""
        filter_type = e.control.value
        visible_fields = None  # Default to all

        if filter_type == "vib":
            visible_fields = VIB_FIELDS
        elif filter_type == "class":
            visible_fields = CLASS_FIELDS

        self.dps_fields.filter_fields(visible_fields)
        self.page.update()


    def _click_edit_headword(self, _e: ft.ControlEvent) -> None:
        id_or_lemma = (self._enter_id_or_lemma_field.value or "").strip()
        if not id_or_lemma:  # Check if the field was empty
            self.update_message("Enter an ID or Lemma.")
            return

        headword = self._db.get_headword_by_id_or_lemma(id_or_lemma)
        if not headword:
            self.update_message("Headword not found.")
            return

        self.headword = headword
        self.headword_original = copy.deepcopy(headword)
        self.ru_word = fetch_ru(self._db.db_session, headword.id)
        self.sbs_word = fetch_sbs(self._db.db_session, headword.id)
        self.tests_passed = False  # Reset test state when loading new word

        self.dps_fields.populate_dps_tab(headword, self.ru_word, self.sbs_word)
        self.add_headword_to_dps_examples()  # Populate word_to_find fields with stem
        self.update_message(f"Loaded {headword.lemma_1}")

    def _click_next_ru(self, e: ft.ControlEvent) -> None:
        """Find and load the next headword needing Russian meaning review."""
        self.update_message("Searching for next 'Ru' word...")
        word_id, count = self._get_next_word_ru()

        if word_id:
            self._enter_id_or_lemma_field.value = str(word_id)
            self._click_edit_headword(e)
            self.update_message(f"Loaded next 'Ru' word. {count} left.")
        else:
            self.update_message("No more 'Ru' words to process.")

    def _click_next_note(self, e: ft.ControlEvent) -> None:
        """Find and load the next headword needing Russian note review."""
        self.update_message("Searching for next 'Note' word...")
        word_id, count = self._get_next_note_ru()

        if word_id:
            self._enter_id_or_lemma_field.value = str(word_id)
            self._click_edit_headword(e)
            self.update_message(f"Loaded next 'Note' word. {count} left.")
        else:
            self.update_message("No more 'Note' words to process.")

    def _get_next_word_ru(self) -> tuple[int | None, int]:
        """Fetch the ID of the next word needing Russian meaning processing."""
        query = self._db.db_session.query(DpdHeadword).join(Russian).join(SBS).filter(
            DpdHeadword.meaning_1 != "",
            DpdHeadword.example_1 != "",
            Russian.ru_meaning == "",
            SBS.sbs_patimokkha == "vib",
            # Russian.ru_meaning_raw != "",
        )
        
        count = query.count()
        word = query.first()
        
        if word:
            return word.id, count
        return None, 0

    def _get_next_note_ru(self) -> tuple[int | None, int]:
        """Fetch the ID of the next word needing Russian note processing."""
        query = self._db.db_session.query(DpdHeadword).join(Russian).join(SBS).filter(
            Russian.ru_notes.like("%ИИ%"),
            or_(
                SBS.sbs_index.isnot(None),
                SBS.sbs_category != '',
                SBS.sbs_index.isnot(None),
                SBS.sbs_patimokkha != '',
            )
        )

        # Count before filtering on sbs_index
        count = query.count()
        
        # Further filter in Python for integer field
        for word in query.all():
            if word.sbs and word.sbs.sbs_index is not None and word.sbs.sbs_index != 0:
                return word.id, count
        
        # Fallback if no word with a non-zero sbs_index is found
        return None, 0


    def _update_history_dropdown(self) -> None:
        """Populate history dropdown with DPS history"""
        history = self.dps_history_manager.get_history()
        options = []
        for item in history:
            options.append(ft.dropdown.Option(
                key=str(item["id"]),
                text=f"{item['id']}: {item['lemma_1']}"
            ))
        self._history_dropdown.options = options
        # Remove self._history_dropdown.update() - let page update handle it


    def _handle_history_selection(self, e: ft.ControlEvent) -> None:
        """Load selected headword from DPS history"""
        selected_id = self._history_dropdown.value
        if selected_id:
            self._enter_id_or_lemma_field.value = selected_id
            self._click_edit_headword(e)  # Reuse existing load logic


    def _build_middle_section(self) -> ft.Column:
        self.dps_fields = DpsFields(self, self._db, self.toolkit)
        middle_section = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=5,
        )
        self.dps_fields.add_to_ui(middle_section)
        return middle_section


    def add_headword_to_dps_examples(self) -> None:
        """Add headword to all DPS example fields - EXACT same as Pass2Add"""
        lemma_1_field = self.dps_fields.fields.get("dps_lemma_1")
        if lemma_1_field and lemma_1_field.value:
            lemma_value = str(lemma_1_field.value)  # Ensure string type
            lemma_clean = clean_lemma_1(lemma_value)  # Same cleaning function
            stem = lemma_clean[:-1]  # Same stem logic
            
            # Update all DPS example fields
            for field_name, field in self.dps_fields.fields.items():
                if isinstance(field, DpsExampleField) and hasattr(field, 'word_to_find_field'):
                    field.word_to_find_field.value = stem
                    field.word_to_find_field.update()  # Force UI update

    def _click_clear_all(self, _e: ft.ControlEvent | None = None) -> None:
        """Clear all fields by rebuilding the middle section."""
        # Rebuild middle section to ensure a clean state for all controls
        self._middle_section = self._build_middle_section()

        # Update view controls with the new middle section
        self.controls = [self._top_section, self._middle_section, self._bottom_section]

        # Re-apply the current filter to the newly created fields
        current_filter = self._filter_radios.value
        if current_filter != "all":
            if self._filter_radios.uid:
                self._handle_filter_change(ft.ControlEvent(target=self._filter_radios.uid, name="change", data=current_filter, control=self._filter_radios, page=self.page))
        # Clear relevant top-section fields and reset state
        self._enter_id_or_lemma_field.value = ""
        self.tests_passed = False
        self.update_message("Fields cleared.")
        self.page.update()

    def _click_run_tests(self, _e: ft.ControlEvent) -> None:
        """Run tests on current field values - using enhanced DPS test manager"""
        self.update_message("Loading tests...")
        
        # Get current field values
        values = self._get_current_field_values()
        
        # Run DPS tests using enhanced test manager with interactive dialog
        self.dps_test_manager.run_all_tests(self, values)


    def _click_update_db(self, e: ft.ControlEvent) -> None:
        # Check if tests have been run and passed
        if not self.tests_passed:
            self.update_message("tests first")
            return
        
        self.update_message("Updating DB...")
        
        # Get current headword ID
        dpd_id_field = self.dps_fields.fields.get("dps_id")
        if not dpd_id_field or not dpd_id_field.value:
            self.update_message("Error: No headword ID found")
            return
        
        try:
            headword_id = int(dpd_id_field.value)
        except ValueError:
            self.update_message("Error: Invalid headword ID")
            return
        
        # Update Russian table
        self._update_russian_table(headword_id)
        
        # Update SBS table
        self._update_sbs_table(headword_id)
        
        # Commit changes
        try:
            self._db.db_session.commit()
            self.update_message("SBS and Russian tables updated")
            
            # Add to DPS history after successful DB update
            if self.headword:
                self.dps_history_manager.add_item(self.headword.id, self.headword.lemma_1)
                request_dpd_server(str(self.headword.id))
                
                self._update_history_dropdown()
                self.page.update()
                
                self.page.set_clipboard(self.headword.lemma_1)  # Copy headword to clipboard               
                self._click_clear_all(e)  # Clear all fields after successful update
                
        except Exception as ex:
            self._db.db_session.rollback()
            self.update_message(f"Error updating DB: {str(ex)}")


    def _update_russian_table(self, headword_id: int) -> None:
        """Update Russian table with fields starting with dps_ru_*"""
        # Get or create Russian record
        ru_word = fetch_ru(self._db.db_session, headword_id)
        if not ru_word:
            ru_word = Russian(id=headword_id)
            self._db.db_session.add(ru_word)
        
        values = self._get_current_field_values()

        # Update Russian fields
        for field_name in self.dps_fields.fields:
            if field_name.startswith("dps_ru_"):
                ru_field_name = field_name.replace("dps_", "")
                if hasattr(ru_word, ru_field_name):
                    setattr(ru_word, ru_field_name, values.get(field_name, ""))
                else:
                    print(f"ERROR: Russian field {ru_field_name} not found in model")
                    self.update_message(f"ERROR: Russian field {ru_field_name} not found in model")


    def _update_sbs_table(self, headword_id: int) -> None:
        """Update SBS table with fields starting with specified prefixes"""
        # Get or create SBS record
        sbs_word = fetch_sbs(self._db.db_session, headword_id)
        if not sbs_word:
            sbs_word = SBS(id=headword_id)
            self._db.db_session.add(sbs_word)
        
        values = self._get_current_field_values()

        # Get current values from database before updating
        current_sbs = fetch_sbs(self._db.db_session, headword_id)
        old_vib_example = current_sbs.vib_example if current_sbs else ""
        old_pat_example = current_sbs.pat_example if current_sbs else ""
        old_sbs_patimokkha = current_sbs.sbs_patimokkha if current_sbs else ""
        
        # Special handling for class_example_translation - bulk update all matching records
        class_example_translation_field = self.dps_fields.fields.get("dps_class_example_translation")
        if class_example_translation_field:
            new_value = values.get("dps_class_example_translation", "")
            
            # Get current value from database
            current_value = current_sbs.class_example_translation if current_sbs else ""
            
            # If values are different
            if current_value != new_value:
                # Case 1: Current value exists and new value exists - bulk update all matching records
                if current_value and new_value:
                    matching_records = self._db.db_session.query(SBS).filter(
                        SBS.class_example_translation == current_value
                    ).all()
                    
                    # Update all matching records
                    for record in matching_records:
                        record.class_example_translation = new_value
                # Case 2: Current value is empty but new value exists - update only current record
                elif not current_value and new_value and current_sbs:
                    current_sbs.class_example_translation = new_value
                # Case 3: Current value exists but new value is empty - update only current record
                elif current_value and not new_value and current_sbs:
                    current_sbs.class_example_translation = new_value
        
        # SBS field prefixes to process
        sbs_prefixes = ["sbs_", "dhp_", "pat_", "vib_", "class_", "discourses_"]
        
        # Track new values for vib_example and pat_example
        new_vib_example = ""
        new_pat_example = ""
        
        # Update SBS fields (excluding class_example_translation which was handled above)
        for field_name in self.dps_fields.fields:
            if field_name.startswith("dps_"):
                # Skip class_example_translation as it's already handled
                if field_name == "dps_class_example_translation":
                    continue

                # Check if this is an SBS-related field
                for prefix in sbs_prefixes:
                    if field_name.startswith(f"dps_{prefix}"):
                        sbs_field_name = field_name.replace("dps_", "")
                        if hasattr(sbs_word, sbs_field_name):
                            field_value = values.get(field_name, "")
                            setattr(sbs_word, sbs_field_name, field_value)

                            # Track vib_example and pat_example values for auto-population logic
                            if sbs_field_name == "vib_example":
                                new_vib_example = field_value
                            elif sbs_field_name == "pat_example":
                                new_pat_example = field_value
                                
                        else:
                            print(f"ERROR: SBS field {sbs_field_name} not found in model")
                            self.update_message(f"ERROR: SBS field {sbs_field_name} not found in model")
                        break
        
        # Auto-populate sbs_patimokkha logic
        if not old_sbs_patimokkha:  # Only if sbs_patimokkha is currently empty
            # Check if vib_example changed from empty to non-empty
            if not old_vib_example and new_vib_example:
                sbs_word.sbs_patimokkha = "vib"
                # print(f"DEBUG: Auto-populated sbs_patimokkha to 'vib' because vib_example was added")
            
            # Check if pat_example changed from empty to non-empty
            elif not old_pat_example and new_pat_example:
                sbs_word.sbs_patimokkha = "pat"
                # print(f"DEBUG: Auto-populated sbs_patimokkha to 'pat' because pat_example was added")


    def _get_current_field_values(self) -> dict[str, str]:
        """Get current values from all DPS fields"""
        values = {}
        for field_name, field_control in self.dps_fields.fields.items():
            # Use .value for TextFields, Dropdowns, etc. and handle None
            values[field_name] = field_control.value or ""

        return values

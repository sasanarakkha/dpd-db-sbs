# -*- coding: utf-8 -*-
import copy

import flet as ft

from db.models import DpdHeadword, Russian, SBS
from gui2.dps_fields import DpsFields
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
        self.dps_history_manager = HistoryManager(self.toolkit, max_size=20)
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

        self._message_field = ft.TextField(
            "",
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
            border=ft.InputBorder.OUTLINE,
            color=ft.Colors.BLUE_200,
            expand_loose=True,
            expand=True,
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            hint_text="Messages",
            read_only=True,
            text_size=14,
            width=700,
        )

        self._enter_id_or_lemma_field = ft.TextField(
            "",
            autofocus=True,
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
            expand_loose=True,
            expand=True,
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            hint_text="Enter ID or Lemma",
            on_submit=self._click_edit_headword,
            text_size=14,
            width=400,
        )

        self._history_dropdown = ft.Dropdown(
            hint_text="History",
            hint_style=ft.TextStyle(color=ft.Colors.BLUE_200),
            options=[],
            expand=True,
            expand_loose=True,
            border_radius=20,
            text_size=14,
            on_change=self._handle_history_selection,
        )

        self._top_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self._enter_id_or_lemma_field,
                            self._history_dropdown,
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row([self._message_field]),
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
                            ft.ElevatedButton(
                                "Clear",
                                on_click=self._click_clear_all,
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


    def update_message(self, message: str) -> None:
        self._message_field.value = message
        self.page.update()


    def _click_edit_headword(self, e: ft.ControlEvent) -> None:
        if self._enter_id_or_lemma_field.value:
            id_or_lemma = self._enter_id_or_lemma_field.value.strip()
        if not id_or_lemma:
            self.update_message("Enter an ID or Lemma.")
            return

        headword = self._db.get_headword_by_id_or_lemma(id_or_lemma)
        if not headword:
            self.update_message("Headword not found.")
            return

        self.headword = headword
        self.headword_original = copy.deepcopy(headword)
        self.ru_word = self._db.fetch_ru(headword.id)
        self.sbs_word = self._db.fetch_sbs(headword.id)
        self.tests_passed = False  # Reset test state when loading new word

        self.dps_fields.populate_dps_tab(headword, self.ru_word, self.sbs_word)
        self.update_message(f"Loaded {headword.lemma_1}")


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


    def _click_clear_all(self, e: ft.ControlEvent) -> None:
        self.dps_fields.clear_all_fields()
        self._enter_id_or_lemma_field.value = ""  # Clear the ID/Lemma input field
        self.tests_passed = False  # Reset test state when clearing fields
        self.update_message("Fields cleared.")


    def _click_run_tests(self, e: ft.ControlEvent) -> None:
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
        dpd_id_field = self.dps_fields.fields.get("dps_dpd_id")
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
                
        except Exception as ex:
            self._db.db_session.rollback()
            self.update_message(f"Error updating DB: {str(ex)}")


    def _update_russian_table(self, headword_id: int) -> None:
        """Update Russian table with fields starting with dps_ru_*"""
        # Get or create Russian record
        ru_word = self._db.fetch_ru(headword_id)
        if not ru_word:
            ru_word = Russian(id=headword_id)
            self._db.db_session.add(ru_word)
        
        # Update Russian fields
        for field_name, field in self.dps_fields.fields.items():
            if field_name.startswith("dps_ru_"):
                ru_field_name = field_name.replace("dps_", "")
                if hasattr(ru_word, ru_field_name):
                    setattr(ru_word, ru_field_name, field.value or "")
                    print(f"DEBUG: Updated Russian field {ru_field_name} = {field.value}")
                else:
                    print(f"ERROR: Russian field {ru_field_name} not found in model")
                    self.update_message(f"ERROR: Russian field {ru_field_name} not found in model")


    def _update_sbs_table(self, headword_id: int) -> None:
        """Update SBS table with fields starting with specified prefixes"""
        # Get or create SBS record
        sbs_word = self._db.fetch_sbs(headword_id)
        if not sbs_word:
            sbs_word = SBS(id=headword_id)
            self._db.db_session.add(sbs_word)
        
        # SBS field prefixes to process
        sbs_prefixes = ["sbs_", "dhp_", "pat_", "vib_", "class_", "discourses_"]
        
        # Update SBS fields
        for field_name, field in self.dps_fields.fields.items():
            if field_name.startswith("dps_"):
                # Check if this is an SBS-related field
                for prefix in sbs_prefixes:
                    if field_name.startswith(f"dps_{prefix}"):
                        sbs_field_name = field_name.replace("dps_", "")
                        if hasattr(sbs_word, sbs_field_name):
                            setattr(sbs_word, sbs_field_name, field.value or "")
                        else:
                            print(f"ERROR: SBS field {sbs_field_name} not found in model")
                            self.update_message(f"ERROR: SBS field {sbs_field_name} not found in model")
                        break


    def _get_current_field_values(self) -> dict[str, str]:
        """Get current values from all DPS fields"""
        values = {}
        for field_name, field in self.dps_fields.fields.items():
            if hasattr(field, "value"):
                values[field_name] = field.value or ""
            elif isinstance(field, ft.Checkbox):
                values[field_name] = "True" if field.value else "False"
            else:
                values[field_name] = ""
        return values

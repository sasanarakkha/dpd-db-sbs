import copy
import flet as ft

from db.models import DpdHeadword
from gui2.class_daily_log import DailyLog
from gui2.class_database import DatabaseManager
from gui2.class_mixins import PopUpMixin
from gui2.class_dpd_fields import DpdFields
from gui2.class_pass2_file_manager import Pass2AutoFileManager
from gui2.def_make_dpd_headword import make_dpd_headword_from_dict
from tools.fast_api_utils import request_dpd_server

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class EditView(ft.Column, PopUpMixin):
    def __init__(self, page: ft.Page, db: DatabaseManager, daily_log: DailyLog) -> None:
        # Main container column - does not scroll, expands vertically
        super().__init__(
            expand=True,  # Main column expands
            controls=[],  # Controls defined below
            spacing=5,
        )
        self.page: ft.Page = page
        self._db = db
        self._daily_log = daily_log
        self._pass2_auto_file_manager = Pass2AutoFileManager()
        self.headword: DpdHeadword | None = None
        self.headword_original: DpdHeadword | None = None

        self._message_field = ft.Text("", expand=True)
        self._next_pass2_auto_button = ft.ElevatedButton(
            "NextPass2Auto",
            width=BUTTON_WIDTH,
            on_click=self._click_load_next_pass2_entry,
        )
        self._enter_id_or_lemma_field = ft.TextField(
            "",
            width=400,
            expand=True,
            expand_loose=True,
            on_submit=self._click_edit_headword,
        )
        self._clone_headword_button = ft.ElevatedButton(
            "Clone", on_click=self._click_clone_headword
        )
        self._edit_headword_button = ft.ElevatedButton(
            "Edit", on_click=self._click_edit_headword
        )

        self._history_dropdown = ft.Dropdown(
            hint_text="Select History",
            options=[
                ft.dropdown.Option("Placeholder 1"),
                ft.dropdown.Option("Placeholder 2"),
                ft.dropdown.Option("Placeholder 3"),
            ],
            width=BUTTON_WIDTH,
            border_radius=20,
            text_style=ft.TextStyle(color=ft.Colors.BLUE_200),
            text_size=14,
        )

        self._top_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            # self._clone_headword_button,
                            self._enter_id_or_lemma_field,
                            self._edit_headword_button,
                            self._next_pass2_auto_button,
                            self._history_dropdown,
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row(controls=[self._message_field]),
                ],
            ),
            border=ft.Border(
                top=ft.BorderSide(1, HIGHLIGHT_COLOUR),
                bottom=ft.BorderSide(1, HIGHLIGHT_COLOUR),
            ),
            padding=10,
            alignment=ft.alignment.center,
        )

        self._dpd_fields = DpdFields(self, self._db)
        self._middle_section = ft.Column(
            scroll=ft.ScrollMode.AUTO, expand=True, spacing=5
        )
        self._dpd_fields.add_to_ui(self._middle_section, include_add_fields=True)

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
                                "Add to DB",
                                on_click=self._click_add_to_db,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Delete",
                                # on_click=self.handle_delete_click,
                                width=BUTTON_WIDTH,
                                on_hover=self._on_delete_hover,
                            ),
                        ],
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Button",
                                # on_click=self.handle_sandhi_ok_click,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Button",
                                # on_click=self.handle_add_to_sandhi_click,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Button",
                                # on_click=self.handle_add_to_variants_click,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Button",
                                # on_click=self.handle_add_to_spelling_mistakes_click,
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

    def _on_delete_hover(self, e: ft.ControlEvent) -> None:
        e.control.bgcolor = ft.Colors.RED if e.data == "true" else None
        e.control.color = "white" if e.data == "true" else None
        e.control.update()

    def update_message(self, message: str) -> None:
        self._message_field.value = message
        self.page.update()

    def _click_edit_headword(self, e: ft.ControlEvent) -> None:
        id_or_lemma = self._enter_id_or_lemma_field.value

        if id_or_lemma:
            headword = self._db.get_headword_by_id_or_lemma(id_or_lemma)
            if headword:
                self.clear_all_fields()
                self.headword = headword
                self.headword_original = copy.deepcopy(
                    headword
                )  # Store original for ID comparison
                self._dpd_fields.update_db_fields(headword)
                if self.headword is not None:
                    self.update_message(f"loaded {self.headword.lemma_1}")
                    if (
                        self.headword.id is not None
                        and str(self.headword.id)
                        in self._pass2_auto_file_manager.responses
                    ):
                        to_add = self._pass2_auto_file_manager.get_headword(
                            str(self.headword.id)
                        )
                        self._dpd_fields.update_add_fields(to_add)
            else:
                self.update_message("headword not found")
        else:
            self.update_message("you're shooting blanks")

    def _click_clone_headword(self, e: ft.ControlEvent) -> None:
        pass

    def _click_load_next_pass2_entry(self, e: ft.ControlEvent | None = None) -> None:
        """Load next pass2 entry into the view."""
        headword_id, pass2_auto_data = (
            self._pass2_auto_file_manager.get_next_headword_data()
        )

        if headword_id is not None:
            self._dpd_fields.clear_fields()

            self.headword = self._db.get_headword_by_id(int(headword_id))
            if self.headword is not None:
                self._dpd_fields.update_db_fields(self.headword)

            self._dpd_fields.update_add_fields(pass2_auto_data)

        else:
            self._message_field.value = "Current Pass2: None"
            self._dpd_fields.clear_fields(target="all")  # Clear all fields

        self.update()

    def clear_all_fields(self):
        self._dpd_fields.clear_fields(target="all")

    def _click_run_tests(self, e: ft.ControlEvent):
        """Run tests on current field values"""
        values = self._dpd_fields.get_current_values()
        passed, failures = self._dpd_fields.run_tests(values)

        if passed:
            self.update_message("All tests passed!")
        else:
            self.update_message(f"{len(failures)} tests failed")
            # Highlight error columns
            for failure in failures:
                if failure["error_column"]:
                    field = self._dpd_fields.get_field(failure["error_column"])
                    if field:
                        field.error_text = failure["test_name"]
                        field.update()
            self._dpd_fields.show_test_failures(self.page)

    def _click_add_to_db(self, e: ft.ControlEvent):
        id_field = self._dpd_fields.fields.get("id")
        id_value: int | None = int(id_field.value) if id_field else None

        if (
            hasattr(self, "headword")
            and self.headword
            and hasattr(self, "headword_original")
            and self.headword_original
            and id_value == self.headword_original.id
        ):
            # Update existing word
            for field_name, field in self._dpd_fields.fields.items():
                if hasattr(self.headword, field_name):
                    setattr(self.headword, field_name, field.value)
            try:
                self._db.db_session.commit()
                committed, message = True, ""
            except Exception as ex:
                self._db.db_session.rollback()
                committed, message = False, str(ex)
        else:
            # Create new word (whether first time or ID changed)
            field_data = {
                field_name: field.value
                for field_name, field in self._dpd_fields.fields.items()
                if hasattr(DpdHeadword, field_name)
            }
            new_word = make_dpd_headword_from_dict(field_data)
            committed, message = self._db.add_word_to_db(new_word)

        if committed:
            request_dpd_server(str(id_value))
            message = self._daily_log.increment("pass2")
            self.clear_all_fields()
        else:
            self.update_message(f"Commit failed: {message}")

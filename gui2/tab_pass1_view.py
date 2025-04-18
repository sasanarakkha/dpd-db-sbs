import flet as ft
from gui2.class_database import DatabaseManager
from gui2.class_mixins import PopUpMixin
from gui2.class_dpd_fields import DpdFields

from rich import print

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class Pass1View(ft.Column, PopUpMixin):
    def __init__(self, page: ft.Page, db: DatabaseManager) -> None:
        # Main column: expands, does NOT scroll
        super().__init__(
            expand=True,
            controls=[],
            spacing=5,
        )
        from gui2.tab_pass1_controller import Pass1Controller

        PopUpMixin.__init__(self)
        self.page: ft.Page = page
        self.db: DatabaseManager = db
        self.controller = Pass1Controller(self, db)
        self.dpd_fields: DpdFields

        # --- Top Section Controls ---
        self.message_field = ft.Text("", color=HIGHLIGHT_COLOUR, selectable=True)
        self.book_options = [
            ft.dropdown.Option(key=item, text=item)
            for item in self.controller.pass1_books_list
        ]
        self.books_dropdown = ft.Dropdown(
            autofocus=True,
            options=self.book_options,
            width=300,
            text_size=14,
            border_color=HIGHLIGHT_COLOUR,
        )
        self.word_in_text = ft.TextField(
            value="",
            width=LABEL_WIDTH,
            color=HIGHLIGHT_COLOUR,
            expand=True,
        )

        # Create the top section Column
        self.top_section = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("", width=LABEL_WIDTH),
                        self.message_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("book", width=LABEL_WIDTH, color=LABEL_COLOUR),
                        self.books_dropdown,
                        ft.ElevatedButton(
                            "Process Book",
                            width=BUTTON_WIDTH,
                            on_click=self.handle_process_book_click,
                        ),
                        ft.ElevatedButton(
                            "Refresh DB",
                            width=BUTTON_WIDTH,
                            on_click=self.handle_refresh_db_click,
                        ),
                        ft.ElevatedButton(
                            "Clear All",
                            width=BUTTON_WIDTH,
                            on_click=self.clear_all_fields,
                        ),
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("word_in_text", width=LABEL_WIDTH, color=LABEL_COLOUR),
                        self.word_in_text,
                    ],
                ),
            ],
            spacing=5,
        )

        # Initialize middle section
        self.middle_section = self._build_middle_section()

        self.bottom_section = ft.Container(
            height=50,
            content=ft.Row(
                [
                    ft.ElevatedButton(
                        "Add to DB",
                        on_click=self.handle_add_to_db_click,
                        width=BUTTON_WIDTH,
                    ),
                    ft.ElevatedButton(
                        "Sandhi OK",
                        on_click=self.handle_sandhi_ok_click,
                        width=BUTTON_WIDTH,
                    ),
                    ft.ElevatedButton(
                        "Sandhi Correction",
                        on_click=self.handle_add_to_sandhi_click,
                        width=BUTTON_WIDTH,
                    ),
                    ft.ElevatedButton(
                        "Pass", on_click=self.handle_pass_click, width=BUTTON_WIDTH
                    ),
                    ft.ElevatedButton(
                        "Delete", on_click=self.handle_delete_click, width=BUTTON_WIDTH
                    ),
                ],
            ),
            padding=ft.padding.all(10),
        )

        # --- Set Main View Controls ---
        self.controls = [
            self.top_section,
            self.middle_section,
            self.bottom_section,
        ]

    def load_database(self):
        self.controller.db.make_inflections_lists()

    def update_message(self, message: str):
        self.message_field.value = message
        self.page.update()

    def handle_process_book_click(self, e):
        if self.books_dropdown.value:
            self.controller.process_book(self.books_dropdown.value)

    def handle_refresh_db_click(self, e):
        self.db.new_db_session()
        self.update_message("Database refreshed")

    def handle_add_to_db_click(self, e):
        self.controller.make_dpdheadword_and_add_to_db()

    def handle_add_to_sandhi_click(self, e):
        current_word = self.word_in_text.value
        if not current_word:
            self.update_message("No word selected.")
            return

        self.show_popup(
            page=self.page,
            prompt_message="Enter construction",
            initial_value=self.word_in_text.value or "",
            on_submit=self.process_sandhi_popup_result,
        )

    def handle_sandhi_ok_click(self, e):
        current_word = self.word_in_text.value
        if current_word:
            self.controller.update_sandhi_checked(current_word)
            self.update_message(f"{current_word} added to sandhi checked")

    def handle_pass_click(self, e):
        self.clear_all_fields()
        self.controller.get_next_item()
        self.controller.load_into_gui()

    def handle_delete_click(self, e):
        print(self.dpd_fields)
        if self.word_in_text.value:
            self.controller.remove_word_and_save_json()
            self.clear_all_fields()
            self.controller.get_next_item()
            self.controller.load_into_gui()
        else:
            self.update_message("No word_in_text.")

    def _build_middle_section(self) -> ft.Column:
        """Build and return the middle section with DpdFields."""
        self.dpd_fields = DpdFields(self, self.db)
        middle_section = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[],
            spacing=5,
        )

        visible_fields = [
            "lemma_1",
            "lemma_2",
            "pos",
            "grammar",
            "meaning_2",
            "root_key",
            "family_root",
            "root_sign",
            "root_base",
            "family_compound",
            "construction",
            "stem",
            "pattern",
            "example_1",
            "translation_1",
            "example_2",
            "translation_2",
            "comments",
        ]
        self.dpd_fields.add_to_ui(middle_section, visible_fields=visible_fields)
        return middle_section

    def clear_all_fields(self, e=None):
        """Clear all fields by rebuilding the middle section."""
        # Rebuild middle section
        self.middle_section = self._build_middle_section()

        # Update view controls with new middle section
        self.controls = [self.top_section, self.middle_section, self.bottom_section]

        # Clear word_in_text separately
        self.word_in_text.value = ""
        self.word_in_text.error_text = None

        self.update_message("")
        self.page.update()

    def process_sandhi_popup_result(self, breakup_value):
        """Handles the result after the sandhi popup closes."""

        if breakup_value is not None and self.word_in_text.value:
            self.controller.update_sandhi_corrections(
                self.word_in_text.value, breakup_value
            )
            self.update_message(f"Sandhi added for {self.word_in_text.value}")
        else:
            self.update_message("Sandhi input cancelled.")

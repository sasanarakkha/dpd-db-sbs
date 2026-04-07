# -*- coding: utf-8 -*-
import flet as ft

from gui2.dpd_fields_classes import DpdTextField
from gui2.dpd_fields_functions import clean_example
from gui2.dps_example_stash_manager import DpsExampleStashManager
from gui2.flet_functions import (
    highlight_word_in_sentence,
)
from gui2.toolkit import ToolKit
from tools.clean_sentence import split_pali_sentence_into_words
from tools.cst_source_sutta_example import (
    CstSourceSuttaExample,
    find_cst_source_sutta_example,
)
from tools.speech_marks import SpeechMarkManager
from tools.tsv_read_write import read_tsv_dict
from difflib import SequenceMatcher

book_codes: dict[str, str] = {
    # vinaya
    "VIN1 Pārājika": "vin1",
    "VIN2 Pācittiya": "vin2",
    "VIN3 Mahāvagga": "vin3",
    "VIN4 Cūlavagga": "vin4",
    "VIN5 Parivāra": "vin5",
    # dn
    "DN1 Sīlakkhandhavagga": "dn1",
    "DN2 Mahāvagga": "dn2",
    "DN3 Pāthikavagga": "dn3",
    # mn
    "MN1 Mūlapaṇṇāsa": "mn1",
    "MN2 Majjhimapaṇṇāsa": "mn2",
    "MN3 Uparipaṇṇāsa": "mn3",
    # sn
    "SN1 sagāthāvagga": "sn1",
    "SN2 nidānavagga": "sn2",
    "SN3 khandhavagga": "sn3",
    "SN4 saḷāyatanavagga": "sn4",
    "SN5 mahāvagga": "sn5",
    # an
    "AN1 ekakanipāta": "an1",
    "AN2 dukanipāta": "an2",
    "AN3 tikanipāta": "an3",
    "AN4 catukkanipāta": "an4",
    "AN5 pañcakanipāta": "an5",
    "AN6 chakkanipāta": "an6",
    "AN7 sattakanipāta": "an7",
    "AN8 aṭṭhakanipāta": "an8",
    "AN9 navakanipāta": "an9",
    "AN10 dasakanipāta": "an10",
    "AN11 ekādasakanipāta": "an11",
    # kn
    "KP khuddakapāṭha": "kn1",
    "DHP dhammapada": "kn2",
    "UD udāna": "kn3",
    "ITI itivuttaka": "kn4",
    "SNP suttanipāta": "kn5",
    "VV vimanavatthu": "kn6",
    "PV petavatthu": "kn7",
    "TH theragāthā": "kn8",
    "THI therīgāthā": "kn9",
    "APA therāpadāna": "kn10",
    "API therīapadāna": "kn11",
    "BV buddhavaṃsa": "kn12",
    "CP cariyapitaka": "kn13",
    "JA jataka": "kn14",
    "NIDD1 mahaniddesa": "kn15",
    "NIDD2 culaniddesa": "kn16",
    "PM patisambhidamagga": "kn17",
    "MIL milindapañha": "kn18",
    "NP nettippakaraṇa": "kn19",
    "PTP peṭakopadesa": "kn20",
    # abhidhamma
    "ABH1 dhammasaṅgaṇī": "abh1",
    "ABH2 vibhaṅga": "abh2",
    "ABH3 dhātukathā": "abh3",
    "ABH4 puggalapaññatti": "abh4",
    "ABH5 kathāvatthu": "abh5",
    "ABH6 yamaka": "abh6",
    "ABH7 paṭṭhāna": "abh7",
    # commentaries
    "VINa Commentary": "vina",
    "DNa Dīgha Commentary": "dna",
    "MNa Majjhima Commentary": "mna",
    "SNa Saṃyutta Commentary": "sna",
    "ANa Aṅguttara Commentary": "ana",
    "KPa Khuddakapātha Commentary  ": "kn1a",
    "DHPa Dhammapada Commentary": "kn2a",
    "UDa Udāna Commentary": "kn3a",
    "ITIa Itivuttaka Commentary": "kn4a",
    "SNPa Suttanipāta Commentary": "kn5a",
    "VVa Vimānavatthu Commentary": "kn6a",
    "PVa Petavatthu Commentary": "kn7a",
    "THa Theragāthā Commentary": "kn8a",
    "THIa Therigāthā Commentary": "kn9a",
    "APAa Apadāna Commentary": "kn10a",
    "BVa Buddhavaṃsa Commentary": "kn12a",
    "CPa Cariyapitaka Commentary": "kn13a",
    "JAa Jātaka Commentary": "kn14a",
    "NIDD1a Mahāniddesa Commentary": "kn15a",
    "NIDD2a Cūlaniddesa Commentary": "kn16a",
    "PMa Patisambhidhāmagga Commentary": "kn17a",
    "NPa Nettipakarana Commentary": "kn19a",
    "VISM Visuddhimagga": "vism",
    "VISMa Visuddhimagga Ṭīkā": "visma",
    # aññā
    "abhidhānappadīpikā": "ap",
    "abhidhānappadīpikāṭīkā": "apt",
}


class DpsExampleField(ft.Column):
    def __init__(
        self,
        ui,
        field_name: str,
        dps_fields,
        toolkit: ToolKit,
        stash_manager=None,
        on_focus=None,
        on_change=None,
        on_submit=None,
        on_blur=None,
        simple_mode: bool = False,
    ):
        from gui2.dps_view import DpsView

        self.ui: DpsView = ui
        self.field_name = field_name
        self.dps_fields = dps_fields

        self.toolkit: ToolKit = toolkit

        self.speech_marks_manager: SpeechMarkManager = self.toolkit.speech_marks_manager
        self.speech_marks_dict = self.speech_marks_manager.get_speech_marks()

        self.simple_mode = simple_mode
        # Use passed stash manager or create new one if not provided
        self.stash_manager = stash_manager or DpsExampleStashManager(self.ui.toolkit)
        # Initialize archive index as instance variable
        self.archived_example_index = 0
        super().__init__(
            expand=True,
        )
        self.page: ft.Page = ui.page

        self.text_field = DpdTextField(
            name=field_name,
            multiline=True,
            on_focus=self.update_counter,
            on_change=self.clean_text,
            on_submit=on_submit,
            on_blur=on_blur,
        )

        # --- Controls for Toggle Visibility ---
        if not self.simple_mode:
            self.bold_field = ft.TextField(
                "",
                width=240,
                label="bold",
                label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=15),
                expand=True,
                dense=True,
                text_size=15,
                on_submit=self.click_bold_example,
                on_blur=self._handle_last_control_blur,
            )
            self.counter_field = ft.Text(
                "",
                size=15,
                width=40,
                expand=False,
            )

            self.book_options = [
                ft.dropdown.Option(key=item, text=item) for item in book_codes.keys()
            ]

            self.book_dropdown = ft.Dropdown(
                options=self.book_options,
                width=300,
                text_size=17,
                label="book",
                label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=15),
                editable=True,
                enable_filter=True,
                border_color=ft.Colors.GREY_800,
                border_radius=20,
                border_width=1,
                on_blur=self._handle_book_blur,
            )

            self.word_to_find_field = ft.TextField(
                "",
                width=300,
                label="word to find",
                label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=15),
                on_submit=self._click_search_dialog_ok,
                border_radius=20,
            )

            # Toggle Button
            self._toggle_tools_button = ft.IconButton(
                icon=ft.Icons.VISIBILITY_OFF_OUTLINED,
                tooltip="Show Tools",
                on_click=self._toggle_tools_visibility,
                icon_color=ft.Colors.BLUE_GREY_300,
            )

            # Search row (initially hidden)
            self._search_row = ft.Row(
                [
                    self.book_dropdown,
                    self.word_to_find_field,
                ],
                spacing=0,
                visible=False,
            )

            # Action buttons row (initially hidden)
            self._actions_row = ft.Row(
                [
                    ft.ElevatedButton("Clean", on_click=self.click_clean_example),
                    ft.ElevatedButton("Delete", on_click=self.click_delete_example),
                    ft.ElevatedButton("Swap", on_click=self.click_swap_example),
                    ft.ElevatedButton("Stash", on_click=self._click_stash_example),
                    ft.ElevatedButton(
                        "Reload",
                        on_click=self._click_reload_example,
                    ),
                    ft.ElevatedButton(
                        "Last",
                        on_click=self._click_last_example,
                    ),
                    ft.ElevatedButton(
                        "Arch",
                        on_click=self._click_arch_example,
                    ),
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                visible=False,
            )

        self.controls = []
        # Add toggle button and hidden rows if not in simple mode
        if not self.simple_mode:
            self.controls.append(ft.Row([self._toggle_tools_button]))
            self.controls.append(self._search_row)
            self.controls.append(self._actions_row)

        self.controls.append(
            self.text_field,
        )
        if not self.simple_mode:
            self.controls.append(
                ft.Row([self.bold_field, self.counter_field], spacing=5)
            )

        self.spacing = 0
        self.cst_examples: list[CstSourceSuttaExample] = []
        self.example_index: str = ""

    @property
    def value(self):
        return self.text_field.value

    @property
    def field(self):
        return self.text_field

    @value.setter
    def value(self, value):
        self.text_field.value = value

    @property
    def error_text(self):
        """Gets the error text from the internal text field."""
        return self.text_field.error_text

    @error_text.setter
    def error_text(self, value):
        """Sets the error text on the internal text field and updates it."""
        self.text_field.error_text = value
        self.text_field.update()

    # --- Toggle Visibility Handling ---
    def _toggle_tools_visibility(self, e: ft.ControlEvent | None = None):
        """Toggles the visibility of the search and action rows."""
        are_visible = not self._search_row.visible
        self._search_row.visible = are_visible
        self._actions_row.visible = are_visible

        # Update button icon and tooltip
        if are_visible:
            self._toggle_tools_button.icon = ft.Icons.VISIBILITY_OUTLINED
            self._toggle_tools_button.tooltip = "Hide Tools"
            self.book_dropdown.focus()
        else:
            self._toggle_tools_button.icon = ft.Icons.VISIBILITY_OFF_OUTLINED
            self._toggle_tools_button.tooltip = "Show Tools"
        self.page.update()

    def _click_search_dialog_ok(self, e: ft.ControlEvent):
        """Handles search submission (e.g., from word_to_find_field on_submit)."""
        self.click_book_and_word(e)

    def _handle_book_blur(self, e: ft.ControlEvent):
        self.word_to_find_field.focus()
        self.page.update()

    def _handle_last_control_blur(self, e: ft.ControlEvent):
        """Hides the tools if they are visible when the last control loses focus.
        Also adds apostrophes, hyphenations and saves current example"""

        if self._search_row.visible:
            self._toggle_tools_visibility(None)

        fields_dict = self.get_fields()

        # Save current example to stash
        example_field = fields_dict.get("example")
        if example_field and hasattr(example_field, 'value') and example_field.value:
            # Create dictionary with field values
            stash_dict: dict[str, str] = {}
            for field_name, field in fields_dict.items():
                if field and hasattr(field, 'value') and field.value:
                    stash_dict[field_name] = field.value
            
            if stash_dict:
                self.stash_manager.last_example = stash_dict

        # handle hyphenations and apostrophes
        if example_field and hasattr(example_field, 'value') and example_field.value and ("'" in example_field.value or "-" in example_field.value):
            self._handle_hyphens_and_apostrophes(example_field.value)

    def _handle_hyphens_and_apostrophes(self, text):
        text_list: list[str] = split_pali_sentence_into_words(text)
        for word in text_list:
            if "-" in word or "'" in word:
                clean_word = word.replace("-", "").replace("'", "")
                self.speech_marks_dict = (
                    self.speech_marks_manager.update_variants(clean_word, word)
                )

    def click_book_and_word(self, e: ft.ControlEvent):
        self.word_to_find_field.error_text = None
        if self.book_dropdown.value and self.word_to_find_field.value:
            self.cst_examples = find_cst_source_sutta_example(
                book_codes[self.book_dropdown.value],
                self.word_to_find_field.value,
            )
            if self.cst_examples:
                self.choose_example()
            else:
                self.word_to_find_field.error_text = "no example found"
        self.word_to_find_field.focus()
        self.page.update()

    def choose_example(self):
        if not self.cst_examples:
            return

        # Limit the number of examples to prevent UI issues
        examples_to_show = self.cst_examples[:50]
        example_list = []

        for counter, i in enumerate(examples_to_show):
            source, sutta, example = i
            example_list.append(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Radio(width=30, value=str(counter)),
                                ft.Text(
                                    source,
                                    selectable=True,
                                    color=ft.Colors.BLUE_200,
                                ),
                                ft.Text(
                                    sutta,
                                    selectable=True,
                                    color=ft.Colors.BLUE_200,
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Text("", width=30),
                                ft.Text(
                                    spans=highlight_word_in_sentence(
                                        self.word_to_find_field.value, example
                                    ),
                                    expand=True,
                                    selectable=True,
                                ),
                            ]
                        ),
                    ],
                )
            )

        radio_group = ft.RadioGroup(
            content=ft.Column(
                controls=example_list,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            on_change=self.update_example_index,
        )

        self.choose_example_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                controls=[radio_group],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(25),
            actions=[
                ft.TextButton("OK", on_click=self.click_choose_example_ok),
                ft.TextButton("Cancel", on_click=self.click_choose_example_cancel),
            ],
        )

        self.page.open(self.choose_example_dialog)
        self.page.update()

    def update_example_index(self, e):
        self.example_index = e.control.value

    def click_choose_example_cancel(self, e: ft.ControlEvent):
        self.choose_example_dialog.open = False
        self.page.update()

    def get_fields(self) -> dict[str, ft.TextField | None]:
        """Return all relevant fields for the current example field as a dictionary."""
        # Extract example type and index from field name
        # e.g., "dps_sbs_example_1" -> type="sbs", index="1"
        # e.g., "dps_dhp_example" -> type="dhp", index=None
        # e.g., "dps_example_1" -> type="dpd", index="1"
        parts = self.field_name.split("_")
        
        # Handle different field name structures
        if len(parts) == 4:
            # 4-part field names: "dps_sbs_example_1", "dps_sbs_example_2"
            example_type = parts[1]  # "sbs"
            index = parts[3]  # "1" or "2"
        elif len(parts) == 3:
            # 3-part field names: "dps_dhp_example", "dps_pat_example", etc.
            example_type = parts[1]  # "dhp", "pat", "vib", etc.
            index = None  # No index for single examples
            
            # Special case for DPD examples: "dps_example_1", "dps_example_2"
            if example_type == "example" and parts[2] in ["1", "2"]:
                example_type = "dpd"
                index = parts[2]  # "1" or "2"
        else:
            # Fallback for unexpected field names
            example_type = "sbs"  # default
            index = "1"  # default

        fields_dict: dict[str, ft.TextField | None] = {}

        # Construct field names based on type and index
        if index:
            # Indexed examples (SBS examples 1 and 2, DPD examples 1 and 2)
            # Special handling for DPD examples - they use different field naming convention
            if example_type == "dpd":
                source_field_name = f"dps_source_{index}"
                sutta_field_name = f"dps_sutta_{index}"
            else:
                source_field_name = f"dps_{example_type}_source_{index}"
                sutta_field_name = f"dps_{example_type}_sutta_{index}"
            
            # Add SBS-specific fields for SBS examples
            if example_type == "sbs":
                fields_dict["chant_pali"] = self.dps_fields.fields.get(f"dps_sbs_chant_pali_{index}")
                fields_dict["chant_eng"] = self.dps_fields.fields.get(f"dps_sbs_chant_eng_{index}")
                fields_dict["chapter"] = self.dps_fields.fields.get(f"dps_sbs_chapter_{index}")
        else:
            # Non-indexed examples (DHP, PAT, VIB, CLASS, DISCOURSES)
            source_field_name = f"dps_{example_type}_source"
            sutta_field_name = f"dps_{example_type}_sutta"
            
            # Add class-specific field for class examples
            if example_type == "class":
                fields_dict["translation"] = self.dps_fields.fields.get("dps_class_example_translation")
                fields_dict["extra"] = self.dps_fields.fields.get("dps_class_extra")
                fields_dict["anki"] = self.dps_fields.fields.get("dps_class_anki")

        # Add core fields
        fields_dict["source"] = self.dps_fields.fields.get(source_field_name)
        fields_dict["sutta"] = self.dps_fields.fields.get(sutta_field_name)
        fields_dict["example"] = self.dps_fields.fields.get(self.field_name)

        return fields_dict

    def click_choose_example_ok(self, e: ft.ControlEvent):
        self.choose_example_dialog.open = False
        self.page.update()

        # add back into page
        cst_example = self.cst_examples[int(self.example_index)]
        fields_dict = self.get_fields()
        
        source_field = fields_dict.get("source")
        sutta_field = fields_dict.get("sutta")
        example_field = fields_dict.get("example")
        
        if source_field:
            source_field.value = cst_example.source
        if sutta_field:
            sutta_field.value = cst_example.sutta
        if example_field:
            example_field.value = clean_example(
                cst_example.example, self.speech_marks_manager
            )
        
        # Automatically populate word_to_find_field with stem (Pass2Add style)
        searched_word = self.word_to_find_field.value
        if searched_word and len(searched_word) > 1:  # Ensure word has at least 2 characters
            stem = searched_word[:-1]  # Remove last character - exact same logic as Pass2Add
            self.word_to_find_field.value = stem
            self.word_to_find_field.update()  # Force immediate UI update
            self.word_to_find_field.focus()  # Focus on the field for quick editing
        
        self.page.update()

    def click_bold_example(self, e: ft.ControlEvent):
        bold_word = e.control.value
        if self.value:
            self.value = self.value.replace(bold_word, f"<b>{bold_word}</b>")
        self.bold_field.focus()
        self.update()

    def click_clean_example(self, e: ft.ControlEvent):
        if self.value:
            self.value = self.value.replace("<b>", "").replace("</b>", "")
            self.update()

    def click_swap_example(self, e: ft.ControlEvent):
        # For DPS, we'll implement swap between sbs_example_1 and sbs_example_2
        # and between dps_example_1 and dps_example_2
        if "sbs_example_1" in self.field_name:
            self._swap_examples("sbs", "1", "2")
        elif "sbs_example_2" in self.field_name:
            self._swap_examples("sbs", "2", "1")
        elif "dps_example_1" in self.field_name:
            self._swap_examples("dpd", "1", "2")
        elif "dps_example_2" in self.field_name:
            self._swap_examples("dpd", "2", "1")
        # Add similar logic for other example types if needed

    def _swap_examples(self, example_type: str, from_index: str, to_index: str):
        """Swap examples between two indices of the same type"""
        source_from = self.dps_fields.fields.get(f"dps_{example_type}_source_{from_index}")
        sutta_from = self.dps_fields.fields.get(f"dps_{example_type}_sutta_{from_index}")
        example_from = self.dps_fields.fields.get(f"dps_{example_type}_example_{from_index}")

        source_to = self.dps_fields.fields.get(f"dps_{example_type}_source_{to_index}")
        sutta_to = self.dps_fields.fields.get(f"dps_{example_type}_sutta_{to_index}")
        example_to = self.dps_fields.fields.get(f"dps_{example_type}_example_{to_index}")

        # Check if all fields exist and have value attribute
        if (source_from and source_to and sutta_from and sutta_to and 
            example_from and example_to and
            hasattr(source_from, 'value') and hasattr(source_to, 'value') and
            hasattr(sutta_from, 'value') and hasattr(sutta_to, 'value') and
            hasattr(example_from, 'value') and hasattr(example_to, 'value')):
            
            # Swap values
            source_x = source_from.value
            sutta_x = sutta_from.value
            example_x = example_from.value

            source_from.value = source_to.value
            sutta_from.value = sutta_to.value
            example_from.value = example_to.value

            source_to.value = source_x
            sutta_to.value = sutta_x
            example_to.value = example_x

            self.page.update()

    def click_delete_example(self, e: ft.ControlEvent):
        fields_dict = self.get_fields()
        
        # Clear all fields in the dictionary
        for field in fields_dict.values():
            if field:
                field.value = ""

        # For SBS examples, also clear the additional chant and chapter fields
        parts = self.field_name.split("_")
        if len(parts) == 4 and parts[1] == "sbs":
            # This is an SBS example field like "dps_sbs_example_1" or "dps_sbs_example_2"
            index = parts[3]  # "1" or "2"
            
            # Clear chant and chapter fields
            chant_pali_field = self.dps_fields.fields.get(f"dps_sbs_chant_pali_{index}")
            chant_eng_field = self.dps_fields.fields.get(f"dps_sbs_chant_eng_{index}")
            chapter_field = self.dps_fields.fields.get(f"dps_sbs_chapter_{index}")
            
            if chant_pali_field:
                chant_pali_field.value = ""
            if chant_eng_field:
                chant_eng_field.value = ""
            if chapter_field:
                chapter_field.value = ""

        self.page.update()

    def _click_stash_example(self, e: ft.ControlEvent):
        """Stashes all relevant fields for the current example."""
        fields_dict = self.get_fields()
        
        # Create dictionary with field values
        stash_dict: dict[str, str] = {}
        for field_name, field in fields_dict.items():
            if field and field.value:
                stash_dict[field_name] = field.value
        
        if stash_dict:
            self.stash_manager.stash_shared_example(stash_dict)
            self.ui.update_message("Stashed current example data")
        else:
            self.ui.update_message("No data to stash")

    def _click_reload_example(self, e: ft.ControlEvent):
        """Reloads stashed data into all relevant fields."""
        stashed_data = self.stash_manager.reload_shared_example()
        if stashed_data:
            fields_dict = self.get_fields()
            for field_name, field in fields_dict.items():
                if field and field_name in stashed_data:
                    field.value = stashed_data[field_name]
            
            self.page.update()
            self.ui.update_message("Reloaded stashed example data")
        else:
            self.ui.update_message("No stashed data found")

    def _click_last_example(self, e: ft.ControlEvent):
        """Loads the last saved example from stash."""
        if last_example := self.stash_manager.last_example:
            fields_dict = self.get_fields()
            for field_name, field in fields_dict.items():
                if field and field_name in last_example:
                    field.value = last_example[field_name]
            
            self.page.update()

    def _click_arch_example(self, e: ft.ControlEvent):
        """Loads an example from the archive."""
        current_id = self.ui.headword.id if self.ui.headword else ""
        if not current_id:
            self.ui.update_message("No headword loaded")
            return
            
        ex_1 = self.dps_fields.fields["dps_sbs_example_1"].value
        ex_2 = self.dps_fields.fields["dps_sbs_example_2"].value
        ex_3 = self.dps_fields.fields["dps_dhp_example"].value
        ex_4 = self.dps_fields.fields["dps_pat_example"].value
        ex_5 = self.dps_fields.fields["dps_vib_example"].value
        ex_6 = self.dps_fields.fields["dps_class_example"].value
        ex_7 = self.dps_fields.fields["dps_discourses_example"].value

        new_index = self._handle_archive_example(
            current_id, ex_1, ex_2, ex_3, ex_4, ex_5, ex_6, ex_7,
            self.archived_example_index
        )
        
        self.archived_example_index = new_index
        self.page.update()

    def paragraphs_are_similar_sbs(self, paragraph1, paragraph2, threshold):
        """Check if two paragraphs are similar based on a similarity threshold."""
        matcher = SequenceMatcher(None, paragraph1, paragraph2)
        return matcher.ratio() >= threshold

    def _handle_archive_example(self, current_id, ex_1, ex_2, ex_3, ex_4, ex_5, ex_6, ex_7, index):
        """Handle archive example logic."""
        word_data = read_tsv_dict(self.ui.dpspth.sbs_archive)
        input_examples = {ex_1, ex_2, ex_3, ex_4, ex_5, ex_6, ex_7}
        total_examples = 4  # Check all 4 examples from archive
        
        for row in word_data:
            if row.get("id") == str(current_id):
                sbs_examples = [
                    row.get("sbs_example_1"),
                    row.get("sbs_example_2"),
                    row.get("sbs_example_3"),
                    row.get("sbs_example_4"),
                ]
                
                sbs_sources = [row.get("sbs_source_1", ""), row.get("sbs_source_2", ""), row.get("sbs_source_3", ""), row.get("sbs_source_4", "")]
                sbs_suttas = [row.get("sbs_sutta_1", ""), row.get("sbs_sutta_2", ""), row.get("sbs_sutta_3", ""), row.get("sbs_sutta_4", "")]

                for i in range(total_examples):
                    example_index = (index + i) % total_examples
                    sbs_example = sbs_examples[example_index]
                    
                    if sbs_example and all(
                        not self.paragraphs_are_similar_sbs(sbs_example, input_ex, 0.9)
                        for input_ex in input_examples if input_ex
                    ):
                        self.dps_fields.fields["dps_extra_source"].value = sbs_sources[example_index]
                        self.dps_fields.fields["dps_extra_sutta"].value = sbs_suttas[example_index]
                        self.dps_fields.fields["dps_extra_example"].value = sbs_example
                        
                        return (example_index + 1) % total_examples
                        
                self.ui.update_message("No unique examples")
                return index
                
        self.ui.update_message("ID not found")
        return index
    def clean_text(self, e: ft.ControlEvent):
        self.text_field.value = (
            e.control.value.replace(" ...", "…")
            .replace("...", "…")
            .replace("'nti", "n'ti")
        )
        self.update_counter(e)
        self.page.update()

    def update_counter(self, e: ft.ControlEvent):
        max_length = 300
        if self.text_field.value and getattr(self, "counter_field", None):
            clean_text = self.text_field.value.replace("<b>", "").replace("</b>", "")
            text_len = len(clean_text)
            self.counter_field.value = str(text_len)

            if text_len > max_length:
                self.text_field.border_color = ft.Colors.RED
                self.text_field.color = ft.Colors.RED
                self.text_field.error_text = str(text_len - max_length)
            else:
                self.text_field.border_color = None
                self.text_field.color = None
                self.text_field.error_text = None

            self.page.update()

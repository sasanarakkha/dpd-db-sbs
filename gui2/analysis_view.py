import csv
import flet as ft
from datetime import datetime
from pathlib import Path

from gui2.toolkit import ToolKit
from exporter.mcp.analyzer import analyze_sentence
from db.models import DpdHeadword

class AnalysisRow(ft.Container):
    def __init__(self, word: str, details_list: list[dict], is_component: bool = False):
        super().__init__()
        self.word = word
        self.details_list = details_list
        self.is_component = is_component
        self.padding = ft.padding.only(left=20 if is_component else 0)
        
        # Controls
        self.id_dropdown = ft.Dropdown(
            width=150,
            options=[],
            on_change=self.on_id_change,
            dense=True,
            text_size=12,
        )
        
        self.word_field = ft.TextField(value=word, width=150, dense=True, text_size=12)
        self.grammar_field = ft.TextField(width=150, dense=True, text_size=12)
        self.meaning_field = ft.TextField(width=200, dense=True, text_size=12)
        self.construction_field = ft.TextField(width=150, dense=True, text_size=12)
        self.root_field = ft.TextField(width=150, dense=True, text_size=12)
        
        # Populate Dropdown
        self.populate_dropdown()
        
        self.content = ft.Row(
            controls=[
                self.id_dropdown,
                self.word_field,
                self.grammar_field,
                self.meaning_field,
                self.construction_field,
                self.root_field,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        
        # Initial selection if data exists
        if self.details_list:
            # Default to the first option
            self.id_dropdown.value = str(self.details_list[0]["id"])
            self.update_fields(self.details_list[0])
        else:
            self.id_dropdown.value = "Manual"
            self.grammar_field.value = ""
            self.meaning_field.value = ""
            self.construction_field.value = ""
            self.root_field.value = ""

    def populate_dropdown(self):
        options = []
        for detail in self.details_list:
            options.append(ft.dropdown.Option(
                key=str(detail["id"]),
                text=f"{detail['id']} - {detail['lemma_1']}"
            ))
        options.append(ft.dropdown.Option(key="Manual", text="Manual"))
        self.id_dropdown.options = options

    def on_id_change(self, e: ft.ControlEvent) -> None:
        selected_id = self.id_dropdown.value
        if selected_id == "Manual":
            # Clear fields or keep as is? Let's keep as is to allow editing from a base, 
            # or maybe clear? The prompt says "Manual which leave all row empty".
            self.grammar_field.value = ""
            self.meaning_field.value = ""
            self.construction_field.value = ""
            self.root_field.value = ""
            self.update()
        else:
            # Find detail
            for detail in self.details_list:
                if str(detail["id"]) == selected_id:
                    self.update_fields(detail)
                    break
            self.update()

    def update_fields(self, detail: dict) -> None:
        self.grammar_field.value = detail.get("grammar", "")
        self.meaning_field.value = detail.get("meaning_combo", "")
        self.construction_field.value = detail.get("construction", "")
        
        # Root field
        root_info = ""
        if detail.get("root_key"):
            root_info = f"{detail['root_key']}"
            if detail.get("family_root"):
                 root_info += f" ({detail['family_root']})" # Simplified root info
        self.root_field.value = root_info
        
        # Update word field if it's the main word and we want to match lemma? 
        # No, Word field matches sentence word. But for components, it might be the lemma.
        # "Word in Sentence" -> user can edit.

    def get_data(self) -> dict[str, str]:
        return {
            "ID": self.id_dropdown.value,
            "Word": self.word_field.value,
            "Grammar": self.grammar_field.value,
            "Meaning": self.meaning_field.value,
            "Construction": self.construction_field.value,
            "Root": self.root_field.value
        }

class AnalysisView(ft.Column):
    def __init__(self, page: ft.Page, toolkit: ToolKit):
        super().__init__()
        self.page = page
        self.toolkit = toolkit
        self.expand = True
        
        # Input Area
        self.input_field = ft.TextField(
            label="Enter Pāḷi text",
            multiline=True,
            min_lines=3,
            max_lines=5,
            expand=False
        )
        
        self.run_button = ft.ElevatedButton(
            text="Run Analysis",
            on_click=self.run_analysis
        )
        
        self.input_container = ft.Column(
            controls=[
                self.input_field,
                self.run_button
            ]
        )
        
        # Results Area
        self.results_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        
        # Header
        self.header = ft.Row(
            controls=[
                ft.Text("ID", width=150, weight=ft.FontWeight.BOLD),
                ft.Text("Word", width=150, weight=ft.FontWeight.BOLD),
                ft.Text("Grammar", width=150, weight=ft.FontWeight.BOLD),
                ft.Text("Meaning", width=200, weight=ft.FontWeight.BOLD),
                ft.Text("Construction", width=150, weight=ft.FontWeight.BOLD),
                ft.Text("Root", width=150, weight=ft.FontWeight.BOLD),
            ]
        )
        
        # Export Buttons
        self.export_csv_btn = ft.ElevatedButton("Export CSV for Anki", on_click=self.export_csv)
        self.save_md_btn = ft.ElevatedButton("Save MD", on_click=self.save_md)
        self.export_row = ft.Row(controls=[self.export_csv_btn, self.save_md_btn], visible=False)

        self.controls = [
            self.input_container,
            ft.Divider(),
            self.header,
            self.results_container,
            self.export_row
        ]

    def run_analysis(self, e: ft.ControlEvent) -> None:
        text = self.input_field.value
        if not text:
            return
        
        self.results_container.controls.clear()
        self.page.update()
        
                # Run analysis
                try:
                    results = analyze_sentence(text, self.toolkit.db_manager.db_session)
                    
                    for result in results:
                        # result is { "word": ..., "status": ..., "data": [...] }
                        word = result["word"]
                        data_list = result["data"]
                        
                        if not data_list:
                            # Not found case
                            row = AnalysisRow(word, [], is_component=False)
                            self.results_container.controls.append(row)
                            continue
        
                        # Iterate through potential analyses (headwords or deconstructions)
                        # Typically we might want to group them or select one. 
                        # For the GUI, if there are multiple headwords for the same token (e.g. homonyms),
                        # the "ID Dropdown" in AnalysisRow handles selection.
                        # So we should pass the whole list to one AnalysisRow?
                        # BUT, different headwords might have different components.
                        # The current AnalysisRow design selects ID and updates fields.
                        # It doesn't dynamically update *rows below it* (components).
                        # This is a complexity.
                        # Simplified approach for this iteration:
                        # Create a row for the *first* analysis found, and populate its components.
                        # (Future improvement: changing ID refetches components and rebuilds rows)
                        
                        # Actually, the AnalysisRow receives `details_list` which corresponds to `data_list`.
                        # It lets the user pick an ID.
                        # We need to render the components for the *currently selected* ID.
                        # But AnalysisRow controls are static.
                        # Let's stick to the prompt's implied logic: show the analysis for the token.
                        # If there are multiple, the dropdown lets you switch data *in that row*.
                        # But components are separate rows.
                        
                        # To fully support dynamic components based on dropdown selection, we'd need a parent control.
                        # For now, let's render the components of the *first* entry in data_list (most likely match).
                        
                        first_entry = data_list[0]
                        
                        # Main Word Row
                        main_row = AnalysisRow(word, data_list, is_component=False)
                        self.results_container.controls.append(main_row)
                        
                        # Component Rows (for the first entry)
                        components = first_entry.get("components", [])
                        for component in components:
                            # Component is a dict with details. Wrap it in a list to satisfy AnalysisRow signature?
                            # Or AnalysisRow should handle a single detail?
                            # AnalysisRow expects a list of dicts for the dropdown.
                            # A component usually has one specific identity in this context.
                            # But `get_components_from_construction` returns a list of *best matches*.
                            # Let's wrap it in a list.
                            
                            comp_lemma = component.get("lemma_1", "")
                            if not comp_lemma:
                                comp_lemma = component.get("word", "???") # Fallback
                                
                            comp_row = AnalysisRow(f"- {comp_lemma}", [component], is_component=True)
                            
                            # Formatting
                            if comp_row.grammar_field.value:
                                 if "in comp" not in comp_row.grammar_field.value and "in sandhi" not in comp_row.grammar_field.value:
                                     comp_row.grammar_field.value = f"in comp, {comp_row.grammar_field.value}"
                            else:
                                 comp_row.grammar_field.value = "in comp"
        
                            self.results_container.controls.append(comp_row)
                    
                    self.export_row.visible = True
                    self.page.update()            
        except Exception as ex:
            self.results_container.controls.append(ft.Text(f"Error: {ex}", color="red"))
            self.page.update()

    def get_all_data(self) -> list[dict[str, str]]:
        data = []
        for control in self.results_container.controls:
            if isinstance(control, AnalysisRow):
                data.append(control.get_data())
        return data

    def export_csv(self, e: ft.ControlEvent) -> None:
        data = self.get_all_data()
        if not data:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"analysis_export_{timestamp}.csv"
        # Determine path (Desktop or Downloads? For now project root or temp)
        filepath = Path(self.toolkit.project_paths.temp_dir) / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["ID", "Word", "Grammar", "Meaning", "Construction", "Root"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Saved to {filepath}"))
        self.page.snack_bar.open = True
        self.page.update()

    def save_md(self, e: ft.ControlEvent) -> None:
        data = self.get_all_data()
        if not data:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"analysis_export_{timestamp}.md"
        filepath = Path(self.toolkit.project_paths.temp_dir) / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("| ID | Word | Grammar | Meaning | Construction | Root |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            for row in data:
                # Handle possible None values
                row_vals = {k: (v if v else "") for k, v in row.items()}
                line = f"| {row_vals['ID']} | {row_vals['Word']} | {row_vals['Grammar']} | {row_vals['Meaning']} | {row_vals['Construction']} | {row_vals['Root']} |\n"
                f.write(line)

        self.page.snack_bar = ft.SnackBar(ft.Text(f"Saved to {filepath}"))
        self.page.snack_bar.open = True
        self.page.update()

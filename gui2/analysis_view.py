import csv
import flet as ft
from datetime import datetime
from pathlib import Path
from typing import Any

from gui2.toolkit import ToolKit
from exporter.mcp.analyzer import analyze_sentence
from exporter.mcp.ai_pali_translate import translate_sentence
from db.models import DpdHeadword, SuttaInfo

class AnalysisRow(ft.Container):
    def __init__(self, word: str, details_list: list[dict[str, Any]], is_component: bool = False, parent_view: "AnalysisView" = None):
        super().__init__()
        self.word = word
        self.details_list = details_list
        self.is_component = is_component
        self.parent_view = parent_view
        self.padding = ft.padding.only(left=30 if is_component else 0)
        self.bgcolor = ft.Colors.TRANSPARENT
        
        # Controls
        self.id_dropdown = ft.Dropdown(
            width=200,
            options=[],
            on_change=self.on_id_change,
            dense=True,
            text_size=12,
        )
        
        self.word_field = ft.TextField(value=word, width=150, dense=True, text_size=12)
        self.grammar_field = ft.TextField(width=200, dense=True, text_size=12)
        self.meaning_field = ft.TextField(width=250, dense=True, text_size=12)
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
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        
        # Initial selection
        self.auto_select()

    def populate_dropdown(self):
        options = []
        for detail in self.details_list:
            comp = detail.get("degree_of_completion", "")
            symbol = {"complete": "✔", "semi-complete": "◑", "incomplete": "✘"}.get(comp, "")
            
            lemma = detail.get('lemma', detail.get('pali', ''))
            grammar = detail.get('grammar', '')
            # Extract short grammar: "masc nom sg of buddha" -> "masc nom sg"
            short_grammar = grammar.split(" of ")[0] if " of " in grammar else grammar
            
            label = f"{symbol} {detail['id']} - {lemma}"
            if short_grammar:
                label += f" ({short_grammar})"
                
            options.append(ft.dropdown.Option(
                key=detail["key"],
                text=label
            ))
        options.append(ft.dropdown.Option(key="Manual", text="Manual"))
        self.id_dropdown.options = options

    def auto_select(self):
        if not self.details_list:
            self.id_dropdown.value = "Manual"
            return

        # Prefer entry with "selected": True (from AI)
        selected_entry = next((d for d in self.details_list if d.get("selected")), None)
        if selected_entry:
            self.id_dropdown.value = selected_entry["key"]
            self.update_fields(selected_entry)
            self.bgcolor = ft.Colors.BLUE_GREY_900 # Highlight AI selection
        else:
            # Default to first (best score)
            self.id_dropdown.value = self.details_list[0]["key"]
            self.update_fields(self.details_list[0])
            self.bgcolor = ft.Colors.TRANSPARENT

    def on_id_change(self, e: ft.ControlEvent) -> None:
        selected_key = self.id_dropdown.value
        if selected_key == "Manual":
            self.grammar_field.value = ""
            self.meaning_field.value = ""
            self.construction_field.value = ""
            self.root_field.value = ""
            self.bgcolor = ft.Colors.TRANSPARENT
        else:
            for detail in self.details_list:
                if detail["key"] == selected_key:
                    self.update_fields(detail)
                    # If user manually changes, remove highlight
                    self.bgcolor = ft.Colors.TRANSPARENT
                    
                    # Update the master results data so re-render keeps the choice
                    if self.parent_view and hasattr(self.parent_view, "analysis_results"):
                         self._update_parent_selection(selected_key)
                    break
        
        if self.parent_view:
            self.parent_view.render_results()
        else:
            self.update()

    def _update_parent_selection(self, selected_key: str):
        """Update the selected state in the parent's analysis_results data."""
        # This is a bit complex because of nesting. 
        # A simpler way: just let render_results read the CURRENT values of all dropdowns.
        # But render_results clears controls and rebuilds.
        # So we MUST store the selection in the data.
        
        def update_recursive(data_list):
            for word_obj in data_list:
                found = False
                for entry in word_obj["data"]:
                    if entry["key"] == selected_key:
                        entry["selected"] = True
                        found = True
                    else:
                        entry["selected"] = False
                
                if not found:
                    for entry in word_obj["data"]:
                        if "components" in entry:
                            for comp_list in entry["components"]:
                                update_recursive(comp_list)

        # For simplicity, we can just scan the whole tree and update the key.
        # Since keys are unique, this works.
        def mark_selected(data_list_or_obj):
            if isinstance(data_list_or_obj, list):
                for item in data_list_or_obj:
                    mark_selected(item)
            elif isinstance(data_list_or_obj, dict):
                if "key" in data_list_or_obj:
                    if data_list_or_obj["key"] == selected_key:
                        data_list_or_obj["selected"] = True
                    # If same word but different key, unselect? 
                    # Actually better: if it's the SAME headword ID, but different grammar?
                    # The analyzer logic groups by token.
                    pass 
                
                for k, v in data_list_or_obj.items():
                    if k in ["data", "components"]:
                        mark_selected(v)

        # Clear previous selection for this "level" or just globally? 
        # Since keys are unique, we can just clear all selected and set the new one.
        def clear_selected(data_list_or_obj):
            if isinstance(data_list_or_obj, list):
                for item in data_list_or_obj:
                    clear_selected(item)
            elif isinstance(data_list_or_obj, dict):
                if "selected" in data_list_or_obj:
                    data_list_or_obj["selected"] = False
                for k, v in data_list_or_obj.items():
                    if k in ["data", "components"]:
                        clear_selected(v)

        # Actually, we only want to clear selection for the alternatives of THIS word.
        # But finding "this word" in the tree is hard without more context.
        # Global clear is fine if we assume only one thing is selected per token.
        # Wait, if AI selected things for ALL tokens, global clear is bad.
        
        # Correct logic: find the list containing the selected_key, and only update that list.
        def find_and_update(data_list_or_obj):
            if isinstance(data_list_or_obj, list):
                # Is the key in this list?
                if any(isinstance(i, dict) and i.get("key") == selected_key for i in data_list_or_obj):
                    for i in data_list_or_obj:
                        if isinstance(i, dict):
                            i["selected"] = (i.get("key") == selected_key)
                    return True
                for i in data_list_or_obj:
                    if find_and_update(i): return True
            elif isinstance(data_list_or_obj, dict):
                for k, v in data_list_or_obj.items():
                    if k in ["data", "components"]:
                        if find_and_update(v): return True
            return False

        find_and_update(self.parent_view.analysis_results)

    def update_fields(self, detail: dict) -> None:
        self.grammar_field.value = detail.get("grammar", "")
        self.meaning_field.value = detail.get("meaning_combo", "")
        self.construction_field.value = detail.get("construction", "")
        self.root_field.value = detail.get("root_key", "")
        
        # Word field: for components, might want to show lemma if word is hyphenated
        if self.is_component and detail.get("lemma"):
             self.word_field.value = f"- {detail['lemma']}"

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
        
        # Sutta Selection
        self.sutta_field = ft.TextField(
            label="Sutta Name",
            width=300,
            on_submit=self.load_sutta,
            hint_text="e.g. dhammacakkappavattana",
            dense=True
        )
        self.load_sutta_btn = ft.ElevatedButton("Load Sutta", on_click=self.load_sutta)
        
        # Input Area
        self.input_field = ft.TextField(
            label="Pāḷi text to analyze",
            multiline=True,
            min_lines=3,
            max_lines=10,
            expand=False,
            dense=True
        )
        
        self.run_button = ft.ElevatedButton(
            text="Analyze (Offline)",
            on_click=self.run_analysis,
            icon=ft.Icons.ANALYTICS
        )
        
        self.ai_button = ft.ElevatedButton(
            text="AI Assist (Online)",
            on_click=self.run_ai_analysis,
            icon=ft.Icons.AUTO_AWESOME,
            bgcolor=ft.Colors.BLUE_900
        )

        self.retranslate_button = ft.ElevatedButton(
            text="Re-Translate",
            on_click=self.retranslate,
            icon=ft.Icons.REFRESH,
            visible=False
        )

        self.translation_label = ft.Text("", weight=ft.FontWeight.BOLD, italic=True, selectable=True)
        self.literal_label = ft.Text("", italic=True, size=12, selectable=True)
        
        self.input_container = ft.Column(
            controls=[
                ft.Row([self.sutta_field, self.load_sutta_btn]),
                self.input_field,
                ft.Row([self.run_button, self.ai_button, self.retranslate_button]),
                self.translation_label,
                self.literal_label
            ]
        )
        
        # Data
        self.analysis_results = []
        
        # Results Area
        self.results_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=2)
        
        # Header
        self.header = ft.Row(
            controls=[
                ft.Text("Selection (ID - Lemma)", width=200, weight=ft.FontWeight.BOLD),
                ft.Text("Word", width=150, weight=ft.FontWeight.BOLD),
                ft.Text("Grammar", width=200, weight=ft.FontWeight.BOLD),
                ft.Text("Meaning", width=250, weight=ft.FontWeight.BOLD),
                ft.Text("Construction", width=150, weight=ft.FontWeight.BOLD),
                ft.Text("Root", width=150, weight=ft.FontWeight.BOLD),
            ]
        )
        
        # Export Buttons
        self.export_csv_btn = ft.ElevatedButton("Export CSV", on_click=self.export_csv)
        self.save_md_btn = ft.ElevatedButton("Save MD", on_click=self.save_md)
        self.export_row = ft.Row(controls=[self.export_csv_btn, self.save_md_btn], visible=False)

        self.controls = [
            self.input_container,
            ft.Divider(),
            self.header,
            self.results_container,
            self.export_row
        ]

    def load_sutta(self, e: ft.ControlEvent) -> None:
        name = self.sutta_field.value
        if not name: return
        
        from tools.tipitaka_db import search_all_cst_texts
        # Search for sutta name as a regex at start of line or similar
        results = search_all_cst_texts(f"^{name}", search_column="pali_text")
        
        if results:
            # Take first result
            pali_text, eng_trans, table, book = results[0]
            self.input_field.value = pali_text
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Loaded from {book} ({table})"))
            self.page.snack_bar.open = True
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Sutta title not found in Tipitaka text."))
            self.page.snack_bar.open = True
        self.page.update()

    def run_analysis(self, e: ft.ControlEvent) -> None:
        self._execute_analysis(ai=False)

    def run_ai_analysis(self, e: ft.ControlEvent) -> None:
        self._execute_analysis(ai=True)

    def _execute_analysis(self, ai: bool = False) -> None:
        text = self.input_field.value
        if not text: return
        
        self.results_container.controls.clear()
        self.translation_label.value = "Analyzing..." if not ai else "AI is thinking (requesting OpenRouter)..."
        self.literal_label.value = ""
        self.export_row.visible = False
        self.page.update()
        
        try:
            db = self.toolkit.db_manager.db_session
            if ai:
                result_obj = translate_sentence(text, db)
                self.translation_label.value = f"Translation: {result_obj.get('translation', '')}"
                self.literal_label.value = f"Literal: {result_obj.get('literal_translation', '')}"
                self.analysis_results = result_obj["analysis"]
            else:
                self.analysis_results = analyze_sentence(text, db)
                self.translation_label.value = ""
            
            self.render_results()
            self.export_row.visible = True
            self.retranslate_button.visible = True
            
        except Exception as ex:
            self.results_container.controls.append(ft.Text(f"Error: {ex}", color="red"))
            import traceback
            traceback.print_exc()
        
        self.page.update()

    def render_results(self) -> None:
        self.results_container.controls.clear()
        for result in self.analysis_results:
            word = result["word"]
            data_list = result["data"]
            
            if not data_list:
                self.results_container.controls.append(AnalysisRow(word, [], parent_view=self))
                continue

            # Create row
            row = AnalysisRow(word, data_list, parent_view=self)
            self.results_container.controls.append(row)
            
            # Find selected entry to render components
            selected_key = row.id_dropdown.value
            selected_entry = next((d for d in data_list if d["key"] == selected_key), data_list[0])
            self._render_components(selected_entry)
        self.page.update()

    def _render_components(self, entry: dict) -> None:
        """Recursive component rendering."""
        if "components" not in entry or not entry["components"]: return
        
        for comp_options in entry["components"]:
            if not comp_options: continue
            
            # Use first option of component for display
            comp_word = comp_options[0].get("pali", "???")
            comp_row = AnalysisRow(f"- {comp_word}", comp_options, is_component=True, parent_view=self)
            self.results_container.controls.append(comp_row)
            
            # Recurse if the selected component itself has components
            selected_comp_key = comp_row.id_dropdown.value
            selected_comp_entry = next((d for d in comp_options if d["key"] == selected_comp_key), comp_options[0])
            self._render_components(selected_comp_entry)

    def retranslate(self, e: ft.ControlEvent) -> None:
        """Triggers a fresh AI translation based on the user's manual word choices."""
        text = self.input_field.value
        if not text or not self.analysis_results: return
        
        self.translation_label.value = "Re-translating based on your choices..."
        self.page.update()
        
        try:
            from tools.ai_open_router import OpenRouterManager
            from exporter.mcp.ai_pali_translate import build_system_prompt
            
            # Construct a context that only contains the SELECTED options
            # to force the AI to follow user choices.
            selected_context = []
            
            def filter_selected(data_list):
                filtered = []
                for word_obj in data_list:
                    new_word_obj = {"word": word_obj["word"], "data": []}
                    for entry in word_obj["data"]:
                        if entry.get("selected"):
                            # Keep only selected entry
                            new_entry = entry.copy()
                            # Recursively filter components
                            if "components" in new_entry:
                                new_entry["components"] = [filter_selected(cl) for cl in new_entry["components"]]
                            new_word_obj["data"].append(new_entry)
                    filtered.append(new_word_obj)
                return filtered

            context = filter_selected(self.analysis_results)
            sys_prompt = build_system_prompt(context)
            sys_prompt += "\n\nCRITICAL: You MUST use the meanings and grammatical forms provided in the context for your translation, as these have been explicitly chosen by the user."
            
            ai_manager = OpenRouterManager()
            model = "xiaomi/mimo-v2-flash:free"
            
            response = ai_manager.request(
                prompt=f"Please provide a refined translation for: {text}",
                model=model,
                prompt_sys=sys_prompt,
            )
            
            if response.content:
                import json
                # Clean up possible markdown code blocks
                json_str = response.content.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:-3].strip()
                elif json_str.startswith("```"):
                    json_str = json_str[3:-3].strip()
                
                ai_data = json.loads(json_str)
                self.translation_label.value = f"Refined Translation: {ai_data.get('translation', '')}"
                self.literal_label.value = f"Refined Literal: {ai_data.get('literal_translation', '')}"
            else:
                self.translation_label.value = f"AI Error: {response.status_message}"
                
        except Exception as ex:
            self.translation_label.value = f"Error: {ex}"
        
        self.page.update()

    def get_all_data(self) -> list[dict[str, str]]:
        data = []
        for control in self.results_container.controls:
            if isinstance(control, AnalysisRow):
                data.append(control.get_data())
        return data

    def export_csv(self, e: ft.ControlEvent) -> None:
        data = self.get_all_data()
        if not data: return

        filepath = Path(self.toolkit.project_paths.temp_dir) / f"analysis_{datetime.now().strftime('%H%M%S')}.csv"
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["ID", "Word", "Grammar", "Meaning", "Construction", "Root"])
            writer.writeheader()
            writer.writerows(data)
        
        self.toolkit.show_snackbar(f"Exported to {filepath}")

    def save_md(self, e: ft.ControlEvent) -> None:
        data = self.get_all_data()
        if not data: return

        filepath = Path(self.toolkit.project_paths.temp_dir) / f"analysis_{datetime.now().strftime('%H%M%S')}.md"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("| ID | Word | Grammar | Meaning | Construction | Root |\n| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            for r in data:
                f.write(f"| {r['ID']} | {r['Word']} | {r['Grammar']} | {r['Meaning']} | {r['Construction']} | {r['Root']} |\n")

        self.toolkit.show_snackbar(f"Saved to {filepath}")

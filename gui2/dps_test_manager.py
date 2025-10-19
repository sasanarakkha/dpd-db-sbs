# -*- coding: utf-8 -*-
import csv
import re
import subprocess
from json import dumps
from typing import NamedTuple

import flet as ft

from db_tests.db_tests_manager import InternalTestRow
from gui2.dps_view import DpsView
from gui2.mixins import PopUpMixin
from tools.paths_dps import DPSPaths


class IntegrityFailure(NamedTuple):
    """Represents a single failure when integrity checking tests TSV."""

    test_row: int
    test_name: str
    invalid_field_name: str
    invalid_value: str


class TestFailure(NamedTuple):
    """A single test failure"""

    test_row: int
    test_name: str
    error_column: str


class DpsTestManager(PopUpMixin):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.dpspth = DPSPaths()
        self.tests_path = self.dpspth.internal_tests_path
        self.fieldnames: list[str] = []
        self.current_tests: list[InternalTestRow] = []
        self.integrity_ok, self.integrity_failures = self.integrity_check()
        
        # UI state
        self.ui: DpsView | None = None
        self.page: ft.Page | None = None
        self.passed: bool = False
        self.failure_list: list[TestFailure] | list[IntegrityFailure] = []
        self.current_headword_id: int | None = None
        self.current_failure_index: int = 0

    def load_tests(self) -> list[InternalTestRow]:
        """Load tests from DPS-specific test file"""
        try:
            with open(self.tests_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, delimiter="\t")
                if reader.fieldnames:
                    self.fieldnames = list(reader.fieldnames)
                self.current_tests = []
                for row in reader:
                    # Reorder the row to match InternalTestRow constructor parameters
                    reordered_row = {
                        "test_name": row["test_name"],
                        "search_column_1": row["search_column_1"],
                        "search_sign_1": row["search_sign_1"],
                        "search_string_1": row["search_string_1"],
                        "search_column_2": row["search_column_2"],
                        "search_sign_2": row["search_sign_2"],
                        "search_string_2": row["search_string_2"],
                        "search_column_3": row["search_column_3"],
                        "search_sign_3": row["search_sign_3"],
                        "search_string_3": row["search_string_3"],
                        "search_column_4": row["search_column_4"],
                        "search_sign_4": row["search_sign_4"],
                        "search_string_4": row["search_string_4"],
                        "search_column_5": row["search_column_5"],
                        "search_sign_5": row["search_sign_5"],
                        "search_string_5": row["search_string_5"],
                        "search_column_6": row["search_column_6"],
                        "search_sign_6": row["search_sign_6"],
                        "search_string_6": row["search_string_6"],
                        "error_column": row["error_column"],
                        "exceptions": row["exceptions"],
                        "iterations": row["iterations"],
                        "display_1": row["display_1"],
                        "display_2": row["display_2"],
                        "display_3": row["display_3"],
                        "notes": row.get("notes", "")  # Optional field
                    }
                    self.current_tests.append(InternalTestRow(**reordered_row))
            return self.current_tests
        except FileNotFoundError:
            self.current_tests = []
            return []
        except Exception:
            self.current_tests = []
            return []

    def integrity_check(self) -> tuple[bool, list[IntegrityFailure]]:
        """
        Checks the validity of search columns and signs in the internal tests list.

        Returns `True` and an empty list if all tests are valid.

        Returns `False` and a list of TestTsvFailure named tuples for any invalid tests found.
        """
        # Get DPS field names from the field mapping
        from gui2.dps_field_mapping import dps_field_mapping
        dps_field_names = list(dps_field_mapping.keys())
        dps_field_names.append("")  # Add "" to allow empty values

        logical_operators: list[str] = [
            "",
            "equals",
            "does not equal",
            "contains",
            "contains word",
            "does not contain",
            "does not contain word",
            "is empty",
            "is not empty",
        ]

        failures: list[IntegrityFailure] = []

        for test_counter, t in enumerate(
            self.current_tests,
            start=2,  # 1 for zero offset, 1 for title
        ):
            for i in range(1, 7):  # Check criteria sets 1 through 6
                # Check search_column_i
                col_attr_name = f"search_column_{i}"
                col_value = getattr(t, col_attr_name, None)
                if col_value not in dps_field_names:
                    failure = IntegrityFailure(
                        test_row=test_counter,
                        test_name=t.test_name,
                        invalid_field_name=col_attr_name,
                        invalid_value=str(col_value),
                    )
                    failures.append(failure)

                # Check search_sign_i
                sign_attr_name = f"search_sign_{i}"
                sign_value = getattr(t, sign_attr_name, None)
                if sign_value not in logical_operators:
                    failure = IntegrityFailure(
                        test_row=test_counter,
                        test_name=t.test_name,
                        invalid_field_name=sign_attr_name,
                        invalid_value=str(sign_value),
                    )
                    failures.append(failure)
                    
        if failures:
            return False, failures
        else:
            return True, failures

    @staticmethod
    def get_search_criteria(t: InternalTestRow) -> list[tuple]:
        return [
            (t.search_column_1, t.search_sign_1, t.search_string_1),
            (t.search_column_2, t.search_sign_2, t.search_string_2),
            (t.search_column_3, t.search_sign_3, t.search_string_3),
            (t.search_column_4, t.search_sign_4, t.search_string_4),
            (t.search_column_5, t.search_sign_5, t.search_string_5),
            (t.search_column_6, t.search_sign_6, t.search_string_6),
        ]

    def error_test_each_single_row(
        self,
        test: InternalTestRow,
        values: dict[str, str],
    ) -> bool:
        """Checks for errors on a single row.

        Returns `True` if there's an error.

        Returns `False` if there's no error.
        """

        search_criteria = self.get_search_criteria(test)
        test_results = {}

        # Get headword ID for exception checking
        headword_id_str = values.get("dps_dpd_id", "")
        try:
            headword_id = int(headword_id_str) if headword_id_str else 0
        except ValueError:
            headword_id = 0

        if headword_id in test.exceptions:
            return False

        for count, criterion in enumerate(search_criteria, start=1):
            test_column, test_logic, test_string = criterion

            if not test_logic:
                test_results[f"test{count}"] = True

            elif test_logic == "equals":
                test_results[f"test{count}"] = (
                    values.get(test_column, "") == test_string
                )
            elif test_logic == "does not equal":
                test_results[f"test{count}"] = (
                    values.get(test_column, "") != test_string
                )
            elif test_logic == "contains":
                test_results[f"test{count}"] = (
                    re.findall(test_string, values.get(test_column, "")) != []
                )
            elif test_logic == "does not contain":
                test_results[f"test{count}"] = (
                    re.findall(test_string, values.get(test_column, "")) == []
                )
            elif test_logic == "contains word":
                test_results[f"test{count}"] = (
                    re.findall(rf"\b{test_string}\b", values.get(test_column, ""))
                    != []
                )
            elif test_logic == "does not contain word":
                test_results[f"test{count}"] = (
                    re.findall(rf"\b{test_string}\b", values.get(test_column, ""))
                    == []
                )
            elif test_logic == "is empty":
                test_results[f"test{count}"] = values.get(test_column, "") == ""
            elif test_logic == "is not empty":
                test_results[f"test{count}"] = values.get(test_column, "") != ""
            else:
                print(f"[red]search_{count} error")

        return all(test_results.values())

    def run_all_tests_on_values(
        self, values: dict[str, str]
    ) -> tuple[bool, list[TestFailure] | list[IntegrityFailure]]:
        """
        Run all the tests on field values.

        Returns `True` and empty list if is all ok.

        Returns `False` and a list of failures if not.

        """
        # Load and check integrity
        self.current_tests = self.load_tests()
        integrity_ok, integrity_failures = self.integrity_check()
        if not integrity_ok:
            return False, integrity_failures

        error_list: list[TestFailure] = []
        for counter, test in enumerate(
            self.current_tests,
            start=2,  # 1 for zero offset and 1 for title
        ):
            error = self.error_test_each_single_row(test, values)
            if error:
                error_list.append(
                    TestFailure(
                        test_row=counter,
                        test_name=test.test_name,
                        error_column=test.error_column,
                    )
                )

        return not bool(error_list), error_list  # Simplified return

    def run_all_tests(self, ui: DpsView, values: dict[str, str]) -> None:
        """Run all tests and handle UI interaction - same as GuiTestManager"""
        self.current_tests = self.load_tests()
        
        # Clear previous error highlights before running tests
        for field in ui.dps_fields.fields.values():
            if isinstance(field, ft.TextField) and hasattr(field, "error_text"):
                field.error_text = None
        
        # Get headword ID for exception management
        headword_id_str = values.get("dps_dpd_id", "")
        try:
            self.current_headword_id = int(headword_id_str) if headword_id_str else None
        except ValueError:
            self.current_headword_id = None
            
        passed, failure_list = self.run_all_tests_on_values(values)
        self.passed = passed
        self.failure_list = failure_list
        self.ui = ui
        self.page = ui.page

        if passed:
            ui.tests_passed = True
            ui.update_message("All tests passed!")
        else:
            ui.tests_passed = False
            ui.update_message(f"{len(failure_list)} tests failed")

            # Highlight error columns
            for f in failure_list:
                if isinstance(f, TestFailure):
                    field = ui.dps_fields.fields.get(f.error_column)
                    if isinstance(field, ft.TextField) and hasattr(field, "error_text"):
                        field.error_text = f.test_name
                elif isinstance(f, IntegrityFailure):
                    ui.update_message(
                        f"error in TSV: {f.test_row} {f.test_name} {f.invalid_field_name} {f.invalid_value}"
                    )
                    return

            self.show_failures()

    def show_failures(self) -> None:
        """Display test failures one at a time with action buttons"""

        if not self.failure_list:
            return

        self.current_failure_index = 0
        self._create_failure_dialog()
        if self.page:
            self.show_popup(self.page)
        self._show_current_failure()

    def _create_failure_dialog(self) -> None:
        """Create dialog with action buttons"""
        self.failure_content = ft.Column(
            height=120,
            expand=False,
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._dialog = ft.AlertDialog(
            modal=True,
            content=self.failure_content,
            actions=[
                ft.TextButton("Edit", on_click=self._handle_edit),
                ft.TextButton("Add to Exceptions", on_click=self._handle_add_exception),
                ft.TextButton("Next", on_click=self._handle_next_failure),
                ft.TextButton("Close", on_click=self._handle_popup_close),
                ft.TextButton("Open Tests TSV", on_click=self._handle_open_test_file),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            actions_padding=20,
            content_padding=20,
        )

    def _show_current_failure(self) -> None:
        """Update dialog content for current failure"""
        failure = self.failure_list[self.current_failure_index]

        self.failure_content.controls = [
            ft.Text(
                "Test Failed",
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                str(failure.test_row),
                color=ft.Colors.BLUE_200,
                selectable=True,
            ),
            ft.Text(
                f"{failure.test_name}",
                selectable=True,
            ),
            # Display relevant info based on failure type
            ft.Text(
                f"Column: {failure.error_column}"
                if isinstance(failure, TestFailure)
                else f"Field: {failure.invalid_field_name}",
                selectable=True,
            ),
            ft.Text(
                f"Value: {failure.invalid_value}"
                if isinstance(failure, IntegrityFailure)
                else "",
                selectable=True,
                visible=isinstance(
                    failure, IntegrityFailure
                ),  # Only show if IntegrityFailure
            ),
        ]
        self._dialog.update()

    def _handle_add_exception(self, e: ft.ControlEvent) -> None:
        """Add current failure's headword ID to exceptions list"""
        if self.current_failure_index >= len(self.failure_list):
            return  # Safety check

        failure = self.failure_list[self.current_failure_index]

        # Ensure we have a headword and it's a TestFailure
        if self.current_headword_id and isinstance(failure, TestFailure):
            test_row = failure.test_row
            test_name = failure.test_name
            headword_id = self.current_headword_id

            if self.ui:
                self.ui.update_message(f"adding exception for {test_row}: {test_name}")

            success = self.add_exception(test_name, headword_id)

            if self.ui:
                if success:
                    self.ui.update_message(f"added exception for {test_name}")
                else:
                    self.ui.update_message(f"Failed to add exception for {test_name}")

            # Move to the next failure regardless of success/failure
            self._handle_next_failure(e)

        elif not isinstance(failure, TestFailure):
            if self.ui:
                self.ui.update_message(
                    f"Cannot add exception for IntegrityFailure: {failure.test_name}"
                )
            self._handle_next_failure(e)
        else:
            # If current_headword is not set, still try to move to the next failure
            # or close if it's the last one, mimicking the "Next" button behavior.
            if self.ui:
                self.ui.update_message(
                    "Error: current_headword not set. Attempting to proceed."
                )
            self._handle_next_failure(e)  # Always behave like 'Next'

    def _handle_open_test_file(self, e: ft.ControlEvent) -> None:
        """Opens the DPS test file in LibreOffice Calc."""
        if self.ui:
            if self.tests_path.exists():
                self.ui.update_message(f"Opening test file: {self.tests_path}")
                try:
                    subprocess.Popen(["libreoffice", "--calc", str(self.tests_path)])
                    self._handle_popup_close(e)  # Close popup after attempting to open
                except FileNotFoundError:
                    self.ui.update_message("Error: 'libreoffice' command not found.")
                except Exception as sub_err:
                    self.ui.update_message(
                        f"Error opening file with LibreOffice: {sub_err}"
                    )
            else:
                self.ui.update_message(
                    f"Error: Test file not found at expected path: {self.tests_path}"
                )

    def _handle_edit(self, e: ft.ControlEvent) -> None:
        """Close dialog and focus error field"""
        failure = self.failure_list[self.current_failure_index]
        self._handle_popup_close(e)
        # Focus the error field
        if self.ui:
            if isinstance(failure, TestFailure):
                field = self.ui.dps_fields.fields.get(failure.error_column)
                if field and hasattr(field, "focus"):
                    field.focus()  # type: ignore
            self.ui.update_message(f"Edit field: {failure.test_name}")

    def _handle_next_failure(self, e: ft.ControlEvent) -> None:
        """Show next failure or close if last"""
        self.current_failure_index += 1
        if self.current_failure_index < len(self.failure_list):
            self._show_current_failure()
        else:
            self._handle_popup_close(e)

    def save_tests(self) -> None:
        """Saves the current state of current_tests back to the TSV file."""
        if not self.current_tests:
            print("No tests loaded, nothing to save.")
            return

        fieldnames = self.fieldnames

        try:
            with open(self.tests_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    delimiter="\t",
                    fieldnames=fieldnames,
                    quoting=csv.QUOTE_ALL,
                )
                writer.writeheader()
                for test_row in self.current_tests:
                    # Create a dictionary representation for writing
                    row_dict = {}
                    for field in fieldnames:
                        # Get value, default to empty string if not present
                        value = getattr(test_row, field, "")
                        # Serialize exceptions list to JSON string
                        if field == "exceptions":
                            exceptions_list = (
                                list(value) if isinstance(value, (list, set)) else []
                            )
                            row_dict[field] = dumps(exceptions_list, ensure_ascii=False)
                        else:
                            row_dict[field] = value

                    writer.writerow(row_dict)
        except IOError as e:
            print(f"Error saving tests to {self.tests_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during saving tests: {e}")

    def add_exception(self, test_name: str, exception_id: int) -> bool:
        """Adds an exception ID to a specific test and saves the changes.

        Args:
            test_name: The name of the test to modify.
            exception_id: The ID to add to the exceptions list.

        Returns:
            True if the exception was added and saved successfully, False otherwise.
        """

        test_found = False
        for test in self.current_tests:
            if test.test_name == test_name:
                test_found = True

                if exception_id not in test.exceptions:
                    test.exceptions.append(exception_id)
                    test.exceptions.sort()
                    print(f"Added exception {exception_id} to test '{test_name}'.")
                    self.save_tests()
                    return True
                else:
                    # Even if it exists, consider it a success
                    return True

        if not test_found:
            print(f"Test '{test_name}' not found.")
            return False

        # Fallback, should ideally not be reached
        return False

    def sort_tests_by_name(self) -> None:
        """Sorts the tests alphabetically by test_name, preserving the header row."""
        if not self.current_tests:
            print("No tests loaded, nothing to sort.")
            return
            
        # Sort the internal tests list by test_name
        self.current_tests.sort(key=lambda test: test.test_name)
        
        # Save the sorted tests back to the TSV file
        self.save_tests()

    # Backward compatibility methods
    def load_tests_compat(self, pth=None) -> list[InternalTestRow]:
        """Backward compatibility method - loads tests from DPS-specific test file"""
        return self.load_tests()

    def run_tests(self, values: dict[str, str]) -> tuple[bool, list[dict]]:
        """Backward compatibility method - run DPS tests using the same logic as Pass2Add"""
        passed, failure_list = self.run_all_tests_on_values(values)
        
        # Convert to old format for compatibility
        failures = []
        for failure in failure_list:
            if isinstance(failure, TestFailure):
                failures.append({
                    "test_name": failure.test_name,
                    "test_number": failure.test_row,
                    "failed_criteria": [],  # Not used in DPS UI
                    "error_column": failure.error_column
                })
        
        return passed, failures

    def show_failures_compat(self, page=None) -> None:
        """Backward compatibility method - show test failures"""
        if page:
            self.page = page
        self.show_failures()

#!/usr/bin/env python3
"""Interactively review correction comments and remember processed IDs."""

import json
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr
from gui2.paths import Gui2Paths


def _normalize_id(id_value: object) -> int | None:
    if isinstance(id_value, bool):
        return None
    if isinstance(id_value, int):
        return id_value
    if isinstance(id_value, str):
        try:
            return int(id_value)
        except ValueError:
            return None
    return None


def main() -> None:
    dps_paths = DPSPaths()
    gui2_paths = Gui2Paths()

    input_file = gui2_paths.corrections_added_path
    processed_file = dps_paths.corrections_processed_json_path

    if not input_file.exists():
        pr.red(f"Error: {input_file} not found.")
        return

    try:
        with open(input_file, encoding="utf-8") as f:
            corrections = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        pr.red(f"Error loading {input_file}: {e}")
        return

    processed_ids: set[int] = set()
    if processed_file.exists():
        try:
            with open(processed_file, encoding="utf-8") as f:
                processed_ids = {
                    normalized_id
                    for id_val in json.load(f)
                    if (normalized_id := _normalize_id(id_val)) is not None
                }
        except json.JSONDecodeError:
            pr.amber(f"Warning: {processed_file} is empty or invalid. Starting fresh.")

    all_with_comment_add = [item for item in corrections if item.get("comment_add")]
    total_with_comment_add = len(all_with_comment_add)

    to_process = [
        item
        for item in all_with_comment_add
        if _normalize_id(item.get("id")) not in processed_ids
    ]

    if not to_process:
        pr.white(
            f"No new corrections with 'comment_add' to process. (Total with comment_add: {total_with_comment_add})"
        )
        return

    pr.white(f"Total entries with 'comment_add': {total_with_comment_add}")
    pr.white(f"Remaining to process: {len(to_process)}\n")

    newly_processed: list[int] = []

    try:
        for i, item in enumerate(to_process):
            item_id = _normalize_id(item.get("id"))
            if item_id is None:
                pr.amber(f"Warning: Skipping item at index {i} because it has no ID.")
                continue

            pr.white("-" * 40)
            pr.white(
                f"Progress: {i + 1}/{len(to_process)} (Total with 'comment_add': {total_with_comment_add})"
            )

            pr.white(f"ID: {item_id}")
            pr.white(
                f"Lemma: {item.get('lemma_1')} (Proposed: {item.get('lemma_1_add')})"
            )
            pr.white(
                f"Meaning: {item.get('meaning_1')} (Proposed: {item.get('meaning_1_add')})"
            )
            pr.white(f"Comment: {item.get('comment')}")
            pr.white(f"Comment Add: {item.get('comment_add')}")

            other_diffs = []
            exclude_keys = [
                "id",
                "comment",
                "comment_add",
            ]

            for key_add, new_val in item.items():
                if key_add.endswith("_add"):
                    base_key = key_add[:-4]
                    if base_key in exclude_keys:
                        continue

                    original_val = item.get(base_key, "")

                    norm_new = new_val if new_val is not None else ""
                    norm_orig = original_val if original_val is not None else ""

                    if str(norm_new) != str(norm_orig):
                        other_diffs.append((base_key, original_val, new_val))

            if other_diffs:
                pr.cyan("--- OTHER DIFFERENCES ---")
                for base_key, original_val, new_val in other_diffs:
                    pr.white(f"{base_key:20}: {original_val}")
                    pr.white(f"{base_key + '_add':20}: {new_val}")
                    pr.white("")
            else:
                pr.white("No other data differences found.")

            pr.white("-" * 40)

            user_input = (
                input("Press Enter to mark as processed (or 'q' to quit): ")
                .strip()
                .lower()
            )

            if user_input == "q":
                break

            newly_processed.append(item_id)
            processed_ids.add(item_id)

    except KeyboardInterrupt:
        pr.amber("Interrupted by user.")

    if newly_processed:
        try:
            with open(processed_file, "w", encoding="utf-8") as f:
                json.dump(sorted(processed_ids), f, indent=4)
            pr.green(
                f"Saved {len(newly_processed)} newly processed IDs to {processed_file}."
            )
        except OSError as e:
            pr.red(f"Error saving {processed_file}: {e}")
    else:
        pr.white("No IDs were marked as processed.")


if __name__ == "__main__":
    main()

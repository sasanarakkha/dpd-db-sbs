#!/usr/bin/env python3

import json

from gui2.paths import Gui2Paths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr


def main() -> None:
    dps_paths = DPSPaths()
    gui2_paths = Gui2Paths()

    input_file = gui2_paths.additions_added_path
    processed_file = dps_paths.addition_processed_json_path

    if not input_file.exists():
        pr.red(f"Error: {input_file} not found.")
        return

    try:
        with open(input_file, encoding="utf-8") as f:
            additions = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        pr.red(f"Error loading {input_file}: {e}")
        return

    processed_ids: set[str] = set()
    if processed_file.exists():
        try:
            with open(processed_file, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    processed_ids = set(data)
        except json.JSONDecodeError:
            pr.amber(f"Warning: {processed_file} is empty or invalid. Starting fresh.")

    all_with_comment = [item for item in additions if item.get("comment")]
    total_with_comment = len(all_with_comment)

    to_process = [
        item for item in all_with_comment if item.get("id") not in processed_ids
    ]

    if not to_process:
        pr.white(
            f"No new additions with 'comment' to process. (Total with comment: {total_with_comment})"
        )
        return

    pr.white(f"Total additions with 'comment': {total_with_comment}")
    pr.white(f"Remaining to process: {len(to_process)}")

    newly_processed = []

    try:
        for i, item in enumerate(to_process):
            item_id = item.get("id")
            if item_id is None:
                pr.amber(f"Warning: Skipping item at index {i} because it has no ID.")
                continue

            pr.white("-" * 40)
            pr.cyan(
                f"Progress: {i + 1}/{len(to_process)} (Total with 'comment': {total_with_comment})"
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

                    # Normalize None and empty string
                    norm_new = "" if new_val is None else new_val
                    norm_orig = "" if original_val is None else original_val

                    if str(norm_new) != str(norm_orig):
                        other_diffs.append((base_key, original_val, new_val))

            if other_diffs:
                pr.white("\n--- OTHER DIFFERENCES ---")
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
            pr.red(f"Error saving processed IDs to {processed_file}: {e}")
    else:
        pr.white("No IDs were marked as processed.")


if __name__ == "__main__":
    main()

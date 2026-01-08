#!/usr/bin/env python3

import json
from tools.paths_dps import DPSPaths
from gui2.paths import Gui2Paths


def main():
    dps_paths = DPSPaths()
    gui2_paths = Gui2Paths()

    input_file = gui2_paths.corrections_added_path
    processed_file = dps_paths.corrections_processed_json_path

    if not input_file.exists():
        print(f"Error: {input_file} not found.")
        return

    # Load corrections
    try:
        with open(input_file, "r") as f:
            corrections = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading {input_file}: {e}")
        return

    # Load processed IDs
    processed_ids = set()
    if processed_file.exists():
        try:
            with open(processed_file, "r") as f:
                processed_ids = set(json.load(f))
        except json.JSONDecodeError:
            print(f"Warning: {processed_file} is empty or invalid. Starting fresh.")

    # Filter items
    all_with_comments = [item for item in corrections if item.get("comment_add")]
    total_with_comments = len(all_with_comments)

    to_process = [
        item for item in all_with_comments if item.get("id") not in processed_ids
    ]

    if not to_process:
        print(
            f"No new corrections with comments to process. (Total with comments: {total_with_comments})"
        )
        return

    print(f"Total entries with comments: {total_with_comments}")
    print(f"Remaining to process: {len(to_process)}\n")

    newly_processed = []

    try:
        for i, item in enumerate(to_process):
            item_id = item.get("id")
            if item_id is None:
                print(f"Warning: Skipping item at index {i} because it has no ID.")
                continue

            print("-" * 40)
            print(
                f"Progress: {i + 1}/{len(to_process)} (Total with comments: {total_with_comments})"
            )

            # Print Context
            print(f"ID: {item_id}")
            print(f"Lemma: {item.get('lemma_1')} (Proposed: {item.get('lemma_1_add')})")
            print(
                f"Meaning: {item.get('meaning_1')} (Proposed: {item.get('meaning_1_add')})"
            )
            print(f"Comment: {item.get('comment')}")
            print(f"Comment Add: {item.get('comment_add')}")

            # Iterate through other _add fields and compare with original
            other_diffs = []
            exclude_keys = [
                "id",
                "lemma_1",
                "meaning_1",
                "comment",
                "id_add",
                "lemma_1_add",
                "meaning_1_add",
                "comment_add",
            ]

            for key_add, new_val in item.items():
                if key_add.endswith("_add"):
                    base_key = key_add[:-4]
                    if base_key in exclude_keys:
                        continue

                    original_val = item.get(base_key, "")

                    # Normalize None and empty string
                    norm_new = new_val if new_val is not None else ""
                    norm_orig = original_val if original_val is not None else ""

                    # Only show if they differ
                    if str(norm_new) != str(norm_orig):
                        other_diffs.append((base_key, original_val, new_val))

            if other_diffs:
                print("\n--- OTHER DIFFERENCES ---")
                for base_key, original_val, new_val in other_diffs:
                    print(f"{base_key:20}: {original_val}")
                    print(f"{base_key + '_add':20}: {new_val}")
                    print()
            else:
                print("\nNo other data differences found.")

            print("-" * 40)

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
        print("\nInterrupted by user.")

    # Save processed IDs
    if newly_processed:
        with open(processed_file, "w") as f:
            json.dump(sorted(list(processed_ids)), f, indent=4)
        print(
            f"\nSaved {len(newly_processed)} newly processed IDs to {processed_file}."
        )
    else:
        print("\nNo IDs were marked as processed.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""Generate a stub SMD entry for every path in registry.json."""

import sys

from kamma.upstream_sync.scripts.registry_helper import (
    load_registry,
    get_modified_upstream_paths,
    get_shadow_mappings_by_category,
)


def make_stub(path: str, category: str, divergence_reason: str = "") -> str:
    sync_rule = "PORT"
    local_changes = """
- **Local Changes**:
  1. TODO: document local change 1
  2. TODO: document local change 2"""

    if category == "inspired_by_upstream":
        sync_rule = "inspired_only"
        local_changes = f"\n- **Divergence Reason**: {divergence_reason}"

    return f"""
**File**: `{path}`
- **Category**: {category}
- **Sync Rule**: {sync_rule}{local_changes}
- **Watch For**:
  - TODO: document sync pitfall
"""


def main() -> None:
    # Progress goes to stderr so stdout is clean for redirection
    _stderr = sys.stderr

    data = load_registry()
    sections: list[str] = []
    count = 0

    for path in get_modified_upstream_paths(data):
        sections.append(make_stub(path, "modified_upstream_files"))
        count += 1

    for category, mapping in get_shadow_mappings_by_category(data).items():
        for shadow in mapping:
            sections.append(make_stub(shadow, category))
            count += 1

    for path, entry in data.inspired_by_upstream.items():
        sections.append(
            make_stub(path, "inspired_by_upstream", entry.divergence_reason)
        )
        count += 1

    _stderr.write(f"gen_smd_scaffold: {count} stubs\n")
    sys.stdout.write("\n".join(sections))


if __name__ == "__main__":
    main()

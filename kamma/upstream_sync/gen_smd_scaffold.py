"""Generate a stub SMD entry for every path in registry.json."""

import sys

from kamma.upstream_sync.registry_helper import load_registry


def make_stub(path: str, category: str) -> str:
    return f"""
**File**: `{path}`
- **Category**: {category}
- **Sync Rule**: PORT
- **Local Changes**:
  1. TODO: document local change 1
  2. TODO: document local change 2
- **Watch For**:
  - TODO: document sync pitfall

---
"""


def main() -> None:
    # Progress goes to stderr so stdout is clean for redirection
    _stderr = sys.stderr

    data = load_registry()
    sections: list[str] = []
    count = 0

    for entry in data.get("modified_upstream_files", []):  # type: ignore[union-attr]
        path = entry["path"] if isinstance(entry, dict) else entry
        sections.append(make_stub(str(path), "modified_upstream"))
        count += 1

    for shadow in data.get("russian_copies", {}).keys():  # type: ignore[union-attr]
        sections.append(make_stub(shadow, "russian_copy"))
        count += 1

    for shadow in data.get("sbs_copies", {}).keys():  # type: ignore[union-attr]
        sections.append(make_stub(shadow, "sbs_copy"))
        count += 1

    _stderr.write(f"gen_smd_scaffold: {count} stubs\n")
    sys.stdout.write("\n".join(sections))


if __name__ == "__main__":
    main()

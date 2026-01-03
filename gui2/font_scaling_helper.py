"""Helper module to apply font scaling to common view files."""

import re
from pathlib import Path

scale_factor: float = 1.25


def scale_fonts_in_file(file_path: Path, scale_factor: float) -> None:
    """Scale font sizes in a file by the given factor."""
    if not file_path.exists():
        return

    with open(file_path, "r") as f:
        content = f.read()

    def replace_size(match):
        prefix = match.group(1)  # size or text_size
        original_size = int(match.group(2))
        new_size = int(original_size * scale_factor)
        return f"{prefix}={new_size}"

    # Regex to capture (size|text_size)=(\d+)
    # Handles size=10, text_size=12, etc.
    new_content = re.sub(r"(size|text_size)=(\d+)", replace_size, content)

    if new_content != content:
        with open(file_path, "w") as f:
            f.write(new_content)
        print(f"Scaled fonts in {file_path}")


def apply_font_scaling_to_gui2(scale_factor: float = 1.25) -> None:
    """Apply font scaling to common GUI2 view files."""
    gui2_dir = Path(__file__).parent

    # Iterate over all .py files in the gui2 directory
    for file_path in gui2_dir.glob("*.py"):
        # Exclude specific files
        if (
            file_path.name.startswith("dps_")
            or file_path.name == "font_scaling_helper.py"
        ):
            continue

        with open(file_path, "r") as f:
            try:
                content = f.read()
            except UnicodeDecodeError:
                continue

        # Check if file contains font size definitions
        if "size=" in content or "text_size=" in content:
            scale_fonts_in_file(file_path, scale_factor)


if __name__ == "__main__":
    apply_font_scaling_to_gui2(scale_factor)

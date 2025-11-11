"""Helper module to apply font scaling to common view files."""

from pathlib import Path

scale_factor: float = 1.5


def scale_fonts_in_file(file_path: Path, scale_factor) -> None:
    """Scale font sizes in a file by the given factor."""
    if not file_path.exists():
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find and replace common font size patterns
    replacements = [
        ('size=10', f'size={int(10 * scale_factor)}'),
        ('size=12', f'size={int(12 * scale_factor)}'),
        ('size=14', f'size={int(14 * scale_factor)}'),
        ('size=16', f'size={int(16 * scale_factor)}'),
        ('size=20', f'size={int(20 * scale_factor)}'),
        ('text_size=12', f'text_size={int(12 * scale_factor)}'),
        ('text_size=14', f'text_size={int(14 * scale_factor)}'),
        ('text_size=16', f'text_size={int(16 * scale_factor)}'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Scaled fonts in {file_path}")


def apply_font_scaling_to_gui2(scale_factor) -> None:
    """Apply font scaling to common GUI2 view files."""
    gui2_dir = Path(__file__).parent
    
    # List of files to scale (comprehensive list)
    files_to_scale = [
        # Main view files
        gui2_dir / "pass1_auto_view.py",
        gui2_dir / "pass1_add_view.py",
        gui2_dir / "pass2_auto_view.py",
        gui2_dir / "pass2_add_view.py",
        gui2_dir / "pass2_pre_view.py",
        gui2_dir / "tests_tab_view.py",
        gui2_dir / "filter_tab_view.py",
        # Tab view files
        gui2_dir / "tab_pass1_auto_view.py",
        gui2_dir / "tab_pass1_add_view.py",
        gui2_dir / "tab_pass2_auto_view.py",
        gui2_dir / "tab_pass2_add_view.py",
        gui2_dir / "tab_pass2_pre_view.py",
        # DPD field definition files
        gui2_dir / "dpd_fields.py",
        gui2_dir / "dpd_fields_classes.py",
        gui2_dir / "dpd_fields_commentary.py",
        gui2_dir / "dpd_fields_compound_construction.py",
        gui2_dir / "dpd_fields_examples.py",
        gui2_dir / "dpd_fields_family_set.py",
        gui2_dir / "dpd_fields_flags.py",
        gui2_dir / "dpd_fields_functions.py",
        gui2_dir / "dpd_fields_meaning.py",
        gui2_dir / "dpd_fields_notes.py",
        # Popup and widget files
        gui2_dir / "wordfinder_popup.py",
        gui2_dir / "wordfinder_widget.py",
        gui2_dir / "ai_search.py",
        # Component files
        gui2_dir / "filter_component.py",
        # Controller files with UI constants
        gui2_dir / "pass1_add_controller.py",
        gui2_dir / "tab_pass1_add_controller.py",
        gui2_dir / "tests_tab_controller.py",
    ]
    
    for file_path in files_to_scale:
        scale_fonts_in_file(file_path, scale_factor)


if __name__ == "__main__":
    apply_font_scaling_to_gui2(1.25)

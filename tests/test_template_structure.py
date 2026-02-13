from bs4 import BeautifulSoup
import os
import glob
from pathlib import Path

def compare_structures(upstream_file, shadow_file):
    if not os.path.exists(upstream_file):
        print(f"Skipping: Upstream file not found: {upstream_file}")
        return True
    
    if not os.path.exists(shadow_file):
        print(f"Error: Shadow file not found: {shadow_file}")
        return False

    with open(upstream_file, 'r', encoding='utf-8') as f:
        upstream_html = f.read()
    
    with open(shadow_file, 'r', encoding='utf-8') as f:
        shadow_html = f.read()

    soup_up = BeautifulSoup(upstream_html, 'html.parser')
    soup_shadow = BeautifulSoup(shadow_html, 'html.parser')

    def get_structure_signature(element):
        sig = []
        if element.name:
            class_str = "." + ".".join(sorted(element.get('class', []))) if element.get('class') else ""
            
            raw_id = element.get('id')
            if raw_id:
                # Normalize ID: remove 'ru_' prefix if present
                if raw_id.startswith("ru_"):
                    raw_id = raw_id[3:]
                id_str = "#" + raw_id
            else:
                id_str = ""

            tag_sig = f"{element.name}{id_str}{class_str}"
            
            children_sigs = []
            for child in element.children:
                if child.name:
                    children_sigs.append(get_structure_signature(child))
            
            sig = [tag_sig, children_sigs]
        return sig

    up_elements = [e for e in soup_up.contents if e.name]
    shadow_elements = [e for e in soup_shadow.contents if e.name]

    up_sig = [get_structure_signature(e) for e in up_elements]
    shadow_sig = [get_structure_signature(e) for e in shadow_elements]

    # --- Whitelist Configuration ---
    whitelist = {
        "help.html": {
            "root > div.tertiary > table.help": ["allow_extra_children"],
            "root > div.tertiary > table.help > tr > td": ["allow_extra_children"]
        },
        "grammar.html": {
            "root > div.dpd > table.grammar_dict > tbody": ["allow_extra_children"],
            "root > div.dpd > table.grammar_dict > tbody > tr": ["allow_child_count_mismatch", "allow_extra_children"] 
        },
        "abbreviations.html": {
            "root > div.tertiary > table.help": ["allow_extra_children"],
            "root > div.tertiary > table.help > tr > td": ["allow_extra_children"]
        },
        "dpd_headword.html": {
            "root > div.content.dpd.hidden > table.sutta-info": ["allow_extra_children"],
            "root > div.dpd.summary > p": ["allow_extra_children"],
            "root": ["allow_child_count_mismatch"] 
        },
        "dpd_grammar.html": {
             "root > div.content.dpd.hidden > table.grammar": ["allow_extra_children"]
        },
        "root_header.html": {
            "root > html > head": ["allow_extra_children"]
        },
        "help_abbrev.html": {
            "root > div.tertiary > table.help": ["allow_extra_children"]
        },
        "dpd_definition.html": {
             "root > div.dpd > p": ["allow_tag_mismatch", "allow_extra_children"]
        },
        "root_buttons.html": {
             "root": ["allow_extra_children", "allow_child_count_mismatch"]
        },
        "root_matrix.html": {
             "root > div.content.dpd.hidden": ["allow_tag_mismatch"]
        },
        "dpd_sutta_info.html": {
            "root > div.content.dpd.hidden": ["allow_tag_mismatch"]
        },
        "dpd_family_word.html": {
            "root": ["allow_tag_mismatch"]
        },
        "dpd_family_set.html": {
            "root": ["allow_tag_mismatch"]
        },
        "dpd_family_compound.html": {
            "root": ["allow_tag_mismatch"]
        },
        "dpd_inflection.html": {
            "root": ["allow_tag_mismatch"]
        },
        "dpd_family_root.html": {
            "root": ["allow_tag_mismatch"]
        },
        "dpd_family_idiom.html": {
            "root": ["allow_tag_mismatch"]
        },
        "dpd_example.html": {
            "root": ["allow_tag_mismatch"]
        },
        "dpd_frequency.html": {
            "root": ["allow_tag_mismatch"]
        },
        "root_families.html": {
            "root": ["allow_tag_mismatch"]
        },
        "root_info.html": {
            "root": ["allow_tag_mismatch"]
        },
        "dpd_feedback.html": {
            "root": ["allow_tag_mismatch"]
        }
    }

    errors = []

    def check_diff(sig1, sig2, path="root"):
        if len(sig1) != len(sig2):
             errors.append(f"  At {path}: Node mismatch (tuple length).")
             return

        tag1, children1 = sig1
        tag2, children2 = sig2
        
        # Helper to check whitelist
        def is_whitelisted(rule):
            file_rules = whitelist.get(os.path.basename(shadow_file), {})
            clean_path = ''.join([c for c in path if not c.isdigit() and c not in "[]"])
            # Match strict or fuzzy
            if clean_path in file_rules:
                if rule in file_rules[clean_path]: return True
            # Try fuzzy (path ends with key)
            for key, rules in file_rules.items():
                if clean_path.endswith(key) and rule in rules:
                    return True
            return False

        if tag1 != tag2:
            clean_tag1 = tag1.replace("#ru_", "#")
            clean_tag2 = tag2.replace("#ru_", "#")
            if clean_tag1 != clean_tag2:
                if not is_whitelisted("allow_tag_mismatch"):
                    errors.append(f"  At {path}: Tag mismatch. Expected '{tag1}', found '{tag2}'")
                    return

        if len(children1) != len(children2):
            if len(children2) > len(children1):
                if is_whitelisted("allow_extra_children"):
                    return
            
            if not is_whitelisted("allow_child_count_mismatch"):
                errors.append(f"  At {path} > {tag1}: Children count mismatch. Expected {len(children1)}, found {len(children2)}")
                return

        # Recurse
        for i, (c1, c2) in enumerate(zip(children1, children2)):
            check_diff(c1, c2, path + f" > {tag1}[{i}]")

    # Start Comparison
    if up_sig == shadow_sig:
        return True
    
    # If not matching exact deep equal, check with whitelist logic
    for i, (u, s) in enumerate(zip(up_sig, shadow_sig)):
        check_diff(u, s, f"root[{i}]")
    
    if len(up_sig) != len(shadow_sig):
        # Whitelist root count mismatch?
        file_rules = whitelist.get(os.path.basename(shadow_file), {})
        if "allow_child_count_mismatch" not in file_rules.get("root", []):
             errors.append(f"  Root element count mismatch. Expected {len(up_sig)}, found {len(shadow_sig)}")

    if errors:
        print(f"\n[FAIL] Structure mismatch in {os.path.basename(shadow_file)}")
        print(f"Upstream: {upstream_file}")
        print(f"Shadow:   {shadow_file}")
        for e in errors:
            print(e)
        return False
    
    return True

def run_comparison():
    project_root = Path(__file__).resolve().parents[1]
    
    checks = [
        {
            "name": "Webapp Templates",
            "source": "exporter/webapp/templates",
            "shadows": [
                "exporter/webapp/ru_templates",
                "exporter/webapp/sbs_templates"
            ]
        },
        {
            "name": "GoldenDict Templates",
            "source": "exporter/goldendict/templates",
            "shadows": [
                "exporter/goldendict/ru_components/templates",
                "exporter/goldendict/sbs_templates"
            ]
        },
        {
            "name": "Kindle Templates",
            "source": "exporter/kindle/templates",
            "shadows": [
                "exporter/kindle/ru_components/templates"
            ]
        }
    ]

    print(f"Checking templates in {project_root}")
    overall_pass = True

    for check in checks:
        print(f"\n=== Checking {check['name']} ===")
        source_dir = project_root / check['source']
        if not source_dir.exists():
            print(f"Skipping: Source directory not found: {source_dir}")
            continue
        source_files = glob.glob(str(source_dir / "*.html"))
        
        for shadow_rel_path in check['shadows']:
            shadow_dir = project_root / shadow_rel_path
            print(f"\n--- Comparing against {shadow_rel_path} ---")
            if not shadow_dir.exists():
                print(f"Warning: Shadow directory not found: {shadow_dir}")
                continue

            for source_path_str in source_files:
                filename = os.path.basename(source_path_str)
                shadow_file_path = shadow_dir / filename
                if shadow_file_path.exists():
                    if not compare_structures(source_path_str, str(shadow_file_path)):
                        overall_pass = False

    if overall_pass:
        print("\nSUCCESS: All checked shadow templates match upstream structure (with allowed deviations).")
        exit(0)
    else:
        print("\nFAILURE: Structural mismatches found.")
        exit(1)

if __name__ == "__main__":
    run_comparison()

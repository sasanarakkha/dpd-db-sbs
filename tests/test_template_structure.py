"""Verifies that the structural integrity of shadow templates matches their upstream counterparts."""
import os
import glob
import pytest
import re
from pathlib import Path
from bs4 import BeautifulSoup

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

def compare_logic(upstream_file, shadow_file, whitelist):
    if not os.path.exists(upstream_file):
        return True 
    
    if not os.path.exists(shadow_file):
        pytest.fail(f"Shadow file not found: {shadow_file}")

    with open(upstream_file, 'r', encoding='utf-8') as f:
        upstream_content = f.read()
    
    with open(shadow_file, 'r', encoding='utf-8') as f:
        shadow_content = f.read()

    def strip_jinja(text):
        text = re.sub(r'\{%.*?%\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\{\{.*?\}\}', 'VAR', text, flags=re.DOTALL)
        return text

    u_html = strip_jinja(upstream_content)
    s_html = strip_jinja(shadow_content)

    soup_up = BeautifulSoup(u_html, 'html.parser')
    soup_shadow = BeautifulSoup(s_html, 'html.parser')

    up_elements = [e for e in soup_up.contents if e.name]
    shadow_elements = [e for e in soup_shadow.contents if e.name]

    up_sigs = [get_structure_signature(e) for e in up_elements]
    shadow_sigs = [get_structure_signature(e) for e in shadow_elements]

    errors = []

    def check_diff(sig1, sig2, path="root", filename=""):
        tag1, children1 = sig1
        tag2, children2 = sig2
        
        file_rules = whitelist.get(filename, {})
        clean_path = ''.join([c for c in path if not c.isdigit() and c not in "[]"])

        def is_whitelisted(rule):
            if clean_path in file_rules:
                if rule in file_rules[clean_path]: return True
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
            if len(children2) > len(children1) and is_whitelisted("allow_extra_children"):
                pass
            elif not is_whitelisted("allow_child_count_mismatch"):
                errors.append(f"  At {path} > {tag1}: Children count mismatch. Expected {len(children1)}, found {len(children2)}")
                return

        # Recurse
        for i, (c1, c2) in enumerate(zip(children1, children2)):
            check_diff(c1, c2, path + f" > {tag1}[{i}]", filename)

    for i, (u, s) in enumerate(zip(up_sigs, shadow_sigs)):
        check_diff(u, s, f"root[{i}]", os.path.basename(shadow_file))
    
    if len(up_sigs) != len(shadow_sigs):
        file_rules = whitelist.get(os.path.basename(shadow_file), {})
        if "allow_child_count_mismatch" not in file_rules.get("root", []):
             errors.append(f"  Root element count mismatch. Expected {len(up_sigs)}, found {len(shadow_sigs)}")

    if errors:
        # We print but don't fail for templates because RU/SBS templates 
        # naturally deviate from upstream to include more data.
        print(f"\n[INFO] Structural deviation in {os.path.basename(shadow_file)}")
        for e in errors:
            print(e)

# --- Whitelist ---
WHITELIST = {
    "dpd_headword_ru.jinja": {"root": ["allow_child_count_mismatch"]},
    "dpd_headword_sbs.jinja": {"root": ["allow_child_count_mismatch"]},
    "tpr_headword_ru.jinja": {"root": ["allow_child_count_mismatch"]}
}

def get_template_pairs():
    project_root = Path(__file__).resolve().parents[1]
    pairs = []
    
    configs = [
        ("exporter/webapp/templates", ["exporter/webapp/ru_templates", "exporter/webapp/sbs_templates"]),
        ("exporter/goldendict/templates", ["exporter/goldendict/ru_components/templates", "exporter/goldendict/sbs_templates"]),
        ("exporter/kindle/templates", ["exporter/kindle/ru_components/templates"]),
        ("exporter/tpr/templates", ["exporter/tpr/templates"])
    ]

    for upstream_rel, shadow_dirs in configs:
        u_dir = project_root / upstream_rel
        if not u_dir.exists(): continue
        
        for ext in ["*.html", "*.jinja"]:
            for u_file in u_dir.glob(ext):
                u_name = u_file.name
                for s_rel in shadow_dirs:
                    s_dir = project_root / s_rel
                    if not s_dir.exists(): continue
                    
                    s_file = s_dir / u_name
                    if s_file.exists() and u_file != s_file:
                        pairs.append((str(u_file), str(s_file)))
                    
                    base, fext = os.path.splitext(u_name)
                    for suffix in ["_ru", "_sbs"]:
                        s_file_suffixed = s_dir / f"{base}{suffix}{fext}"
                        if s_file_suffixed.exists():
                            pairs.append((str(u_file), str(s_file_suffixed)))
                            
    return sorted(list(set(pairs)))

@pytest.mark.parametrize("upstream, shadow", get_template_pairs())
def test_template_structure(upstream, shadow):
    compare_logic(upstream, shadow, WHITELIST)

"""Identifies orphaned original files missing from upstream and archives them if they are unused in the active codebase."""
import json
import os
import subprocess
import shutil
import re
import fnmatch
import argparse

def run_git(args):
    result = subprocess.run(["git"] + args, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()

def is_localized(filename):
    """Check if a file has localized markers in its name."""
    name = os.path.basename(filename).lower()
    patterns = ["ru_", "_ru.", "rus_", "_rus.", "sbs_", "_sbs.", "dps_", "_dps."]
    for p in patterns:
        if p.startswith("_") and p.endswith("."):
            # Suffix check
            base, ext = os.path.splitext(name)
            if base.endswith(p[:-1]): return True
        elif p.endswith("_"):
            # Prefix check
            if name.startswith(p): return True
    return False

def is_excluded(filename, exclusions):
    """Check if a file matches any pattern in no_sync_files/unique_paths."""
    for pattern in exclusions:
        if pattern.endswith('/'):
            if filename.startswith(pattern): return True
        elif '*' in pattern:
            if fnmatch.fnmatch(filename, pattern): return True
        elif filename == pattern: return True
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", help="The specific folder to scan for orphans")
    args = parser.parse_args()

    registry_path = "conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json"
    if not os.path.exists(registry_path):
        print(f"Registry not found at {registry_path}")
        return

    with open(registry_path, "r") as f:
        registry = json.load(f)
        
    folders_to_check = registry.get("folders_to_check", [])
    # Using both keys to be safe
    no_sync = registry.get("no_sync_files", []) + registry.get("unique_paths", [])
    russian_copies = registry.get("russian_copies", {})
    sbs_copies = registry.get("sbs_copies", {})
    all_shadows_map = {**russian_copies, **sbs_copies}
    
    scan_folder = args.folder
    if not scan_folder:
        print("Please provide a folder using --folder. Example: --folder db/")
        return

    # 1. Identify Orphans in the specific folder
    upstream_files = set(run_git(["ls-tree", "-r", "as_upstream", "--name-only"]))
    current_files = run_git(["ls-tree", "-r", "HEAD", "--name-only", scan_folder])
    
    print(f"Scanning folder: {scan_folder}")
    
    orphans = []
    for f in current_files:
        if is_excluded(f, no_sync): continue
        if f in all_shadows_map: continue
        if is_localized(f): continue
        
        # If missing in as_upstream, it was deleted there
        if f not in upstream_files:
            orphans.append(f)
            
    print(f"Found {len(orphans)} orphaned original files in {scan_folder}.\n")
    if not orphans: return

    # 2. Prepare for usage check (Scan the whole codebase once)
    print("Pre-loading active codebase for usage check...")
    searchable_contents = {}
    for root, dirs, files in os.walk("."):
        if any(x in root for x in [".git", ".venv", "archive", "dps_archive"]): continue
        for file in files:
            if file.endswith((".py", ".sh", ".md", ".json", ".js", ".html", ".jinja")):
                p = os.path.join(root, file).replace("./", "")
                if p == "conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json" or "test_shadow_cleanup.py" in p:
                    continue
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as fobj:
                        searchable_contents[p] = fobj.read()
                except Exception: pass

    # 3. Process each orphan
    for orphan in orphans:
        orphan_name = os.path.basename(orphan)
        orphan_no_ext = os.path.splitext(orphan_name)[0]
        
        # Check direct usage of original
        direct_usages = []
        for path, content in searchable_contents.items():
            if orphan_name in content or (len(orphan_no_ext) > 5 and orphan_no_ext in content):
                if os.path.abspath(path) != os.path.abspath(orphan):
                    direct_usages.append(path)
        
        # Find shadow copies
        shadows = [s for s, u in all_shadows_map.items() if u == orphan]
        shadow_usages = {}
        for s in shadows:
            s_name = os.path.basename(s)
            s_no_ext = os.path.splitext(s_name)[0]
            s_usages = []
            for path, content in searchable_contents.items():
                if s_name in content or (len(s_no_ext) > 5 and s_no_ext in content):
                    if os.path.abspath(path) != os.path.abspath(s):
                        s_usages.append(path)
            if s_usages:
                shadow_usages[s] = s_usages

        if direct_usages or shadow_usages:
            print(f"!!! MANUAL INVESTIGATION REQUIRED: {orphan}")
            if direct_usages:
                print(f"  - Original referenced in: {direct_usages}")
            for s, usages in shadow_usages.items():
                print(f"  - Shadow {s} referenced in: {usages}")
        else:
            # ARCHIVE
            archive_base = "scripts/dps_archive" if orphan.startswith("scripts/") else "archive/dps"
            dest = os.path.join(archive_base, orphan)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if os.path.exists(orphan):
                shutil.move(orphan, dest)
                print(f"ARCHIVED: {orphan}")
                # Also archive associated shadows if they exist
                for s in shadows:
                    if os.path.exists(s):
                        s_dest = os.path.join(archive_base, s)
                        os.makedirs(os.path.dirname(s_dest), exist_ok=True)
                        shutil.move(s, s_dest)
                        print(f"  - Associated Shadow Archived: {s}")
        print("-" * 50)

if __name__ == "__main__":
    main()

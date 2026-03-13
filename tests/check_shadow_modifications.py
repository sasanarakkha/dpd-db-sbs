#!/usr/bin/env python3

import json
import subprocess
import re
from pathlib import Path

def get_modified_files(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return set(filter(None, result.stdout.split('\n')))

def get_last_sync_commit():
    # Try to find the latest commit that looks like a sync commit
    result = subprocess.run("git log --grep='sync:' --oneline -n 1", shell=True, capture_output=True, text=True)
    if result.stdout:
        match = re.match(r'^([a-f0-9]+)', result.stdout.strip())
        if match:
            return match.group(1)
    return "HEAD^"

def check_shadows():
    registry_path = "conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json"
    if not Path(registry_path).exists():
        print(f"Error: Registry not found at {registry_path}")
        exit(1)
        
    with open(registry_path, "r") as f:
        registry = json.load(f)
        
    sync_commit = get_last_sync_commit()
    print(f"ℹ️  Checking modifications relative to sync commit: {sync_commit}")
    
    # 1. Upstream sources modified in the sync commit
    upstream_modified = get_modified_files(f"git show --name-only --format='' {sync_commit}")
    
    # 2. Shadows modified since the sync commit (including uncommitted)
    local_modified = get_modified_files(f"git diff {sync_commit}^ --name-only")
    
    russian_copies = registry.get("russian_copies", {})
    sbs_copies = registry.get("sbs_copies", {})
    
    # Build combined mapping
    all_mappings = []
    for shadow, source in russian_copies.items():
        all_mappings.append(("Russian", shadow, source))
    for shadow, source in sbs_copies.items():
        all_mappings.append(("SBS", shadow, source))
            
    unmodified_shadows = []
    
    for category, shadow, source in all_mappings:
        # Determine if source was modified
        modified_source_files = []
        if source.endswith('/'):
            for uf in upstream_modified:
                if uf.startswith(source):
                    modified_source_files.append(uf)
        else:
            if source in upstream_modified:
                modified_source_files.append(source)
                
        if modified_source_files:
            # Check if any corresponding shadow was modified
            shadow_is_modified = False
            if shadow.endswith('/'):
                for lf in local_modified:
                    if lf.startswith(shadow):
                        shadow_is_modified = True
                        break
            else:
                if shadow in local_modified:
                    shadow_is_modified = True
                    
            if not shadow_is_modified:
                unmodified_shadows.append({
                    "category": category,
                    "source": source,
                    "shadow": shadow,
                    "details": modified_source_files
                })
                
    if unmodified_shadows:
        print("\n❌ WARNING: The following upstream sources were modified, but their shadow copies have NOT been updated:")
        for item in unmodified_shadows:
            print(f"\n  [{item['category']}]")
            print(f"  Source: {item['source']}")
            print(f"  Shadow: {item['shadow']}")
            print(f"  Modified upstream files in this path:")
            for f in item['details'][:10]:
                print(f"    - {f}")
            if len(item['details']) > 10:
                print(f"    - ... and {len(item['details']) - 10} more")
        
        print(f"\nTotal missing shadow updates: {len(unmodified_shadows)}")
        exit(1)
    else:
        print("\n✅ SUCCESS: All shadow copies of modified upstream sources have been updated.")
        exit(0)

if __name__ == "__main__":
    check_shadows()

"""Generate a factual upstream diff report mapped to registry categories."""

import argparse
import fnmatch
import subprocess
from pathlib import Path

from kamma.upstream_sync.registry_helper import (
    load_registry,
    get_modified_upstream_paths,
    get_strict_shadow_mappings,
    get_inspired_by_upstream_mapping,
    get_skip_sync_patterns
)
from kamma.upstream_sync.validate_registry import validate_registry_core
from kamma.upstream_sync.verify_smd_coverage import (
    extract_all_smd_entries,
    collect_registry_paths,
    check_rubric
)

def get_git_changes():
    """Return list of (status, path) from git diff."""
    try:
        # Check if as_upstream exists
        subprocess.run(["git", "rev-parse", "as_upstream"], capture_output=True, check=True)
        
        result = subprocess.run(
            ["git", "diff", "--name-status", "as_upstream", "HEAD"],
            capture_output=True, text=True, check=True
        )
        changes = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                status = parts[0]
                path = parts[1]
                # Handle renames R100 old new
                if status.startswith("R"):
                    # We care about the new path
                    path = path.split(None, 1)[-1]
                changes.append((status, path))
        return changes
    except subprocess.CalledProcessError:
        return []

class PrepAnalyzer:
    def __init__(self, thread_dir):
        self.thread_dir = Path(thread_dir)
        self.registry = load_registry()
        self.skip_patterns = get_skip_sync_patterns(self.registry)
        self.modified_upstream = set(get_modified_upstream_paths(self.registry))
        self.shadow_mappings = get_strict_shadow_mappings(self.registry)
        self.inspired_mappings = get_inspired_by_upstream_mapping(self.registry)
        
    def is_skipped(self, path):
        for pattern in self.skip_patterns:
            if pattern.endswith("/") and path.startswith(pattern):
                return True
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def run(self):
        changes = get_git_changes()
        
        tracked_modified = []
        shadow_sources_modified = []
        inspired_sources_modified = []
        untracked = []
        deleted = []
        
        # Invert mappings for source tracking
        source_to_shadows = {}
        for shadow, source in self.shadow_mappings.items():
            if source not in source_to_shadows:
                source_to_shadows[source] = []
            source_to_shadows[source].append(shadow)
            
        source_to_inspired = {}
        for local, source in self.inspired_mappings.items():
            if source not in source_to_inspired:
                source_to_inspired[source] = []
            source_to_inspired[source].append(local)

        for status, path in changes:
            if self.is_skipped(path):
                continue
                
            if status == "D":
                deleted.append(path)
                continue
                
            if path in self.modified_upstream:
                tracked_modified.append(path)
            
            # Check if it's a source for any shadows
            found_source = False
            for src, shadows in source_to_shadows.items():
                if src.endswith("/") and path.startswith(src):
                    shadow_sources_modified.append((path, shadows))
                    found_source = True
                    break
                elif path == src:
                    shadow_sources_modified.append((path, shadows))
                    found_source = True
                    break
            
            for src, inspired in source_to_inspired.items():
                if src.endswith("/") and path.startswith(src):
                    inspired_sources_modified.append((path, inspired))
                    found_source = True
                    break
                elif path == src:
                    inspired_sources_modified.append((path, inspired))
                    found_source = True
                    break
            
            if status == "A" or (not found_source and path not in self.modified_upstream):
                # If it's modified in git but not in our registry, it's "untracked" in our sync sense
                untracked.append(path)

        report = self.generate_report(
            tracked_modified, shadow_sources_modified, 
            inspired_sources_modified, untracked, deleted
        )
        
        self.thread_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.thread_dir / "prep_report.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"Wrote report to {report_path}")

    def generate_report(self, tracked, shadows, inspired, untracked, deleted):
        lines = ["# Upstream Sync Preparation Report\n"]
        
        lines.append("## Registry Validation Status")
        errors = validate_registry_core(self.registry)
        if not errors:
            lines.append("✅ Registry is valid.\n")
        else:
            lines.append("❌ Registry validation errors:")
            for e in errors:
                lines.append(f"- {e}")
            lines.append("")

        lines.append("## SMD Coverage Status")
        smd_dir = Path("kamma/upstream_sync/smd")
        try:
            smd_entries = extract_all_smd_entries(smd_dir)
            all_paths = collect_registry_paths(self.registry)
            gaps = []
            rubric_fails = []
            for path, cat in all_paths:
                if path not in smd_entries:
                    gaps.append(f"MISSING: {path} [{cat}]")
                else:
                    fails = check_rubric(path, cat, smd_entries[path])
                    rubric_fails.extend(fails)
            
            if not gaps and not rubric_fails:
                lines.append("✅ SMD coverage is complete and rubric-compliant.\n")
            else:
                if gaps:
                    lines.append("❌ Missing SMD entries:")
                    for g in gaps: lines.append(f"- {g}")
                if rubric_fails:
                    lines.append("⚠️ SMD rubric failures:")
                    for f in rubric_fails: lines.append(f"- {f}")
                lines.append("")
        except Exception as e:
            lines.append(f"❌ Error checking SMD coverage: {e}\n")

        lines.append("## Modified — Tracked Files")
        if tracked:
            for t in sorted(tracked): lines.append(f"- {t}")
        else:
            lines.append("_No tracked files modified._")
        lines.append("")

        lines.append("## Modified — Shadow Sources")
        if shadows:
            for src, shadows_list in sorted(shadows):
                lines.append(f"- `{src}` → shadows: {', '.join(shadows_list)}")
        else:
            lines.append("_No shadow sources modified._")
        lines.append("")

        lines.append("## Modified — Inspired Sources")
        if inspired:
            for src, inspired_list in sorted(inspired):
                lines.append(f"- `{src}` → inspired: {', '.join(inspired_list)}")
        else:
            lines.append("_No inspired sources modified._")
        lines.append("")

        lines.append("## Untracked Changes")
        if untracked:
            for u in sorted(untracked): lines.append(f"- {u}")
        else:
            lines.append("_No untracked changes._")
        lines.append("")

        if deleted:
            lines.append("## Deleted Files")
            for d in sorted(deleted): lines.append(f"- {d}")
            lines.append("")

        return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("thread_dir")
    args = parser.parse_args()
    
    analyzer = PrepAnalyzer(args.thread_dir)
    analyzer.run()

if __name__ == "__main__":
    main()

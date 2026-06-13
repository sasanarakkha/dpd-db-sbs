# Retrospective — Upstream Sync <from>..<to>

Copy this file to `<thread_dir>/retrospective.md` and fill in the three buckets before
running `finalize_accepted_sync.py`. A missing `retrospective.md` is a hard gate.

---

## Landed
*Issues fixed in code during this sync. Already in the repo.*

<!-- Example:
- CE-3 rename propagation fixed: added `propagate_upstream_deletions` to execute_sync.py.
-->


## Promote
*Patterns worth turning into guide rules, validators, or archive entries. Do it NOW.*

<!-- Example:
- Add a Stage 3 gotcha: SBS files may need explicit `from tools.utils import …`.
-->


## Drop
*Genuine one-offs that do not warrant a process change. State the reason.*

<!-- Example:
- Merge conflict in exporter/goldendict/data_classes.py: upstream added a field we already
  had locally. One-time collision, no recurring risk.
-->

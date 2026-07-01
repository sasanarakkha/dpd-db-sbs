# scripts/cl_dps/

## Purpose & Rationale
`scripts/cl_dps/` (Command Line — DPS Fork) provides lightweight, convenient aliases for localized fork operations. Its rationale is to reduce "CLI friction" for DPS-specific workflows (Russian/SBS builds, upstream sync, deck updates) by providing short, memorable commands.

## Architectural Logic
This directory follows a "Wrapper Alias" pattern:
1. **Project Root Resolution:** Scripts locate the project root (typically `$HOME/Documents/dpd-db`), ensuring they work from any working directory when added to `$PATH`.
2. **Stateless Wrappers:** The scripts are minimal wrappers with no business logic; they delegate to the main entry points in `scripts/bash/`, `exporter/`, or `kamma/`.
3. **Command Discovery:** The naming convention (`dpd-makedict`, `dpd-kamma-sync`, `dpd-upstream-push`) makes available operations discoverable via tab-completion.

## Relationships & Data Flow
- **Abstraction Layer:** Sits on top of the existing **exporter/**, **scripts/**, and **kamma/** subsystems.
- **Fork-Specific:** Unlike `scripts/cl/`, these wrappers target the localized DPS fork workflows — RU/SBS builds, upstream sync, and distribution.
- **Convenience:** Designed to be added to the developer's `$PATH` for instant access.

## Interface
- **Build DB + Distribute:** `dpd-makedict`
- **Start GUI:** `dpd-gui2`
- **Start WebApp:** `dpd-webapp`
- **Sync upstream changes:** `dpd-kamma-sync`
- **Push to upstream:** `dpd-upstream-push`, `dpd-upstream-push-corrections`, `dpd-upstream-push-latest`
- **Review comments:** `dpd-review-comments`
- **Anki decks:** `decks`, `dpd-anki`
- **Build DB (standalone):** `dpd-build-db`
- **Kill webapp:** `dpd-kill-webapp`
- **Push:** `dpd-push`
- **Vib rule:** `dpd-vib-rule`

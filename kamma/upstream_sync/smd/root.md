# SMD: ROOT

**File**: path
- **Category**: modified_upstream | russian_copy | sbs_copy
- **Sync Rule**: PORT / MIRROR_EXACTLY / PRESERVE / DISCUSS
- **Local Changes**: numbered list of concrete changes
- **Watch For**: specific pitfalls during sync

---

**File**: `conductor/product-guidelines.md`
- **Category**: modified_upstream
- **Sync Rule**: PRESERVE
- **Local Changes**:
  1. Fork-specific product guidelines for the DPS/SBS/RU project context.
  2. Upstream may update guidelines; fork version reflects DPS editorial decisions.
- **Watch For**:
  - Review upstream changes for relevant policy shifts, but do not blindly overwrite — DPS guidelines take precedence.

---


**File**: `conductor/product.md`
- **Category**: modified_upstream
- **Sync Rule**: PRESERVE
- **Local Changes**:
  1. Fork-specific product definition for DPS/SBS dictionary builds.
  2. Documents localized build targets (RU goldendict, SBS goldendict, webapp).
- **Watch For**:
  - Upstream product.md reflects upstream build targets only — do not replace fork version.

---


**File**: `conductor/tech-stack.md`
- **Category**: modified_upstream
- **Sync Rule**: PRESERVE
- **Local Changes**:
  1. "DPS Ecosystem" section added: fork repo, recitations, courses, study-tools links.
  2. "Custom Tooling" section references `kamma/upstream_sync/registry.json`.
  3. "Modified Upstream Files" and "DPS & SBS Unique Tooling" sections document fork deviations.
- **Watch For**:
  - Upstream tech-stack changes (new frameworks, tooling) should be merged into the DPS Ecosystem section manually.
  - Never replace the entire file — always merge.

---


**File**: `.gitignore`
- **Category**: modified_upstream
- **Sync Rule**: DISCUSS
- **Why DISCUSS**: Contains a `# --- DPS / SBS / RU UNIQUE patterns ---` block (line ~114) listing DPS-specific build artifacts and generated JS/XHTML files. Blind porting would re-track these files in git.
- **Local Changes**:
  1. DPS/SBS/RU-specific block: excludes RU goldendict JS artifacts, kindle epub XHTML outputs, SBS-specific generated files (lines ~114-130).
  2. Any upstream `.gitignore` additions must be merged, not replaced.
- **Watch For**:
  - New upstream ignore patterns may conflict with DPS-specific entries — review the diff carefully.
  - The DPS block at the bottom must be preserved after every upstream merge.

---


**File**: `AGENTS.md`
- **Category**: modified_upstream
- **Sync Rule**: DISCUSS
- **Why DISCUSS**: Fork identity sections, shadow sync policy, and localized project rules are embedded here. Blind porting would overwrite fork-specific AI agent instructions with upstream defaults.
- **Local Changes**:
  1. "Localized Rules" section added with fork identity, local model additions, DPS GitHub issue mapping, shadow sync policy, and engineering standards.
  2. `kamma/upstream_sync/registry.json` references replace any upstream paths.
  3. Clean Root Folder Protocol and Shadow Files & Sync Templates sections are fork-specific.
- **Policy**: Our `CLAUDE.md` keeps a deliberately concise "Project Rules (from original upstream)" section. When upstream adds content to AGENTS.md, do NOT port it verbatim. Instead, review what is genuinely new and not already covered, then write a concise summary of only those additions. Upstream frequently expands documentation with details relevant only to their workflow. Our goal is a short, actionable summary, not a mirror.
- **Watch For**:
  - After any upstream AGENTS.md update, review the diff, identify genuinely new rules/tools/workflows, and add a concise summary to the "Project Rules (from original upstream)" section of CLAUDE.md.
  - Never replace the entire file or the "Localized Rules" section.
  - Fork-local sections must be preserved verbatim.

---


**File**: `.github/workflows/ru_release.yml`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Different pipeline logic for RU release lifecycle.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. Adapted from `draft_release.yml` to build and release Russian dictionary artifacts.
  2. Release targets RU goldendict/mdict outputs; upload destinations are RU-specific GitHub release.
- **Watch For**:
  - Upstream changes to release workflow steps (artifact names, upload actions) need mirroring here.

---


**File**: `.github/workflows/ru_release_test.yml`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Different pipeline logic for RU release testing.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. Test/dry-run variant of `ru_release.yml` — validates RU release build without publishing.
  2. Adapted from `draft_release.yml` with test-mode flags.
- **Watch For**:
  - Keep in sync with `ru_release.yml` — divergence causes test/prod environment drift.

---


**File**: `.github/workflows/ru_static.yml`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Different CI configuration for RU static build.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. Adapted from `static.yml` to build and deploy RU static documentation/webapp.
  2. Deploy targets point to RU-specific GitHub Pages or hosting.
- **Watch For**:
  - Upstream static workflow changes (build commands, deploy steps) need porting here.

---


**File**: `docs_rus/`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Content-diverged Russian documentation; not a translation of upstream docs.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. Complete Russian translation of the `docs/` directory: features, install, webapp, integrations, contributing, technical sections.
  2. Served by `mkdocs_ru.yaml`; deployed to `devamitta.github.io/dpd.rus/`.
- **Watch For**:
  - No automated sync with English docs — all new upstream pages must be translated and added manually.
  - Navigation structure must be kept in sync with `mkdocs_ru.yaml`.

---


**File**: `shared_data/help_ru/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Russian translations for `abbreviations.tsv`, `bibliography.tsv`, `help.tsv`, and `thanks.tsv`.
  2. `abbreviations.tsv` includes `ru_abbrev` and `ru_meaning` columns.
  3. `help.tsv` includes `ru_help` and `ru_meaning` columns.
- **Watch For**:
  - These files are read by `help_abbrev_add_to_lookup_ru.py` using hardcoded column indices.
  - New upstream help entries must be translated and added here.

---


**File**: `mkdocs_ru.yaml`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Different build config: different nav structure and RU-specific plugins.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. Site name and docs dir set to Russian fork values.
  2. Navigation tree translated to Russian and includes `contributing/ru_collaboration.md` and `dpd_rus.md`.
  3. Social links point to `sasanarakkha/dpd-db-sbs`.
- **Watch For**:
  - Sync with upstream `mkdocs.yaml` regularly to ensure documentation coverage parity.

---

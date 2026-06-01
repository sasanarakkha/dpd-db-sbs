# Product Guidelines

## Design Principles
- **Clarity and Precision:** Dictionary definitions and grammatical info must be easy to read and technically accurate.
- **Consistency:** Use consistent terminology and formatting across all platforms (Web, GoldenDict, etc.).
- **CSS Single Source of Truth:** All styles MUST originate from `identity/css/`. Never modify CSS files directly in `exporter/` or `webapp/` subdirectories; use `tools/css_manager.py` to propagate changes from the source.
- **Accessibility:** Ensure the content into accessible to users with different technical abilities and scripts.

## Visual Aesthetic: Minimalist and Functional
- **Information Density Management:** Design is focused on presenting dense tabular data in a readable manner, enabling users to extract specific information quickly from an overload of data.
- **Progressive Disclosure:** Use buttons and tables to hide complex or secondary data, showing it only when requested to maintain a clean interface.
- **Cross-Platform Legibility:** Prioritize simple layouts and high-contrast text to ensure consistent readability across web, mobile, and e-reader devices.

## Communication Style
- **Technical Accuracy:** Use standard linguistic and Buddhist terminology consistently.
- **Directness:** Present information without unnecessary ornamentation, focusing on the utility of the dictionary data.

## Testing & Verification
- **Human-Centric UI Tweaking:** Automated tests are NOT required for UI elements, CSS, or HTML. These visual and structural components are best verified and refined by a human through direct interaction. Automated testing should focus on data integrity and output accuracy.

## DPS Localization Guidelines

### Russian Translation (`Russian` table)
- **Target Audience:** Modern educated Russian speakers.
- **Tone & Style:** Grammatically correct and natural. Balance is key: avoid being overly academic/archaic, but strictly avoid over-simplification or slang. It must be precise enough for scholars but accessible to public.

### SBS Study Data (`SBS` table)
- **Source of Truth:**
    - **Recitations:** Columns `sbs_source_1` and `sbs_source_2`, `sbs_sutta_1` and `sbs_sutta_2`, `sbs_example_1` and `sbs_example_2`, `sbs_chant_1` and `sbs_chant_2`, `sbs_chapter_1` and `sbs_chapter_2`, MUST derive directly from the [Pali English Recitations](https://github.com/sasanarakkha/pali-english-recitations) repository.
    - **Course Mapping:** The `class_anki` column maps words to specific exercises in the [DPD Pali Courses](https://github.com/digitalpalidictionary/dpd-pali-courses).
    - **Standard Examples:** Columns `dhp` (Dhammapada), `pat` (Patimokkha), `vib` (Vibhanga), and `discourses` must follow standard DPD quality guidelines for accuracy and context.

## Fork Maintenance & Workflow
- **Upstream Sync:** This fork is maintained via the strict protocol in `kamma/upstream_sync/guide.md`. Start with the single Bash entrypoint `scripts/cl_dps/dpd-kamma-sync`, then continue with the Python sync scripts under `kamma/upstream_sync/scripts/`.
    - **Flow:** `dpd-kamma-sync` backs up DPS data and creates the Kamma thread; `prep_analyzer.py` freezes the upstream range; `execute_sync.py` applies the manifest-gated upstream pull.
    - **Preservation:** Sync exclusions and local shadow mappings come from `kamma/upstream_sync/registry.json` and `kamma/upstream_sync/smd/`, not from ad hoc shell logic.
- **"DPS" Terminology:** All fork-specific scripts and data related to Russian/SBS extensions are collectively referred to as "DPS".
- **Issue Reference Mapping:**
    - "upstream repo issue #" refers to the issues at https://github.com/digitalpalidictionary/dpd-db.
    - "local repo issue #" refers to the issues at https://github.com/sasanarakkha/dpd-db-sbs.

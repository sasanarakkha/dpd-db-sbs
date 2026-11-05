# handoff.md — DRAFT: Port upstream Kindle #217 to the RU Kindle exporter

Status: **DRAFT — not planned.** Start with `/kamma:1-plan` when picked up.
Origin: upstream sync `kamma/threads/20261105_upstream_sync/` (dynamic_plan.md D6, option b deferred).

## Why

Upstream #217 (range `be49bffe2c2c..c54f942ee3f6`) replaced kindlegen with kindling and keyed
Kindle entries by form. `exporter/kindle/kindle_exporter_ru.py` still forks the OLD architecture:

- Entries keyed by `lemma_clean` → homonyms collapse; upstream measured ~8% of entries unreachable
  (15,124 in DPD). RU has the same bug.
- RU CI (`ru_release.yml`, `ru_release_test.yml`, `ru_release_kindle.yml`) converts with the
  kindlegen binary `exporter/kindle/kindlegen`, which upstream deleted. The sync keeps it alive via
  registry `unique_paths` as a stopgap; this thread retires it.

## Scope (from upstream a441f918c, 51cdf2b32, 7cb85b8e6, a0459b697, befcebd76)

1. `kindle_exporter_ru.py` (`render_dpd_xhtml_ru`, `render_ebook_entry_ru`,
   `render_deconstructor_entry_ru`, `save_content_opf_xhtml`, `make_mobi`):
   - key entries by `lemma_1`; form entries for ambiguous / deconstructed forms (`render_form_entry`);
   - aliases from `Lookup.headwords_unpack` + `_niggahita_variants` (ṃ→ṁ); drop `add_niggahitas` path;
   - fold deconstruction into entries; retire `ebook_ru_deconstructor_entry.jinja`;
   - `find_pages_with_web_links` → OPF `remote_pages`;
   - `make_mobi` → `kindling-cli build <content.opf> -o <mobi>` (OPF, not epub — SRCS >16 MB limit).
2. RU templates in `exporter/kindle/ru_components/templates/`: new `ebook_ru_form_entry.jinja`;
   `ebook_ru_entry.jinja` (id `e{id}`, orth `lemma_1`, `hw{id}` anchor, `aliases`, blockquote
   summary, `deconstruction`); `ebook_ru_content_opf.jinja` (`dc:type`, ncx item, `remote-resources`).
3. `ru_components/epub/OEBPS/toc.ncx` (mirror upstream).
4. Workflows: add upstream's "Install kindling" step (see upstream `draft_release.yml`) to the
   3 RU release workflows; `RuPaths.kindling_path`; remove `RuPaths.kindlegen_path`.
5. Remove `exporter/kindle/kindlegen` from registry `unique_paths` and `git rm` it.
6. Open question: Russian summary is built outside `KindleData` — adapt `KindleData` or extend
   `render_ebook_entry_ru` (strict-parity rule: emulate upstream).

## Evidence

- Detailed hunk analysis: `kamma/threads/20261105_upstream_sync/stage2a_findings/kindle.md`.
- Upstream diff: `git diff be49bffe2c2c c54f942ee3f6 -- exporter/kindle/`.

## Verification needed

- Kindle device / Kindle Previewer manual test (homonym reachability, Russian summaries, RPD letters).
- kindling validation clean (OPF_014 etc.).

## Next session

- **Model:** ADVANCED (Opus)
- **Precondition:** upstream sync `20261105_upstream_sync` finalized.
- **Start prompt:** `/kamma:1-plan` — plan the RU Kindle #217 port from
  `kamma/threads/20261105_kindle_ru_217_port/handoff.md`.

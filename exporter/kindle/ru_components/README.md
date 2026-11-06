# exporter/kindle/ru_components

components for russian exporter related to creating EPUB and MOBI versions of DPD.

Built by `exporter/kindle/kindle_exporter_ru.py`, the Russian shadow of upstream's
`exporter/kindle/kindle_exporter.py` (upstream issue #217 port).

## Entry keying

A Kindle index term resolves to a single entry, so entries are keyed so that every
form reaches every sense it has:

- one full entry per headword, labelled with `lemma_1` (`ebook_ru_entry.jinja`);
  forms only that headword owns are `idx:iform` aliases of it;
- a form shared by several headwords, or that has a deconstruction, gets its own
  `f{n}` form entry listing every sense with a link (`ebook_ru_form_entry.jinja`);
- where a form entry and a headword want the same label, the headword is folded into
  the form entry.

`KindleDataRu` (in `kindle_exporter_ru.py`) is the Russian body of a headword: summary,
grammar table and examples, layered on upstream's `KindleData`. The RPD (Russian to
Pāḷi) letters and the abbreviations page are Russian-only additions.

## Building the MOBI

`make_mobi` runs `kindling-cli build <content.opf> -o exporter/share/ru-dpd-kindle.mobi`.
It raises if the binary is missing/not executable or kindling exits non-zero.

kindling is not committed (gitignored). CI downloads the pinned release before the
export step. For a local build download the matching asset from
`https://github.com/ciscoriordan/kindling/releases/tag/v0.45.6`:

```sh
curl -sSfL -o exporter/kindle/kindling-cli \
  https://github.com/ciscoriordan/kindling/releases/download/v0.45.6/kindling-cli-mac-apple-silicon
chmod +x exporter/kindle/kindling-cli
```

(use `kindling-cli-mac-intel` on an Intel Mac), then
`uv run python exporter/kindle/kindle_exporter_ru.py` (requires `make_ebook = yes` in
`config.ini`).

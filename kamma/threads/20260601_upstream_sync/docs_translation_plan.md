# Docs Translation Plan — Upstream Sync 2026-06-01

> Stage 4.A output (ADVANCED). Execute in Stage 4.B (FAST), file-by-file.
> Source range: `44a8a00` → `0ea58833` (from `prep_manifest.json`).
> Authoritative scope source: `docs_parity_report.md` (generated from the manifest range).

---

## Scope Summary

The parity script reports **3 actionable files**:

| File | State | Action |
|---|---|---|
| `docs_rus/install/anki.md` | MISSING | Full translation (create) |
| `docs_rus/abbreviations.md` | STALE | Targeted update (1 table row) |
| `docs_rus/install/chromebook.md` | STALE | Full rewrite (short file) |

Plus one nav update:

| File | Action |
|---|---|
| `mkdocs_ru.yaml` | Add `Anki` nav entry (only after `anki.md` exists) |

### Out of scope (no action) — IMPORTANT correction to handoff

The handoff's "Docs scope" listed `changelog.md` and `newsletters.md` as needing
update. The authoritative `check_docs_parity.py` classifies **both** as
`NO_TRANSLATE` (HTML-redirect mirrors). They are **skipped** — no translation, no
redirect edit. Do not touch them. This supersedes the handoff note.

Other handoff "skips" confirmed: home.html RSS, paths_ru/paths_dps new attrs,
mkdocs custom_dir, ru_static.yml RSS — none are docs-parity items; ignore.

---

## Translation Rules (apply to every file)

1. **Keep unchanged (verbatim):**
   - Pāḷi terms and diacritics (`Pāḷi`, `niṭṭhā`, etc.).
   - Product / proper names: `DPD`, `Digital Pāḷi Dictionary`, `Anki`, `AnkiDroid`,
     `AnkiMobile`, `GoldenDict`, `GoldenDict NG`, `MDict`, `Chrome`, `Firefox`,
     `GitHub`, `Play Store`, `Chromebook`.
   - All URLs and the `{target="_blank"}` attribute.
   - Relative markdown link targets (e.g. `browser_extension.md`) — translate only
     the **link text**, never the path.
   - Code blocks verbatim — the entire `:root { ... }` CSS block and all `hsl(...)`
     values stay exactly as in the source.
   - HTML comments (`<!-- ... -->`) and image-path comment placeholders verbatim.
   - Image paths (`../pics/...`) unchanged; translate alt text only.
2. **Translate:** heading text, body prose, list items, link text, alt text.
3. Match the tone/register of existing `docs_rus/install/*.md` (informal "вы").
4. Keep the H1 title style already present in the existing RU file when updating.

---

## Terminology Glossary (EN → RU)

Extracted from `docs_rus/install/browser_extension.md`, `dpd_app.md`, `index.md`,
`abbreviations.md`.

| EN | RU |
|---|---|
| Digital Pāḷi Dictionary / DPD | Digital Pāḷi Dictionary / DPD *(не переводить)* |
| Anki / AnkiDroid / AnkiMobile | *(не переводить)* |
| flashcard app | приложение для карточек |
| vocabulary deck | колода словарных карточек |
| deck | колода |
| card | карточка |
| desktop | десктоп |
| the releases page on GitHub | страница релизов на GitHub |
| Download | Скачайте |
| Double-click | Дважды щёлкните |
| imports the deck | импортирует колоду |
| ready to study | готова к изучению |
| Updating | Обновление |
| update (verb) | обновить |
| recognise the existing deck | распознает существующую колоду |
| Theme | Тема |
| colours and fonts | цвета и шрифты |
| card styling (CSS) | стилизация карточек (CSS) |
| colour variables | цветовые переменные |
| settings | настройки |
| save | сохранить |
| browser extension | расширение для браузера |
| Pāḷi word | палийское слово |
| to look it up | чтобы найти его |
| standalone dictionary app | отдельное приложение-словарь |
| following the relevant instructions | следуя соответствующим инструкциям |

### Anki UI labels (translate to these exact RU forms for consistency)

| EN UI label | RU |
|---|---|
| **Browse** | **Обзор** |
| card browser | обозреватель карточек |
| **Cards…** | **Карточки…** |
| **Styling** (tab/section) | **Стилизация** |
| **Card Browser** | **Обозреватель карточек** |
| **Edit note** | **Изменить заметку** |
| **⋮** menu | меню **⋮** |
| **back arrow** | **стрелка назад** |

---

## Per-File Tasks

### TASK 1 — CREATE `docs_rus/install/anki.md` (full translation)

- **Source:** `docs/install/anki.md` (60 lines)
- **Target:** `docs_rus/install/anki.md` (new file)
- **Type:** Full translation.
- **Instructions:**
  - Translate all headings and prose per glossary + rules.
  - Keep the `:root { ... }` CSS code block **exactly verbatim** (lines 26–33 of
    source) — do not translate CSS keywords, comments, or `hsl()` values.
  - Keep the two `<!-- ... -->` HTML comment lines (placeholder screenshot) verbatim.
  - Keep all URLs and `{target="_blank"}` verbatim.
  - Section headers to produce (in order): `# DPD для Anki`, `## Установка`,
    `## Обновление`, `## Тема`, `### Anki Desktop` (keep "Anki Desktop" as-is),
    `### AnkiDroid` (keep as-is).
  - Numbered steps `(1) (2) ...` keep the same numbering format.

### TASK 2 — UPDATE `docs_rus/abbreviations.md` (1 new table row)

- **Source diff:** `docs/abbreviations.md` added one row between `DNa` and `DNt`:
  `|DNnt|Dīgha Nikāya Nava-ṭīkā, Sādhuvilāsinī|Newer sub-commentary on the Sīlakkhandhavagga of the Dīgha Nikāya; lit. charming and beautiful|`
- **Target:** `docs_rus/abbreviations.md`
- **Type:** Targeted insert. **One line only. Do not touch any other line.**
- **Anchor:** between existing line `|DNa|Дигха Никая Комментарий|` and the next line
  `|DNt|Дигха Никая Подкомментарий|`.
- **Exact line to insert** (the RU table is 2-column `Сокращение|Значение`; follow the
  existing short-name pattern — DNa=Комментарий, DNt=Подкомментарий → DNnt = new
  sub-commentary = Новый подкомментарий):
  ```
  |DNnt|Дигха Никая Новый подкомментарий|
  ```
- **Result (the three rows, in order):**
  ```
  |DNa|Дигха Никая Комментарий|
  |DNnt|Дигха Никая Новый подкомментарий|
  |DNt|Дигха Никая Подкомментарий|
  ```

### TASK 3 — UPDATE `docs_rus/install/chromebook.md` (full body rewrite)

- **Source:** `docs/install/chromebook.md` (now 7 lines — old single-paragraph body
  replaced with 3 paragraphs).
- **Target:** `docs_rus/install/chromebook.md`
- **Type:** Replace the entire body below the H1. Keep H1 `# Установка на Chromebook`.
- **Exact target file content** (write the file to exactly this):
  ```markdown
  # Установка на Chromebook

  Если вы пользуетесь Chromebook, лучшим помощником станет [расширение DPD для браузера](browser_extension.md). Оно работает прямо внутри Chrome, поэтому ничего больше устанавливать не нужно — просто добавьте его и дважды щёлкните по любому палийскому слову, чтобы найти его.

  Полную инструкцию смотрите на [странице расширения для браузера](browser_extension.md).

  Если вы предпочитаете отдельное приложение-словарь, вы также можете попробовать [MDict из Play Store](https://play.google.com/store/apps/details?id=cn.mdict&hl=en){target="_blank"} или Linux-версию [GoldenDict NG](https://github.com/xiaoyifang/goldendict-ng/releases/latest){target="_blank"}, следуя соответствующим инструкциям.
  ```

### TASK 4 — UPDATE `mkdocs_ru.yaml` nav (only after TASK 1 done)

- **Target:** `mkdocs_ru.yaml`
- **Anchor:** between line `    - Kobo: "install/kobo.md"` and
  `    - ChromeBook: "install/chromebook.md"` (matches upstream `mkdocs.yaml` order,
  which places Anki between Kobo and ChromeBook).
- **Exact line to insert** (4-space indent, same as siblings):
  ```
    - Anki: "install/anki.md"
  ```
- Do not reorder or change any other nav entry.

---

## Verification (Stage 4.B, after all tasks)

- `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py kamma/threads/20260601_upstream_sync --strict`
  → must report 0 missing, 0 stale, exit 0.
- `mkdocs_ru.yaml` still valid YAML (build or `mkdocs build --config-file mkdocs_ru.yaml`
  if convenient; otherwise visual check).
- Commit message (FAST prepares, user runs):
  `#docs: translate/update docs_rus/ for sync 44a8a00..0ea58833`

---

## Execution Order (Stage 4.B)

1. TASK 1 (create anki.md — full translation).
2. TASK 2 (abbreviations.md row).
3. TASK 3 (chromebook.md rewrite).
4. TASK 4 (mkdocs_ru.yaml nav — only after TASK 1).
5. Run `--strict` parity check; record result in `handoff.md`.

Split after every 5 translation files (only 1 full-translation file here, so a single
batch is fine).

# Stage 4.B — Docs Translation Execution Plan

Sync range: `9af5f7ee..44a8a005`

## What is already done (do NOT redo)

- `docs_rus/changelog.md` — symlink to `../docs/changelog.md` already created. Skip it entirely.
- `kamma/upstream_sync/scripts/check_docs_parity.py` — already bugfixed and updated.
- `kamma/upstream_sync/guide.md` — already updated with symlink policy.

## Your tasks (in order)

1. Translate `docs/install/dpd_app.md` → create `docs_rus/install/dpd_app.md`
2. Translate `docs/newsletters.md` → create `docs_rus/newsletters.md`
3. Update `mkdocs_ru.yaml` nav (3 insertions)
4. Prepare commit

---

## Terminology Glossary (EN → RU)

Apply consistently. When in doubt, preserve the English term.

| English | Russian |
|---|---|
| Digital Pāḷi Dictionary | Цифровой Пали Словарь |
| DPD (abbreviated) | DPD |
| headword | заглавное слово |
| inflection / inflected form | флексии / словоформа |
| root | корень |
| root family | корневые семейства |
| compound | сложное слово |
| deconstructor | деконструктор |
| lookup | поиск / таблица поиска |
| feedback | отзыв / обратная связь |
| update | обновление |
| download | скачать / загрузить |
| install | установить / установка |
| release | версия / выпуск |
| webapp / web app | веб-приложение |
| browser extension | расширение для браузера |
| beta testing | бета-тестирование |
| beta tester | бета-тестировщик |
| proofreader | вычитывающий / корректор |
| correction | исправление |
| addition | дополнение |
| sutta | сутта |
| vagga | вагга |
| Nikāya | Никая |
| Tipiṭaka | Типитака |
| Vinaya | Виная |
| Dīgha Nikāya | Дигха Никая |
| Majjhima Nikāya | Маджхима Никая |
| Saṃyutta Nikāya | Самьютта Никая |
| Aṅguttara Nikāya | Ангуттара Никая |
| Khuddaka Nikāya | Кхуддака Никая |

**Never translate these — keep exactly as-is:**
- All Pāḷi words with diacritics: *mettā*, *dhamma*, *bhikkhu*, *vagga*, *sutta*, *saṃyutta*, proper Pāḷi names, etc.
- All URLs (http/https links) — never modify a URL
- All image paths: `pics/newsletters/abc123.jpg`, `../pics/...`, etc.
- All Markdown image tags in full: `![image.png](pics/newsletters/hash.jpg)` — keep alt text and path unchanged
- All code blocks (text inside triple backticks)
- Product/app/OS names: GoldenDict, MDict, DictTango, Kindle, Kobo, GitHub, Google, Android, APK, iOS, macOS, Windows, Mac, Linux, Chrome, Firefox, Safari, Play Store, Flet
- Person names: Bodhirasa, Bhikkhu Bodhi, Ven. Mettānanda, Jordi, Ben
- Organization names: SuttaCentral, Bhashini, DhammaBytes, PaliPractice
- The ⚠ warning symbol and all emoji — keep unchanged

**Translation rules for Markdown structure:**
- Headings: translate text, keep `#` count and spacing
- Bold `**text**`: translate text inside, keep `**` markers
- Links `[link text](url)`: translate link text if it's English prose; keep URL unchanged; keep product names/Pāḷi terms in link text unchanged
- Lists: translate bullet content, keep `*` or `-` and indentation
- YAML front matter (lines between `---` at top of file): keep unchanged
- Horizontal rules `---`: keep unchanged

---

## Task 1: Translate `docs/install/dpd_app.md`

**Read**: `docs/install/dpd_app.md` (114 lines — read all at once, offset=0 limit=120)
**Write**: `docs_rus/install/dpd_app.md` (new file — use Write tool)

### Exact heading translations for this file

| English heading | Russian heading |
|---|---|
| `# DPD App — Beta Testing` | `# DPD Приложение — Бета-тестирование` |
| `## Download The Latest Release` | `## Скачать последнюю версию` |
| `## Install On Android` | `## Установка на Android` |
| `## How To Look Up Words From Other Apps` | `## Как искать слова из других приложений` |
| `## How To Look Up Words Within The App` | `## Как искать слова внутри приложения` |
| `## How Updates Work` | `## Как работают обновления` |
| `## How To Send Feedback` | `## Как отправить отзыв` |
| `## Quick Troubleshooting` | `## Быстрое устранение неполадок` |
| `### My browser warns the file might be harmful` | `### Браузер предупреждает, что файл может быть вредоносным` |
| `### The APK will not install` | `### APK-файл не устанавливается` |
| `### The app does not update immediately` | `### Приложение не обновляется сразу` |
| `### I found a dictionary mistake` | `### Я нашёл ошибку в словаре` |

### Key phrase translations for this file

| English phrase | Russian phrase |
|---|---|
| `**Having a problem? Report it here**` | `**Возникла проблема? Сообщите нам**` |
| `On the latest release page, download the `.apk` file listed under **Assets**.` | `На странице последней версии скачайте файл `.apk`, указанный в разделе **Assets**.` |
| `Your browser may warn that the file might be harmful.` | `Браузер может предупредить, что файл может быть вредоносным.` |
| `This is a standard warning shown for any APK downloaded outside the Play Store` | `Это стандартное предупреждение, которое появляется для любого APK, скачанного не из Play Store` |
| `not a sign that the file is actually dangerous` | `не признак того, что файл действительно опасен` |
| `You can safely proceed with the download.` | `Вы можете безопасно продолжить загрузку.` |
| `Allow from this source` | `Разрешить из этого источника` |
| `Install unknown apps` | `Установка из неизвестных источников` |
| `Double-click on any word within the app to search for it.` | `Дважды щёлкните любое слово в приложении для его поиска.` |
| `Type directly into the search bar using Unicode or Velthuis typing.` | `Введите слово непосредственно в строку поиска, используя Unicode или транслитерацию Velthuis.` |
| `App update: automatic check/download, then Android asks you to approve install.` | `Обновление приложения: автоматическая проверка/загрузка, затем Android просит подтвердить установку.` |
| `Database update: automatic background download and apply.` | `Обновление базы данных: автоматическая фоновая загрузка и применение.` |
| `Please tap this link to report anything you notice` | `Пожалуйста, нажмите эту ссылку, чтобы сообщить о любых замечаниях` |
| `The form is pre-filled with your device and app version` | `Форма предварительно заполнена информацией о вашем устройстве и версии приложения` |
| `Every report helps, no matter how small.` | `Любой отчёт полезен, каким бы незначительным он ни был.` |
| `Click **Keep** or **Download anyway** to proceed.` | `Нажмите **Сохранить** или **Загрузить всё равно**, чтобы продолжить.` |
| `Make sure the device has internet access.` | `Убедитесь, что устройство подключено к интернету.` |
| `Check whether updates are limited to Wi-Fi in the app settings.` | `Проверьте, не ограничены ли обновления только Wi-Fi в настройках приложения.` |
| `You can also use the app's \`Update Now\` button in Settings.` | `Вы также можете использовать кнопку \`Обновить сейчас\` в настройках приложения.` |
| `Open the entry, tap the \`feedback\` button at the bottom, and choose \`Correct a mistake\`.` | `Откройте запись, нажмите кнопку \`обратная связь\` внизу и выберите \`Исправить ошибку\`.` |

---

## Task 2: `docs/newsletters.md` — symlink (NO translation)

**Decision**: newsletters.md is too large and data-heavy for translation. Use symlink pattern same as changelog.md.
**Action**: `ln -s ../docs/newsletters.md docs_rus/newsletters.md`
**Also**: Add `"newsletters.md"` to `NO_TRANSLATE` in `check_docs_parity.py`
**Status**: DONE

### Reading strategy

Read `docs/newsletters.md` in chunks of 150 lines:
- Chunk 1: `offset=0, limit=150`
- Chunk 2: `offset=150, limit=150`
- Chunk 3: `offset=300, limit=150`
- Continue until the read returns fewer lines than requested (end of file).

**Writing strategy**: Translate each chunk as you read it. Use Write tool for the first chunk's translated content, then Edit tool to append each subsequent translated chunk.

### Structure of each newsletter entry

Each entry follows this pattern (translate as shown):

```
## YYYY-MM-DD                          ← keep date unchanged
**Digital Pāḷi Dictionary update (Month Year)**    ← translate as shown below

Dear Venerable monastics, professors, and Pāḷi enthusiasts,   ← use fixed RU phrase

[body paragraphs — translate]

**- Latest release**                   ← translate as: **- Последняя версия**

[download links list — keep ALL links and link text EXACTLY as-is]

Please share this information with those who might be interested.   ← use fixed RU phrase

Wishing you well from [place],         ← use fixed RU phrase
/or/
With much *mettā* from [place],        ← use fixed RU phrase
/or/
With *mettā* from [place],             ← use fixed RU phrase

Bodhirasa                              ← keep name unchanged

---                                    ← keep unchanged
```

### Fixed phrase translations for newsletters

| English | Russian |
|---|---|
| `# DPD Newsletters` | `# Новостные рассылки DPD` |
| `**Digital Pāḷi Dictionary update (Month Year)**` | `**Обновление Цифрового Пали Словаря (Месяц Год)**` |
| `Dear Venerable monastics, professors, and Pāḷi enthusiasts,` | `Уважаемые монашествующие, профессора и любители Пали,` |
| `**- Latest release**` | `**- Последняя версия**` |
| `Download the latest version of DPD for your device using these links:` | `Скачайте последнюю версию DPD для вашего устройства по этим ссылкам:` |
| `**- Corrections and Additions**` | `**- Исправления и дополнения**` |
| `As always, thank you for the abundant [X] over the past month.` | `Как всегда, благодарим вас за многочисленные [X] в течение прошлого месяца.` |
| `Please share this information with those who might be interested.` | `Пожалуйста, поделитесь этой информацией с теми, кому это может быть интересно.` |
| `Wishing you well from [place],` | `С наилучшими пожеланиями из [place],` |
| `With much *mettā* from [place],` | `С метта из [place],` |
| `With *mettā* from [place],` | `С метта из [place],` |

### Month names in RU

| English | Russian |
|---|---|
| January | января |
| February | февраля |
| March | марта |
| April | апреля |
| May | мая |
| June | июня |
| July | июля |
| August | августа |
| September | сентября |
| October | октября |
| November | ноября |
| December | декабря |

### Section heading translations for newsletters

| English | Russian |
|---|---|
| `**- Saṃyutta Nikāya**` | `**- Самьютта Никая**` |
| `**- Sutta Names and Codes**` | `**- Названия и коды сутт**` |
| `**- Theragāthā and Therīgāthā codes**` | `**- Коды Тхерагатхи и Тхеригатхи**` |
| `**- DPD Android app — beta testing**` | `**- Приложение DPD для Android — бета-тестирование**` |
| `**- DPD Android app — looking for beta testers**` | `**- Приложение DPD для Android — поиск бета-тестировщиков**` |
| `**- Other dictionaries for download**` | `**- Другие словари для скачивания**` |
| `**- Saṃyutta Nikāya progress**` | `**- Прогресс по Самьютта Никае**` |
| `**- Small quality-of-life improvements**` | `**- Небольшие улучшения удобства использования**` |
| `**- DPD browser extension**` | `**- Расширение DPD для браузера**` |
| `**- Apple Dictionary**` | `**- Словарь для Apple**` |
| `**- Saṃyutta Nikāya 1-3 complete**` | `**- Самьютта Никая 1-3 завершена**` |
| `**- Searching without diacritics**` | `**- Поиск без диакритических знаков**` |
| `**- English-to-Pāḷi Dictionary on Kindle**` | `**- Словарь с английского на Пали для Kindle**` |
| `**- Looking for Beta Testers**` | `**- Поиск бета-тестировщиков**` |
| `**- Pāli Practice App**` | `**- Приложение для практики Пали**` |
| `**- Sutta Information**` | `**- Информация о суттах**` |
| `**- Plain text version of DPD**` | `**- Версия DPD в виде обычного текста**` |
| `**- Majjhima Nikāya**` | `**- Маджхима Никая**` |
| `**- Verbal Forms**` | `**- Глагольные формы**` |
| `**- Dictionary of Bold Definitions**` | `**- Словарь выделенных определений**` |
| `**- Improvements to the Website**` | `**- Улучшения веб-сайта**` |
| `**- Audio Pronunciation**` | `**- Аудиопроизношение**` |
| `**- Buddha Jayanti Tipiṭaka**` | `**- Типитака Будда Джаянти**` |
| `**- Searchable Tipiṭaka Translations**` | `**- Поиск по переводам Типитаки**` |

### Download links section — keep ALL as-is

The "Latest release" section contains a list of download links. Keep the ENTIRE block unchanged — both link text and URLs:

```markdown
* [DPD online](https://www.dpdict.net/)
* [DPD for GoldenDict](...)
...
```

Do not translate link text in download lists.

---

## Task 3: Update `mkdocs_ru.yaml`

Read `mkdocs_ru.yaml` before making edits (it has not been read in this session).

### Change 1: Add DPD App to install nav

Find (around line 18):
```yaml
    - "install/index.md"
    - Windows: "install/win.md"
```

Replace with:
```yaml
    - "install/index.md"
    - DPD Приложение: "install/dpd_app.md"
    - Windows: "install/win.md"
```

### Change 2: Add Changelog and Newsletters after Контакты

Find (around line 67-68):
```yaml
  - Благодарности: "thanks.md"
  - Контакты: "contact.md"
```

Replace with:
```yaml
  - Благодарности: "thanks.md"
  - Контакты: "contact.md"
  - Changelog: "changelog.md"
  - Новостные рассылки: "newsletters.md"
```

---

## Task 4: Prepare commit

Run ruff check on the two new .md files — they are Markdown, ruff does not check them, so no ruff step needed.

Stage these files:
```
git add docs_rus/install/dpd_app.md
git add docs_rus/newsletters.md
git add docs_rus/changelog.md
git add mkdocs_ru.yaml
git add kamma/upstream_sync/scripts/check_docs_parity.py
git add kamma/upstream_sync/guide.md
git add kamma/threads/20260502_upstream_sync/docs_parity_report.md
git add kamma/threads/20260502_upstream_sync/docs_translation_plan.md
git add kamma/threads/20260502_upstream_sync/handoff.md
```

Commit message to present to user:
```
#docs: translate missing docs_rus/ pages for sync 9af5f7ee..44a8a005
```

# Docs Translation Parity Report

Sync range: `44a8a00556cce9bd3874a94efb5dfaceaaf20a66` → `0ea5883380f56b682cf8574043afb8e66cca3260`

---

## Missing Translations

None.

## Stale Translations

Files in `docs/` changed since baseline SHA — corresponding Russian translation needs review:

- `docs/abbreviations.md` → review/update `docs_rus/abbreviations.md`
- `docs/install/anki.md` → review/update `docs_rus/install/anki.md`
- `docs/install/chromebook.md` → review/update `docs_rus/install/chromebook.md`

## Stale Translation Diff Evidence

### `docs/abbreviations.md`

```diff
diff --git a/docs/abbreviations.md b/docs/abbreviations.md
index e5101c94..a0b650f8 100644
--- a/docs/abbreviations.md
+++ b/docs/abbreviations.md
@@ -151,6 +151,7 @@ There are two types of abbreviations: Grammatical and Textual.
 |DhSṭ|Dhammasaṅgaṇī mūlaṭīkā||
 |DN|Dīgha Nikāya|Book 1 of the Sutta Piṭaka; Collection of Long Discourses; lit. long collection|
 |DNa|Dīgha Nikāya Aṭṭhakathā, Sumaṅgalavilāsinī|Commentary on the Dīgha Nikāya compiled by Ven. Buddhaghosa; lit. very auspicious and charming|
+|DNnt|Dīgha Nikāya Nava-ṭīkā, Sādhuvilāsinī|Newer sub-commentary on the Sīlakkhandhavagga of the Dīgha Nikāya; lit. charming and beautiful|
 |DNt|Dīgha Nikāya Ṭīkā, Sādhuvilāsinī||
 |EV|Elder's Verses by K.R.Norman||
 |ITI|Itivuttaka|Book 4 of the Khuddaka Nikāya; Quotations; lit. thus said|
```

### `docs/install/anki.md`

```diff
diff --git a/docs/install/anki.md b/docs/install/anki.md
new file mode 100644
index 00000000..cb7e374e
--- /dev/null
+++ b/docs/install/anki.md
@@ -0,0 +1,59 @@
+# DPD for Anki
+
+A DPD vocabulary deck is available for [Anki](https://apps.ankiweb.net){target="_blank"}, the popular flashcard app. It works on desktop, AnkiDroid and AnkiMobile.
+
+## Install
+
+(1) Download the latest version of **dpd-anki.apkg** from **[the releases page on GitHub](https://github.com/digitalpalidictionary/dpd-db/releases/latest){target="_blank"}**.
+
+(2) Double-click **dpd-anki.apkg**. Anki opens and imports the deck.
+
+That's it. The deck appears in your deck list, ready to study.
+
+## Updating
+
+When a new version is released, download and open the latest **dpd-anki.apkg** again. Anki will recognise the existing deck and ask if you want to update it. Choose to update.
+
+<!-- placeholder: screenshot of the Anki update prompt -->
+<!-- ![update prompt](../pics/anki/anki_update.png) -->
+
+## Theme
+
+You can change the colours and fonts of the cards by editing the card styling (CSS). The theme is controlled by the `:root` colour variables at the top of the styling.
+
+These are the settings used to make the default DPD theme:
+
+```css
+:root {
+  --label: hsl(205, 79%, 48%);
+  --hl:    hsl(198, 100%, 50%);
+  --soft:  hsl(198, 100%, 95%);
+  --bg:    hsl(198, 100%, 5%);
+}
+```
+
+Change the `hsl(...)` values to set your own colours, then save.
+
+### Anki Desktop
+
+(1) Click **Browse** to open the card browser.
+
+(2) Select any DPD card.
+
+(3) Click **Cards…**.
+
+(4) Open the **Styling** tab and edit the CSS.
+
+(5) Close the window to save.
+
+### AnkiDroid
+
+(1) Open the **Card Browser** and tap a DPD card.
+
+(2) Tap the **⋮** menu and choose **Edit note**.
+
+(3) Tap the **⋮** menu again and choose **Cards…**.
+
+(4) Open the **Styling** section and edit the CSS.
+
+(5) Tap the **back arrow** to save.
```

### `docs/install/chromebook.md`

```diff
diff --git a/docs/install/chromebook.md b/docs/install/chromebook.md
index 31397a66..5d1b30f2 100644
--- a/docs/install/chromebook.md
+++ b/docs/install/chromebook.md
@@ -1,3 +1,7 @@
 # Install on Chromebook
 
-Chromebook is not currently supported, but you can try your luck with installing [MDict from the Play Store](https://play.google.com/store/apps/details?id=cn.mdict&hl=en){target="_blank"} or installing the Linux version of [GoldenDict NG](https://github.com/xiaoyifang/goldendict-ng/releases/latest){target="_blank"} and following the relevant instructions.
+If you're on a Chromebook, the [DPD browser extension](browser_extension.md) is your friend. It runs right inside Chrome, so there's nothing else to install — just add it and double-click any Pāḷi word to look it up.
+
+See the [browser extension page](browser_extension.md) for full instructions.
+
+If you'd rather use a standalone dictionary app, you can also try your luck with [MDict from the Play Store](https://play.google.com/store/apps/details?id=cn.mdict&hl=en){target="_blank"} or the Linux version of [GoldenDict NG](https://github.com/xiaoyifang/goldendict-ng/releases/latest){target="_blank"}, following the relevant instructions.
```


## No-translate Files (HTML Redirect)

Files mirrored via HTML redirect — no translation needed:

- `docs_rus/changelog.md` (redirect)
- `docs_rus/newsletters.md` (redirect)

## Unique Local Files

Files in `docs_rus/` with no `docs/` counterpart (no action needed):

- `docs_rus/contributing/rus_collaboration.md` ← expected
- `docs_rus/dpd_rus.md` ← expected
- `docs_rus/technical/dpd_headwords_table_ru.md` ← expected

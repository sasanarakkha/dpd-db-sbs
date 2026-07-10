# Docs Translation Parity Report

Sync range: `518672a65fa3ea7c36c4c754dc5276bb41f92da7` → `be49bffe2c2c85971784337d4e09915ad1f42800`

---

## Missing Translations

None.

## Stale Translations

Files in `docs/` changed since baseline SHA — corresponding Russian translation needs review:

- `docs/technical/local_server_setup.md` → review/update `docs_rus/technical/local_server_setup.md`
- `docs/technical/quick_start.md` → review/update `docs_rus/technical/quick_start.md`
- `docs/technical/use_db.md` → review/update `docs_rus/technical/use_db.md`

## Stale Translation Diff Evidence

### `docs/technical/local_server_setup.md`

```diff
diff --git a/docs/technical/local_server_setup.md b/docs/technical/local_server_setup.md
index d35a072d3..8d8ca38c2 100644
--- a/docs/technical/local_server_setup.md
+++ b/docs/technical/local_server_setup.md
@@ -37,7 +37,7 @@ You need to download three main database files: the primary DPD database, the au
 Download and extract the latest primary database:
 
 ```bash
-wget -qO- https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd.db.tar.bz2 | tar -xj
+wget -qO- https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd.db.tar.xz | tar -xJ
 ```
 
 #### 3.2. Audio Database
```

### `docs/technical/quick_start.md`

```diff
diff --git a/docs/technical/quick_start.md b/docs/technical/quick_start.md
index d764c9737..8355c9248 100644
--- a/docs/technical/quick_start.md
+++ b/docs/technical/quick_start.md
@@ -11,7 +11,7 @@ Welcome to the Digital Pāḷi Dictionary (DPD) developer guide. This page will
     git clone --depth 1 --recurse-submodules https://github.com/digitalpalidictionary/dpd-db.git
     cd dpd-db
     ```
-2. **Database**: Download the latest `dpd.db.tar.bz2` from the [dpd-db releases page](https://github.com/digitalpalidictionary/dpd-db/releases){target="_blank"} and place it in the root folder. Then extract it with `tar -xf dpd.db.tar.bz2`
+2. **Database**: Download the latest `dpd.db.tar.xz` from the [dpd-db releases page](https://github.com/digitalpalidictionary/dpd-db/releases){target="_blank"} and place it in the root folder. Then extract it with `tar -xf dpd.db.tar.xz`
 
 3. **uv**: This project uses [astral uv](https://github.com/astral-sh/uv) for dependency management and Python version control. Install it if you haven't already:
     ```bash
```

### `docs/technical/use_db.md`

```diff
diff --git a/docs/technical/use_db.md b/docs/technical/use_db.md
index cb67e2768..23c4c6779 100644
--- a/docs/technical/use_db.md
+++ b/docs/technical/use_db.md
@@ -9,7 +9,7 @@ git clone --depth 1 https://github.com/digitalpalidictionary/dpd-db.git
 cd dpd-db
 ```
 
-Download **dpd.db.tar.bz2** from [the dpd-db release page](https://github.com/digitalpalidictionary/dpd-db/releases){target="_blank"}, 
+Download **dpd.db.tar.xz** from [the dpd-db release page](https://github.com/digitalpalidictionary/dpd-db/releases){target="_blank"}, 
 
 Unzip and place the db in the root of the project folder.
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
- `docs_rus/technical/generate_pli2ru_json.md`

## Unexpected Local Files

These `docs_rus/` files have no `docs/` counterpart and are not listed as expected local-only files:

- `docs_rus/technical/generate_pli2ru_json.md`

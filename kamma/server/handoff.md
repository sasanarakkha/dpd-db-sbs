# Server Operations — Handoff / Runbook

**Purpose:** single place to resume work on the remote dictionary server. Read this
first; it carries the state, the procedure, and the traps.
**Last updated:** 2026-11-06
**Scope:** the SBS deployment only (`~/dpd-db-sbs`). The plain `~/dpd-db` deployment
on the same server is out of scope — never touch it.

---

## 1. What lives where

| Item | Location | Notes |
|---|---|---|
| Server | `django@85.215.66.115` | home is `/home/django` |
| SBS repo | `~/dpd-db-sbs` | fork checkout; **this is the one we work on** |
| Deployed update script | `~/update-dpd-sbs.sh` | copy of `scripts/server_dpdict/update-dpd-sbs.sh`, `chmod +x`, run from `~` |
| Plain repo | `~/dpd-db` | separate non-SBS deployment, port 8080 — **do not touch, do not kill** |
| SBS webapp | port `8081`, `exporter.webapp.main_ru:app` | started by the script via `nohup uv run uvicorn ...` |
| Plain webapp | port `8080`, `exporter.webapp.main:app` | started via `uv run` in `~/dpd-db` |
| SBS app logs | `~/dpd-db-sbs/logs/<YYYY-MM-DD_HH-MM-SS>.uvicorn.log` | one file per restart |
| uv cache | `~/.cache/uv` | shared by both repos — source of the trap in §3 |

The repo copy is the source of truth. The home copy is a deployment artifact and
will drift the moment you edit one and not the other.

---

## 2. Normal update procedure

1. **Deploy the script** (only when the repo copy changed):

   ```bash
   # from the local machine
   scp scripts/server_dpdict/update-dpd-sbs.sh django@85.215.66.115:~/update-dpd-sbs.sh
   # then on the server
   chmod +x ~/update-dpd-sbs.sh
   ```

2. **Run it from the home directory** — the script does `cd dpd-db-sbs`
   (relative), so any other CWD fails at step 1:

   ```bash
   cd ~ && ./update-dpd-sbs.sh
   ```

3. **Verify:** watch the log it prints at the end, then

   ```bash
   ps -eo pid,etimes,cmd | grep uvicorn | grep -v grep
   tail -f ~/dpd-db-sbs/logs/<latest>.uvicorn.log
   ```

### What the script does

| Step | Action | Safe to re-run? |
|---|---|---|
| 1 | `cd dpd-db-sbs`, recreate `update_tmp` with an `EXIT` trap | yes |
| 2 | `git pull --no-recurse-submodules`; on failure, wipe `resources/dpd_submodules` + `resources/tipitaka_translation_db`, `submodule sync`, `submodule update` | yes |
| 3 | `uv sync` | yes |
| 4 | `uv run python audio/db_release_download.py` (translation db download is commented out) | yes, re-downloads |
| 5 | download `dpd.db.tar.xz` from the latest GitHub release → sanity-check headword count → `tools/prepare_webapp_lookup.py` → `mv` into place → regenerate search index | yes |
| 6 | `pkill -f "uvicorn exporter.webapp.main_ru:app"`, `sleep 2` | yes |
| 7 | `nohup uv run uvicorn ... --port 8081 &`, log to `logs/` | yes |

`set -euo pipefail` is on, so any failure aborts. Nothing before step 5 mutates
`dpd.db`; a run that dies before then leaves the live database intact.

---

## 3. Known issue: `uv cache prune` deadlock (fixed 2026-11-06)

**Symptom:** the script hangs at step 3 with
`Cache is currently in-use, waiting for other uv processes to finish`.

**Cause:** `uv` takes an exclusive lock on the shared `~/.cache/uv`, and `uv run`
holds it for the *lifetime of its child process*. The plain `~/dpd-db` webapp is
started with `uv run uvicorn ...` and runs for weeks, so the lock is never
released. Because the SBS script pruned the cache at step 3 but only killed its
own webapp at step 6, a healthy deployment could deadlock the update against an
unrelated project's server.

**Fix:** the `uv cache prune` line was removed from
`scripts/server_dpdict/update-dpd-sbs.sh`. It was pure cache housekeeping with no
role in the update. Reordering it after step 6 would *not* have helped — the
blocker is the other project's process, not ours.

**Do not** "fix" this with `uv cache prune --force`: it prunes a cache that
`~/dpd-db`'s environment depends on.

**Diagnose a hang** (second SSH session):

```bash
ps -eo pid,ppid,etimes,cmd | grep -E "uv|uvicorn" | grep -v grep
```

`etimes` is seconds alive — a multi-day `uv run` is the lock holder.

**Ctrl+C is safe** at step 3: `update_tmp` is cleaned by the `trap`, `dpd.db` is
untouched, the running app keeps serving.

### Patching a deployed copy that is already stale

```bash
cp ~/update-dpd-sbs.sh ~/update-dpd-sbs.sh.bak
sed -i '/^uv cache prune$/d' ~/update-dpd-sbs.sh
diff ~/update-dpd-sbs.sh.bak ~/update-dpd-sbs.sh
bash -n ~/update-dpd-sbs.sh && echo "syntax OK"
rm ~/update-dpd-sbs.sh.bak
```

The anchored regex removes exactly that one line; `sed -i` preserves the `+x`
bit. Delete the `.bak` once one full run succeeds.

---

## 4. Gotchas

- **Never edit the script while it is running.** Bash reads the file from disk as
  it executes; rewriting it mid-run produces bizarre behaviour. `Ctrl+C` first.
- **Run from `~`.** `cd dpd-db-sbs` is relative — running it from inside
  `~/dpd-db-sbs` fails immediately.
- **`pkill -f "uvicorn exporter.webapp.main_ru:app"` is scoped by `main_ru`** and
  must stay that way; a looser pattern (`uvicorn`) would kill the plain `:8080`
  deployment too.
- **The home copy drifts.** After any `git pull` that touches the repo script,
  re-`cp` it to `~`.
- **The repo copy is tracked as `100644`** (not executable) in git. That is fine
  for the `scp` + `chmod +x` flow; only change it deliberately.
- **Legacy process:** one old SBS webapp was found started directly from
  `env/bin/uvicorn` (no `uv run` wrapper, ~15 days uptime). It holds no cache
  lock; the script kills it by pattern and replaces it with a `uv run` one.

---

## 5. Change log

| Date | Change |
|---|---|
| 2026-11-06 | Removed `uv cache prune` (deadlock against `~/dpd-db`'s `uv run`); deployed copy patched by hand on the server, repo copy edited locally. |

# baseline.md — ru_cognate

## Inspection
Dumps in `temp/ru_cognate/` (downloaded 2026-11-16). Scratch scripts `temp/ru_cognate/inspect{1-4}.py` reproduce every quote below.
Sheet: `shared_data/ru_cognate/sheet_snapshot.csv` final `wc -l` = 45 (user-edited, no header row).

**(a) Proto-Slavic key.** PSL dump `word` has NO `*` and is not accented: `bratrъ`, `novъ`, `dvьrь`, `trьje`, `mati`.
Russian `inh` templates carry the `*` and sometimes accents: `{"1":"ru","2":"sla-pro","3":"*nòvъ"}`, `*dvьrь`, `*trьje`, `*mati`.
Matching needs: strip `*`, strip accents (`nòvъ`→`novъ`). Mechanical once normalised.
BUT most PSL entries have **no etymology templates at all** (`mati`, `trьje`, `novъ` → `[]`); the PIE source exists only in
free text `etymology_text` ("Inherited from Proto-Balto-Slavic *náwas, from Proto-Indo-European *néwos."). Only `bratrъ` and
`dvьrь` have `inh ... ine-pro` templates.

**(b) PIE term, as written, per language** (id never present in these templates; `id` only appears inside Sanskrit `etymon` templates as `<id:door>`):
| word | Sanskrit/Pali side | Russian | Proto-Slavic | identical? |
|---|---|---|---|---|
| брат | Skt भ्रातृ `inh sa ine-pro *bʰréh₂tēr`; Pali `bhātar` `inh pi ine-pro *bʰréh₂tēr` | `PIE word *bʰréh₂tēr` (no `inh` template; `dercat`) | `bratrъ`: `inh sla-pro ine-pro *bʰréh₂tēr` | **yes** |
| мать | Skt मातृ / Pali `mātar`: only `inh pi sa मातृ` (no PIE on the Pali entry; PIE reached via 1 hop) | `inh ru ine-pro *méh₂tēr` | `mati`: text only, `*méh₂tēr` | yes (after hop + text parse) |
| дверь | Skt द्वार् `inh sa ine-pro *dʰwṓr`; Skt द्वार (=Pali dvāra) only `etymon ... द्वार्<id:door>` | `root ru ine-pro *dʰwer-` AND `inh ru ine-pro *dʰwṓr` | `dvьrь`: `inh sla-pro ine-pro *dʰwer-` | **NO** — `*dʰwṓr` vs `*dʰwer-` (RU has both, PSL has the root form) |
| три | Pali `ti`/`tayo`: `inh pi sa त्रि` / `त्रयस्`; (Skt tri entry not inspected for PIE) | `inh ru ine-pro *tréyes` | `trьje`: text only, `*tréyes` | yes if Skt side has `*tréyes` (not verified) |
| новый | Skt नव adj: only `iir-pro *náwas` (NO ine-pro); Skt नव num ('nine') is `*h₁néwn̥` (a different word) | no ine-pro template at all (`dercat` only; `inh sla-pro *nòvъ`) | `novъ`: text only, `*néwos` | **NO** — Sanskrit side never reaches PIE |
| будить (√budh) | Skt बुध् root: `inh sa ine-pro` with term in arg **4**: `*bʰúdʰs` (arg 3 empty) | `root ru ine-pro *bʰewdʰ-` | n/a | **NO** — `*bʰúdʰs` vs `*bʰewdʰ-` |

**(c) Sanskrit romanization vs DPD `sanskrit_root`** (accents stripped): root entries match for √budh→`budh`, √ñā→`jñā`, √gam, √han, √jan, √vac, √bhū, √sthā; √kar's DPD `sanskrit_root` is `√kṛ` → `kṛ` matches. **√dvar: DPD `√dvṛ` → `dvṛ`; no Sanskrit `dvṛ` root entry was found** (the door word is `dvār`/`dvāra`, noun). Homonymous Sanskrit entries exist (`kṛ` has two roots: `*kʷer-` and `*kreH-`; `bhū` root and noun) → ambiguity must be handled, not first-hit.

**(d) Borrowing/non-inherited template names in Russian etymologies** (lang_code ru, counts): `bor+` 6495, `bor` 1518, `lbor` 61, `ubor` 6, `obor` 2, `learned borrowing` 2, `unadapted borrowing` 1, `calque` 253, `clq` 61, `pclq` 4, `blend` 70, `onomatopoeic` 52, `onom` 7, `back-formation` 18, `translit` 14, `univ` 23. Inheritance: `inh` 5920, `inh+` 3893 (`der` 5674 is mixed).

**(e) grounding.** `tools/ai_openai_compat.py:232` accepts `grounding` but never uses it (`grep grounding` → only the signature). `AIManager.request` (`tools/ai_manager.py:211`) uses `grounding=True` only to pick `GROUNDED_MODELS` (= `deepseek / deepseek-v4-pro`; thinking disabled). **No web search happens for deepseek.** Decision: `verify` uses `grounding=True` (selects the grounded chain) and must NOT be described as "grounded"/web-verified — the verifier works from model knowledge only.

**Escalation: TRIGGERED.** Findings contradict the spec:
1. PIE terms differ between languages for the same etymon (дверь `*dʰwṓr` vs `*dʰwer-`; √budh `*bʰúdʰs` vs `*bʰewdʰ-`; Sanskrit новый never reaches PIE) → the `(term,id)` exact-key join will miss several gold pairs (дверь, новый, будить).
2. Proto-Slavic hop is not template-based for most entries (text only).
3. `grounding=True` does nothing for deepseek (no search).
4. `id` is effectively absent from `inh`/`root` templates; spec's `(term,id)` key is really `term`.
5. DPD `√dvṛ` has no Sanskrit root entry; the Pāli/Skt `dvāra` reaches PIE only through the Sanskrit `द्वार्` noun entry via an `etymon` template.

## Join run (task 4.1, 2026-11-16)
Command: `uv run python scripts/ru_cognate/ru_cognate_ledger.py --dumps temp/ru_cognate` (about 4 s). Ledger: `shared_data/ru_cognate/ledger.tsv`.
Two data-driven fixes were made after the first run, both with a test (the ledger was deleted and rebuilt; nothing had been reviewed):
(1) `is_loan` — Russian `имя` has `inh` plus a `calque` template for a later sense ("Neologism sense: calque of English name"), so a word with its own
`inh`/`inh+` chain is no longer a loan; (2) the Russian line prefilter also accepts `Proto-Indo-European` (text-only PIE).

## Counts
Reproduce: `awk -F'\t' 'NR>1{print $1, $13}' shared_data/ru_cognate/ledger.tsv | sort | uniq -c`
| unit_type | proposed (join hit) | pending (miss) | none (non-IA) | total |
|---|---|---|---|---|
| root | 350 | 396 | 7 | 753 |
| family | 210 | 626 | 18 | 854 |
| all | 560 | 1022 | 25 | 1607 |

- Rows = 753 + 854 (`sqlite3 dpd.db "select count(*) from dpd_roots"` = 753; `select count(distinct family_word) from dpd_headwords where root_key='' and family_word!=''` = 854).
- No `none` row has candidates, and no `карма|будда|нирвана|шаман` in `ru_candidates`: `python3 -c` over the ledger gives 0 and 0.
- `non_ia` rule = any headword of the unit carries `non_ia` (spec literal): 7 roots + 18 families. Reproduce: `awk -F'\t' 'NR>1 && $13=="none"{print $1}' shared_data/ru_cognate/ledger.tsv | sort | uniq -c`.

## Resolved by source side (proposed rows)
Reproduce: the `source` column starts `Wiktionary: sa …; pi …; ru …`; counts by which parts occur (`stats` script below).
Sanskrit side only 271 · Pāḷi side only 30 · both 259.

## Russian entries reaching PIE: direct vs Proto-Slavic hop
`stats` script below (needs the dumps). Distinct Russian words in the index: **2,462** with the PSL hop, **1,147** direct only → **1,315 (53 %) come only through the PSL hop**.
Units proposed with a direct-only Russian index: 417 of 560 → **143 units (26 %) need the PSL hop**.

## Gold set (13 pairs, ledger after the join)
Reproduce: for each unit, `awk -F'\t' '$2=="<key>"{print $13, $9}' shared_data/ru_cognate/ledger.tsv`.
| pair | unit | result |
|---|---|---|
| √dvar → дверь | root `√dvar` | **found** (via the Pāḷi side `dvāra`, Skt `dvṛ` itself has no entry) |
| bhātar → брат | family `bhātar` | found |
| nāma → имя | family `nāma` | found (after the `is_loan` fix) |
| nava1 → новый | family `nava1` | found (PSL hop) |
| ti → три | family `ti` | found |
| bhamu → бровь | family `bhū` (Skt `bhrū`) | found |
| mātar → мать | family `mātar` | found |
| vidhavā → вдова | family `dhava` | found |
| dvi → два | family `dvi` | found |
| aṭṭha → восемь | family `aṭṭha` | found |
| √budh → будить | root `√budh` | found (from another key than `*bʰúdʰs`, plus noise) |
| √ñā → знать | root `√ñā` | found |
| cha → шесть | family `cha` | **MISS, only `шестой` found.** DPD lists Skt `ṣaḍ`; Wiktionary's PIE keys (`*swéḱs`) sit on lemma `ṣáṣ` while `ṣáḍ`/`ṣáṭ` have none. Sandhi-form mismatch; the verifier only sees candidates, so `шесть` must be added by hand in `ru_final` at review (7.1). |
12 of 13 found.

## Sheet pairs reproduced
`shared_data/ru_cognate/sheet_snapshot.csv` (45 lines, 41 CSV records; one record spans several lines and cannot be paired). Pali word → its root/family unit → Russian word ∈ `ru_candidates`:
**12 found · 16 unit exists but Russian word not among candidates · 12 no root/family unit** (words under neither, e.g. `Pita`, `Nasa`, `Jivati`, or malformed rows).
Many misses are expected: the sheet mixes loans and sound-alikes; the join emits inherited cognates only. Not used as AI input.

## Noise in the join (informational)
The join is deliberately generous: mean 4.8 candidates per proposed unit, some far-fetched (`√kath` → `где, как, кто …` through a bare `*kʷ`). The verifier (stage 2) is the filter; `ru_final` takes only confirmed words.

## AI request estimate (recomputed, batch 25)
- `propose`: 1,022 pending → 41 requests.
- `verify`: 560 proposed now + the pending units the model marks `cognate`/`unsure` (guess 25–40 %, i.e. 250–410) → 810–970 rows → 33–39 requests.
- Total ≈ 74–80, ~90 with retries (spec guessed 100–120). Confidence 5/10; the 25–40 % share is an assumption until the pilot (6.1).

## `stats` script (scratch, deleted at 4.3)
Counts above that need the dumps come from `temp/ru_cognate/baseline_stats.py`: it runs `index_russian(..., psl)` and `index_russian(..., {})`, compares the word sets,
re-runs `join_units` with the direct-only index, and matches `sheet_snapshot.csv` Pali words to units via `dpd_headwords.lemma_1`. Re-download the dumps (`README.md` curl lines) to redo it.

## AI runs
Reproduce counts: `awk -F'\t' 'NR>1{print $13}' shared_data/ru_cognate/ledger.tsv | sort | uniq -c`.
**Session 2026-11-16 (pilot, 11:5x UTC, off-peak):** `propose --max-batches 1` (deepseek-flash, 25 units, 8.5 s) → 20 `none`, 3 `proposed` (`√aṅg` угол/угль, `√añj 1` угол, `√āgam` гнать/гнаться), 2 `unsure` with no words (`√añch`, `√udrabh`) left `pending`. `verify --max-batches 1` (deepseek-v4-pro, 25 rows): first reply unusable because of the `(root)` prompt suffix (fixed); same reply applied locally → 14 `verified`, 11 `disputed`. Ledger after pilot: 999 pending, 538 proposed, 45 none, 14 verified, 11 disputed.
Observations for the user: the verifier confirms some doubtful sets (`√ar` → рать, рост, расти; `√as 1` → ещё, абы, забыть) while rejecting `√as 2-4` with the same candidate list; `ru_final` does not follow "most recognisable first" reliably.

### 6.1a–6.1b re-verify of the 25 pilot rows (2026-11-16, tightened `VERIFY_RULES`)
- 6.1a: `VERIFY_RULES` extended; `unsure` + no words → `status none`; `√añch`, `√udrabh` set to `none` locally. 39 tests pass; gates clean.
- 6.1b: the 25 pilot rows reset to `proposed` and re-verified (1 batch, deepseek-v4-pro, 0 problems). Before: 14 confirmed / 11 rejected. After: 10 `verified`, 15 `disputed`.
- Kept: `√akkh` око, окунь; `√agg` огонь; `√aṅg` угол; `√ad` есть, еда, яд; `√an` вонь, вон; `√ādā` дать, дар, дань; `√i 1/2` идти, найти, прийти; `√ikkh` око, окунь; `√is` искать.
- Now rejected: `√ar`, `√as 1–4`, `√ās` (as intended); also `√āgam` гнать (was kept before) and `√añj 1` угол.
- Open for the user at 6.1c: `окунь` newly kept under `√akkh`; `найти, прийти` both kept under `√i` (derivatives of идти — the new rule asks to list only the base word).

### 6.1d–6.1e re-verify with the sound + member-meaning rule (2026-11-16, 12:1x UTC, off-peak)
- 6.1d: verify prompt now lists member headwords; `VERIFY_RULES` gains the sound + meaning rule. 41 tests pass; gates clean.
- 6.1e: 25 pilot rows reset and re-verified (1 batch, deepseek-v4-pro, 43.7 s). 24 applied, 1 problem (`√āgam`: "confirmed without ru_final" → row left `proposed`). Result: 5 `verified`, 19 `disputed`.
- Kept: `√ad` есть, еда, медведь; `√an` вонь, вон; `√i 1` идти; `√ikkh` око; `√is` искать. Dropped as intended: `√ādā` дать (take ≠ give), `√i 2` идти (study ≠ go), `√ad` яд, `√i 1` найти/прийти.
- **Defect:** for `√akkh` (око), `√agg` (огонь), `√aṅg` (угол), `√añj 1` (угол) the `verifier_note` argues for "confirmed" but the verdict is `rejected`. The note has turned into running reasoning and the verdict field disagrees with it. `√ad` keeps медведь (meaning "bear" fails the meaning rule).

### 6.1g–6.1h: note-first schema, consonant rule, PIE-as-hint (2026-11-16, 12:18–12:25 UTC, off-peak)
- 6.1g: `VERIFY_RULES` rewritten: 4 numbered keep-conditions (etymology, audible root consonant, member-headword meaning, no derivatives); reply schema `verifier_note` first; note = one short sentence; verdict must agree with note. Then added "the claimed PIE root is only a hint" (join keys are often PIE word forms, e.g. `h₁n̥gʷnis`, `h₂isketi`). 44 tests pass; gates clean.
- Run A (consonant rule, schema): note/verdict contradictions gone; `√ad` = еда; but `√agg` огонь and `√is` искать falsely rejected (judged the claimed PIE string literally).
- Run B (+ PIE-as-hint): 0 problems; 13 verified / 12 disputed. Fixed: `√agg` огонь, `√is` искать, `√akkh`/`√ikkh` око, `√ādā` none, `√i 2` none. New wrong keeps: `√ad` еда, **яд, едкий**; `√i 1` идти, **найти**; `√añc`/`√añj 3` **ячмень**; `√ar` **рост, расти** (move ≠ grow); `√añj 1` угол (distinguish).
- Conclusion: one verify pass at batch 25 with thinking disabled (`tools/ai_openai_compat.py:54`) is unstable between runs; the rules are now right, the single-shot judgment is not.

### 6.1i–6.1j: thinking enabled (2026-11-17)
- 6.1i: `VERIFY_REQUEST_OPTIONS` (`thinking` enabled, `max_tokens` 32768) + `check_grounded_chain` + `make_ask(manager)`; 49 tests pass; gates clean; `tools/` untouched.
- 6.1j: run **with `--allow-peak` on the user's explicit instruction** (03:5x UTC was peak; the plan said never). Run B snapshot taken, 25 pilot rows reset.
- Batches (deepseek-v4-pro): batch-size 10 → batch 1 OK 361 s (10 rows); batch 2 **FAILED** after 472 s, `finish_reason=length`, all 32,768 completion tokens were reasoning, no content (exit 2). Re-run at batch-size 5 → 376 s, 122 s, 237 s, 15 rows, 0 problems. Ledger after: 538 proposed, 997 pending, 47 none, 9 verified, 16 disputed.
- Finding: with thinking on, a 10-row batch can burn the whole 32k budget. Batch 5 is safer; full verify at batch 5 ≈ 108 requests, ~2–6 min each.
- Run B → run C (ru_final): √aṅg угол → none; √añc, √añj 3 ячмень → none; √ad еда, яд, едкий → еда, едкий; √an вонь, вон → вонь; √ar рост, расти → расти; √i 1 идти, найти → идти. Unchanged: √akkh/√ikkh око, √agg огонь, √añj 1 угол, √is искать; √ādā, √i 2 → none.
- Still wrong or doubtful in run C: √ad **едкий** (kept; "caustic" ≠ eat), √ar **расти** (grow ≠ move), √añj 1 **угол** kept while √aṅg угол rejected (same Pāli family, inconsistent), √an вонь.
- 6.1k user verdict (2026-11-17): not satisfied. едкий, расти wrong; вонь not similar in sound (an/āna) and doubtful in meaning; √aṅg vs √añj 1 угол is not an inconsistency (√aṅg has only aṅgaṇa "courtyard"; √añj 1 has aṅga "limb"). Join gap noted: √as 1 "be" never gets есть ("is"), which is indexed only under √ad. Next: per-word labels (plan 6.1l–6.1o).

### 6.1p–6.1s: candidate cleanup + thinking-off two-pass pilot (2026-11-17)
- Cleanup (6.1q) on the live ledger: `clean_ledger` → `(92, 149)` (92 rows changed, 149 of 2,728 words dropped).
  The dumps-based join key fix (√as 1–4 добыча, забыть, …) is deferred (needs ~1.1 GB dumps re-download).
- Pilot E (`verify --no-thinking --passes 2 --batch-size 5`), off-peak, no `--allow-peak`:
  E1 (25 pilot rows): 5 batches, 1 problem (`pass 2: √ar: word not in candidates: ратить`), the row was re-run
  once with `--batch-size 1` (deviation from plan's batch 3, to avoid touching non-pilot rows) → fine.
  E2: 5 batches, 0 problems. Held-out (25 rows): 5 batches, 0 problems. No `finish_reason=length`.
- Per-request seconds (min/median/max): D1 (thinking on) 199/361/456 (1 fail); E1 7/11/17; E2 8/12/17; held-out 9/14/21.
  ≈ 25–30× faster. One batch of 5 (two requests) ≈ 25 s → 513 rows ≈ 103 batches ≈ 45 min.
- Result quality: **0 of 50 rows have a kept word** (all `disputed`). Right words land in `ru_flagged`
  (око, огонь, идти, искать, дар/дать, вода, учить, клясть…) because thinking-off labels `sound` as `weak`
  where D1 said `close` (огонь/aggi weak in E1, close in D1). Pass disagreement is small (9 words in E1, 8 in E2).
  Junk is also flagged (√ad яд/ясли/яство; √kan чадо/щенок…).
- Ledger now: proposed 513, pending 997, disputed 50, none 47. No DB writes.

### 6.1u–6.1w: new pass combination + flag rule (2026-11-17)
- Code: `_outcome` flag needs sound or meaning `close`; `apply_verify_pair` keep-if-either / drop-if-both / else flag.
  124 tests pass (ai/ledger/etyma); ruff, pyright, pyrefly clean; `git diff --stat tools/` empty.
- Run F (50 rows, 10 batches of 5 + one batch of 2 for √ikkh/√kand after one off-candidate word each):
  per-request seconds min/median/max 7.8/12.4/21.8 (22 requests). Counts: proposed 513, pending 997, none 47,
  verified 2, disputed 48.
- Kept: √ad еда; √kās 2 кашель. Flagged 11 words / 8 rows (run E: 37 / 22): око, огонь (√akkh, √agg), идти (√i 1),
  искать (√is), вода (√ud), квас (√kaṭh 2), дар/дань/дарить/даровать (√ādā), кашлять (√kās 2).
- Expectations met: no ячмень, яд, язь, кон/чадо/щенок, кой/чей, чары kept; √i 2 none. Not met: √akkh око and
  √agg огонь flagged not kept; √kās 2 кашель kept; √ikkh око, √uc учить, √kās 1 кашель now dropped.

### 6.1x–6.1z: code-side sound (2026-11-17)
- Code: `ru_cognate_sound.py` (28 tests) + `ru_cognate_ai.py` wiring; model no longer labels `sound`. 153 tests pass; all gates clean.
- Run G: 50 rows re-verified (`verify --no-thinking --passes 2 --batch-size 5 --max-batches 10`), 0 problems, off-peak.
  Counts after: proposed 513, pending 997, none 47, verified 7, disputed 43. 20 requests, 7.7 / 11.9 / 22.4 s min/median/max.
- Kept (8 words / 7 rows): √akkh око, √agg огонь, √ad еда, √is искать, √kās 2 кашель, √ādā дар + дать, √ikkh око.
  Flagged: 16 words / 14 rows (run F: 11 / 8). Run F kept only еда, кашель.
- Expectations met: √akkh око, √agg огонь, √is искать, √ad еда, √kās 2 кашель kept; √i 2 none kept; no ячмень, яд, язь,
  кон/чадо/щенок, кой/чей, чары kept (яд, чары only flagged).
- Unexpected kept (user decides at review): √ādā дар, дать (model meaning label "close" for take ≠ give; дать was
  an anchor expected "far"); √ikkh око (sound close via `K` skeleton). Flagged but not expected: √akkh окунь, √ad яд,
  √ar ронять/рушить, √kand клясть/колокол, √uc учить, √kas 2 короста, √kās 1 чекать, √kit 3 честный.

### 6.1za–6.1zc: strict pass combination (2026-11-17)
- Rule (spec 7 amendment f): per word, keep only if both passes keep; drop if either pass drops; else flag.
  Code: `apply_verify_pair` in `scripts/ru_cognate/ru_cognate_ai.py` (tests: 153 pass across the 4 ru_cognate test files; ruff, pyright, pyrefly clean; `git diff --stat tools/` empty).
- Recompute: 50 verified/disputed rows recomputed offline from their notes (no AI calls, notes round-trip asserted).
  Only `status`, `verifier_verdict`, `ru_final`, `ru_flagged` changed (diffed against the pre-run copy).
- Counts after: proposed 513, pending 997, none 47, verified 5, disputed 45.
- Kept (5): √akkh око; √agg огонь; √ad еда; √is искать; √kās 2 кашель.
- Flagged (5 rows, for the user at phase 7): √ad яд; √ādā дар; √i 1 идти; √ikkh око; √ud вода.
- Lost vs run G: учить (√uc) and квас (√kaṭh 2) were flagged in run G and are now dropped (a pass disagreed); likewise every other run G flagged word not listed above.

### 6.1zd–6.1zf: validation run, 50 roots + 50 families (2026-11-17) — selection (6.1ze)
Seed `random.Random(20261117)`; 13 gold units first, then 47 random roots and 40 random families from the `proposed` rows.
- Roots: √dvar, √budh, √ñā, √ghaṭ 1, √bhuj 1, √khā, √jhā, √kham, √paṇ, √migh, √paṭ 2, √tan, √cikkh, √bhaj 2, √pis 1, √mas 2, √mah 2, √thu 1, √dā 1, √vah, √ruj, √tapp 2, √han, √gah, √mih 1, √vic, √ṭhā, √vid 2, √gas, √khī, √vā, √gā, √ḍaṃs, √jan, √vhe, √dhā, √gad, √cud, √dar 1, √dhar 1, √gar 1, √vaddh, √har 1, √dā 2, √yam 1, √mañc, √vis 2, √panth, √dam, √dal
- Families: bhātar, nāma, nava1, ti, bhū, mātar, dhava, dvi, cha, aṭṭha, ghana, ahaṃ, jimha, hima, iti, miñja, loha, yuva, muddha, pheṇa, aṇḍa, adhi, muṭṭhi, kāṇa, khujja, piṅgala, upari, duma, pāṇi, pabba, pisāca, haliddī, dīgha, loṇa, takka, tamas, sa, sassa, saha, eta, siras, jivhā, salla, ha, tiṇa, siṅga, hema, rukkha, dalidda, ud

#### Result (6.1ze–6.1zf, 2026-11-17; off-peak, `--no-thinking --passes 2 --batch-size 5`, v1 20 batches + v2 1 leftover batch)
- Only the 100 listed rows changed (`status`, `verifier_verdict`, `verifier_note`, `ru_final` ×32, `ru_flagged` ×25). Counts: proposed 413, pending 997, none 47, verified 36, disputed 113 (this run: verified 32, disputed 68). No `finish_reason=length`, no exit 2. v1: 1 problem (one row left `proposed`, done by v2).
- Gold (13): kept дверь, бдеть/бодрый/будить, знать, брат, новый, три, бровь, мать, вдова, два, шестой (cha — the join gives only шестой, kept); flagged имя (nāma), восемь (aṭṭha) — code sound `weak`. All as spec amendment g expected. Also flagged: двор, знамя.
- Roots (50): verified 17 / disputed 33; kept words 23 (17 rows), flagged words 21; 4 flag-only rows (√ghaṭ 1, √bhaj 2, √han, √mih 1); 14 rows with `pass 2 differs`.
- Families (50): verified 15 / disputed 35; kept words 15 (15 rows), flagged words 15; 6 flag-only rows (nāma, aṭṭha, hima, miñja, loha, loṇa); 13 rows with `pass 2 differs`.
- Near misses (etymon same + form base, dropped): mostly meaning far/drifted or sound weak; notable true-looking losses: √thu 1 стоять/стать/ставить (sound close, meaning close, dropped by pass disagreement), ahaṃ я, iti и/он/их (code sound `none`).
- Per-request seconds (42 requests): min 4.4, median 16.1, max 27.2.

### 6.2: propose run (2026-11-17, ~14:00 UTC, off-peak)
`propose` (deepseek-flash, batch-size 25, no `--allow-peak`): 40 batches, 996 rows changed, 1 problem; a second run retried the leftover and got the same rejection. Ledger after: pending 1, none 951, proposed 505 (413 + 92 new), verified 37, disputed 113 (total 1607).
- Left `pending`: `parā` — model returned `ru_candidates ['пере-', 'через', 'пара']`; `пере-` is a prefix (not a valid word per `parse_words`), so the whole item is rejected, twice. Not touched.

### 6.3: verify run (2026-11-17, 14:00–14:55 UTC, off-peak, `--no-thinking --passes 2 --batch-size 5`, deepseek-v4-pro)
Run 1: 101 batches, 495 rows changed, 11 problems (second pass dropped a word / missing answers: √chid, √tar 1, √pas, √vu, √veṭh, √had, √har 2, √har 3, √ve …), 10 left `proposed`, no `finish_reason=length`, exit 0. Run 2 (leftovers): 2 batches, 10 rows changed, 0 problems. Requests (run 1, 202): min 2.1 s, median 14.9 s, max 32.6 s.
Ledger after: proposed 0, pending 1 (`parā`), none 951, verified 126, disputed 529 (total 1607). Every verified/disputed row (655) has `verifier_verdict` and `verifier_note`. Rows with a kept word 126; rows with a flagged word 153 (110 flag-only). No loan (`карма|будда|нирвана|шаман`) in any `ru_final`.

### 6.4: post-AI gold and sheet tables (2026-11-17, after 6.3)
Ledger: proposed 0, pending 1 (`parā`), none 951, verified 126, disputed 529. No loan (`карма|будда|нирвана|шаман`) in any `ru_final`.

Gold set (13) — `ru_final` / `ru_flagged`:
| unit | status | ru_final | ru_flagged |
|---|---|---|---|
| √dvar | verified | дверь | двор |
| bhātar | verified | брат | — |
| nāma | disputed | — | имя |
| nava1 | verified | новый | — |
| ti | verified | три | — |
| bhū (bhamu) | verified | бровь | — |
| mātar | verified | мать | — |
| dhava (vidhavā) | verified | вдова | — |
| dvi | verified | два | — |
| aṭṭha | disputed | — | восемь |
| √budh | verified | бдеть, бодрый, будить | — |
| √ñā | verified | знать | знамя |
| cha | verified | шестой | — |
**10 of 13 in `ru_final` (cha as шестой, not шесть — join miss, add `шесть` at 7.1); имя and восемь only flagged (code sound `weak`) — user decides at 7.1.**

Sheet pairs (Pali word → unit → Russian word), 40 matchable records: **7 in `ru_final`** (pheṇa пена; dvāra дверь; vidhavā вдова; kiṃ кто; giri гора; yuga иго; pivati пить), **3 only flagged** (nabhas небо; diva день; hima зима), **0 dropped by the AI after being a candidate; 12 unit exists but the word was never a candidate** (patati падать, mūsikā мышь, nagga нагой, sīdati сидеть, theyya таить, dadāti давать, ṭhāna, ete эти, te те, pakāseti, lapati ляпнуть, hanati), **18 no unit** (e.g. plavati, mata, pita, kāsa, jivati, nasa, samaṇa шаман — loan, rightly absent).
Note: the 12 «not a candidate» were not candidates at the join; earlier baseline counted 12 found / 16 / 12 with a different matcher, so totals differ slightly.

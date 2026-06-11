# Export Memory to Rules

Analyze all memory files and suggest promotions to CLAUDE.md or kamma/ folder.

---

## What to do

You are being asked to export and classify memory entries. Follow these steps:

### 1. Collect all memory entries
Read all `.md` files from `~/.claude/projects/-Users-deva-Documents-dpd-db/memory/`. Skip the index file (`MEMORY.md` if it exists).

For each memory file, extract:
- **Name** (from frontmatter `name:`)
- **Type** (from frontmatter `type:` — one of: user, feedback, project, reference)
- **Content** (the body)
- **Age** (relative to today, 2026-04-08; note if older than 7 days)

### 2. Classify each entry
For each memory, decide one of these destinations:

- **→ Global `~/.claude/CLAUDE.md`**
  - Universal rules that apply to ALL projects
  - Examples: "never use memory", "always use type hints", "use uv for deps"
  - Go under existing sections like `## Code Standards`, `## Testing Protocol`, `## Communication`, or create a new section

- **→ Local `/Users/deva/Documents/dpd-db/CLAUDE.md`**
  - Rules specific to this dpd-db project only
  - Examples: "model relationships are in db/models.py", "use DpdHeadword for headwords"

- **→ `kamma/` folder**
  - Workflow notes, process steps, or async context (not rules)
  - File path: specify which file in `kamma/` or suggest a new one
  - Examples: "migration A blocked by migration B", "team prefers PR size < N commits"

- **→ Discard**
  - Outdated, already covered, or not actionable
  - Reason: explain why

### 3. Present recommendations
Create a **markdown table** with columns:
- Memory name
- Current type
- Recommendation (one of: global, local, kamma, discard)
- Target (file path if promoting)
- Reason (one-line)

Example:
```
| Memory | Type | Recommendation | Target | Reason |
|--------|------|---|---|---|
| user_role | user | → Global | `## Communication` section | Universal principle applies across projects |
| feedback_testing | feedback | → Local | `CLAUDE.md` / `## Testing Protocol` | DPD-specific test requirements |
```

### 4. Get user approval
Present the table and ask: *"Approve these promotions? Any changes?"*

Wait for explicit approval. Do NOT apply changes until user confirms.

### 5. Apply changes (after approval)
For each approved promotion:
1. **Global or Local CLAUDE.md:** Add the rule under the appropriate section (or create a new section if needed). Preserve existing structure and tone.
2. **kamma/:** Append the note to the target file in proper markdown.
3. **Delete the promoted memory file immediately.** This prevents duplication—once a memory is promoted to a permanent rule file, it must be removed from memory.

Report success: *"✓ Promoted N entries, cleaned memory folder."*

### 6. Return summary
List what was promoted and where. Example:
```
Global rules added: 2 (Code Standards, Security)
Local rules added: 1 (Testing Protocol)
Workflow notes added: 1 (kamma/conductor.md)
Memory files deleted: 4
Remaining memory: 0 files
```

**Critical:** After this completes, the memory folder should contain ONLY entries that were NOT promoted (i.e., marked "discard" or not yet ready for promotion).

---

## Edge cases

- **Empty memory:** If no memory files exist, say so and exit.
- **Conflicting rules:** If a memory conflicts with existing rules, flag it and ask for clarification.
- **Multi-section memories:** If a memory spans multiple topics, suggest promoting the whole entry to ONE target, or ask the user to split it.
- **Aged memories:** If a memory is older than 7 days, note this in the recommendation reason.

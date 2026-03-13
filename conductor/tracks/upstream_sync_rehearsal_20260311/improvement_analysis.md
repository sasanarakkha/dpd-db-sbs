# Improvement Analysis: Upstream Sync Rehearsal

Based on the errors and feedback from the 2026-03-11 session, the following systemic improvements are recommended to refine the synchronization workflow.


## 2. Mandatory Dual-Shadow Parity
**Problem**: The agent frequently updated one localized shadow (e.g., SBS) but forgot to apply the same logic to its Russian counterpart, leading to broken builds.
**Solution**: 
- Update the track plan to include a **"Dual-Shadow Check"** task.
- Explicitly require the agent to identify all shadow copies mapped to an upstream source (RU and SBS) and update them in the same turn.

## 3. Strict Upstream Mirroring
**Problem**: When a shadow copy fails, agents often try to "guess" a fix or invent new solutions that diverge from the upstream logic, creating long-term maintenance debt.
**Solution**: 
- Enforce the **"Mirror Upstream Logic"** rule: Whenever an error occurs in a shadow file, the agent MUST open the original upstream source and emulate its logic exactly.
- Discourage arbitrary "cleanup" or refactoring during sync; only localized updates should be layered on top of upstream logic.

## 4. CSS/JS Namespace Isolation
**Problem**: Migrating upstream templates to Jinja2 caused conflicts in GoldenDict because the RU and SBS dictionaries shared the same HTML IDs and JS function names.
**Solution**: 
- Mandate a **"Unique Localization Namespace"** in the template guidelines. 
- All IDs, classes, and JS functions in localized templates MUST have a suffix (e.g., `_ru` or `_sbs`) to ensure compatibility when multiple dictionaries are active.

## 5. Reinforced Phase Gating
**Problem**: Agents sometimes committed partial work or advanced to verification phases while critical bugs were still present.
**Solution**: 
- Strengthen the **"Unambiguous Approval Protocol"**. 
- The agent is forbidden from committing or moving phases unless the user explicitly provides a specific "Phase is complete" or "Proceed with final commit" signal.

## 6. Automated Parity Verification
**Problem**: `test_shadow_parity.py` often fails due to legitimate localization differences, making it difficult to spot real regressions.
**Solution**: 
- Implement an automated **"Whitelist Generation"** step in the plan.
- The agent should be able to generate a temporary AST-based whitelist for intended differences, allowing it to focus only on unexpected parity breaks.

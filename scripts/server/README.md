# scripts/server/

## Purpose & Rationale
`scripts/server/` provides deployment and update scripts for production server environments — handling updates to both the main DPD and SBS variants on hosted infrastructure.

## Architectural Logic
"Server Deployment" pattern:
1. **Pull:** Fetches the latest code and data from the repository.
2. **Build:** Rebuilds the database and exports on the server.
3. **Restart:** Cycles server processes (webapp, API) to apply changes.

## Relationships & Data Flow
- **Target:** Server-hosted instances of DPD and DPD-SBS.
- **Triggered by:** SSH-based manual invocation or CI/CD hooks.
- **Dependencies:** Requires `git`, `uv`, and project dependencies installed on the server.

## Interface
- `bash scripts/server/update-dpd.sh`
- `bash scripts/server/update-dpd-sbs.sh`

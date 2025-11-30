## Archive

This directory keeps non-primary or legacy assets to keep the main codebase lean:

- `frontends/admin-portals`: older portal bundles kept for reference.
- `frontends/user-app`: legacy standalone user bundle (main app now lives in `frontend/`).
- `frontends/tech-field-app`: legacy field-tech bundle; current flows are in `frontend/`.
- `frontends/dist`: build artifacts not needed for source control.

Nothing here is loaded by default builds; move back if you explicitly need to revive an old bundle.

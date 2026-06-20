# Original repo preservation note

The chat environment could browse the public repository, but the container used to create ZIP files could not resolve `github.com`, so it could not clone the repository directly.

This package is therefore a complete updated RNW codebase/scaffold, not a byte-for-byte clone of every original file. It follows the same public architecture (`backend/rnw`, `models`, `routes`, `services`, `templates`, Docker, migrations, tests) and includes the previous patch scripts in `patch_history/`.

To preserve every unchanged upstream file exactly:

1. Clone your repository locally:
   ```bash
   git clone https://github.com/reddycea/RoomNearWork.git
   cd RoomNearWork
   ```
2. Copy the scripts from `patch_history/` into that clone.
3. Run:
   ```bash
   python apply_roomnearwork_fixes.py
   python apply_roomnearwork_concurrency_fixes.py
   python apply_roomnearwork_roles_threads_fixes.py
   python apply_roomnearwork_marketplace_features.py
   ```
4. Copy `backend/rnw/static/css/uber.css`, `backend/rnw/static/js/app.js`, and the updated templates from this ZIP if you want the Uber-inspired UI.
5. Review `git diff`, run tests, then commit.

# Clean-room controls (No RustDesk shadow)

This project is a **from-scratch rewrite**. These controls exist to ensure we can credibly claim:

- No code reuse from RustDesk
- No protocol compatibility with RustDesk
- No accidental brand/string leakage

## Process rules

- **No copy/paste** from RustDesk repositories, issues, or code snippets.
- Spec writers can describe behavior; implementers build from specs.
- Any third-party library must be added via the allowlist process and recorded.

## Automated controls (CI + local)

### 1) Forbidden string scan

We block commits that introduce RustDesk identifiers into `afkzone2/`:

- `rustdesk`
- `rustdesk.com`
- `com.carriez`
- `carriez`
- and other reserved legacy identifiers

Script: `afkzone2/tools/check_clean_room.py`

### 2) Dependency allowlist

We validate dependencies for the new subproject only:

- Backend: `afkzone2/backend/requirements.txt`
- Client: `afkzone2/clients/ug_shell_flutter/pubspec.yaml`

Allowlist file: `afkzone2/tools/dependency_allowlist.json`

### 3) License scan (recommended)

Add a license scanning tool in CI (e.g., ScanCode/FOSSA) to report new licenses.
This MVP repo includes hooks to add that later without changing product code.

## How to run locally

```powershell
python afkzone2/tools/check_clean_room.py
python afkzone2/tools/check_deps_allowlist.py
```


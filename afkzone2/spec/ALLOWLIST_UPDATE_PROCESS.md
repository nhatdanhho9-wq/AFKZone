# Dependency Allowlist Update Process

## Overview

All dependencies for afkzone2/ must be explicitly approved in `afkzone2/tools/dependency_allowlist.json`.

## Update Process

### 1. Add New Dependency

1. **Create PR** adding the new dependency to:
   - `afkzone2/backend/requirements.txt` (Python)
   - `afkzone2/clients/*/pubspec.yaml` (Flutter)

2. **Update allowlist** in the same PR:
   ```json
   // afkzone2/tools/dependency_allowlist.json
   {
     "python_requirements": [
       "existing-dep",
       "new-dependency"  // Add here
     ],
     "flutter_pubspec": [
       "flutter",
       "new_flutter_package"  // Add here
     ]
   }
   ```

3. **Include in PR description:**
   - Dependency name and version
   - Why it's needed
   - License type (must be permissive: MIT, BSD, Apache-2.0)
   - Security audit status (if available)

### 2. Review Requirements

- **Backend dependencies**: Reviewed by Backend Lead
- **Flutter dependencies**: Reviewed by Mobile Lead
- **All changes**: Require 1 approval minimum

### 3. CI Enforcement

The `afkzone2-ci.yml` workflow runs:
```
python tools/check_deps_allowlist.py
```

This check **fails** if any dependency is not in the allowlist.

### 4. Removing Dependencies

1. Remove from requirements.txt or pubspec.yaml
2. Remove from dependency_allowlist.json
3. Create PR with justification

## Approved License Types

| License | Status |
|---------|--------|
| MIT | ✅ Approved |
| BSD-2-Clause | ✅ Approved |
| BSD-3-Clause | ✅ Approved |
| Apache-2.0 | ✅ Approved |
| ISC | ✅ Approved |
| Unlicense | ✅ Approved |
| GPL | ❌ Forbidden |
| LGPL | ⚠️ Case-by-case |
| AGPL | ❌ Forbidden |

## Emergency Updates

For critical security patches:
1. Create PR with `[SECURITY]` prefix
2. Ping @security-team and @cto
3. Can be merged with 1 approval after 1 hour

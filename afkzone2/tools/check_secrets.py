"""
AFKZone vNext - Secrets Scanner
Scans files for potential secrets and credentials.
Used by CI to enforce no-secrets policy.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Patterns that indicate potential secrets
SECRET_PATTERNS = [
    (re.compile(r'password\s*[:=]\s*["\'][^"\']{8,}["\']', re.IGNORECASE), "hardcoded password"),
    (re.compile(r'api[_-]?key\s*[:=]\s*["\'][^"\']{16,}["\']', re.IGNORECASE), "API key"),
    (re.compile(r'secret\s*[:=]\s*["\'][^"\']{16,}["\']', re.IGNORECASE), "secret value"),
    (re.compile(r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----'), "private key"),
    (re.compile(r'-----BEGIN CERTIFICATE-----'), "certificate"),
    (re.compile(r'token\s*[:=]\s*["\'][A-Za-z0-9_\-\.]{32,}["\']', re.IGNORECASE), "token"),
    (re.compile(r'bearer\s+[A-Za-z0-9_\-\.]{32,}', re.IGNORECASE), "bearer token"),
]

# File types to scan
TEXT_EXTS = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".py", ".ts", ".tsx", 
    ".js", ".jsx", ".dart", ".html", ".css", ".toml", ".rs", ".sql",
    ".sh", ".bash", ".env",
}

# Directories to skip
IGNORE_DIRS = {
    ".git", ".dart_tool", "build", "node_modules", ".venv", "__pycache__",
    "dist", "target", ".idea", ".vs",
}

# Files to always skip
IGNORE_FILES = {
    "check_secrets.py",  # This file
    "package-lock.json",
    "pubspec.lock",
    "Cargo.lock",
}

# Allowed patterns (false positives)
ALLOWED_PATTERNS = [
    r'password\s*[:=]\s*["\']<redacted>["\']',
    r'password\s*[:=]\s*["\']test123["\']',
    r'password\s*[:=]\s*["\']password["\']',
    r'mock-turn-secret',  # Known mock value
    r'example\.com',
    r'\.example\.',
    r'_require_env\(',  # Env lookup
    r'os\.getenv\(',
    r'process\.env\.',
    r'\$\{.*\}',  # Template variables
    r'\{\{.*\}\}',  # Template variables
]


def is_text_file(p: Path) -> bool:
    return p.suffix.lower() in TEXT_EXTS


def should_ignore_dir(name: str) -> bool:
    return name in IGNORE_DIRS


def should_ignore_file(name: str) -> bool:
    return name in IGNORE_FILES


def is_allowed(line: str) -> bool:
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def scan_file(p: Path) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    try:
        data = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return hits
    for i, line in enumerate(data.splitlines(), start=1):
        if is_allowed(line):
            continue
        for pat, desc in SECRET_PATTERNS:
            if pat.search(line):
                hits.append((i, desc, line.strip()[:100]))
    return hits


def main() -> int:
    scan_path = ROOT
    if len(sys.argv) > 1:
        scan_path = Path(sys.argv[1])
    
    failures: list[str] = []
    for dirpath, dirnames, filenames in os.walk(scan_path):
        # Prune ignored dirs
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]
        for fn in filenames:
            if should_ignore_file(fn):
                continue
            p = Path(dirpath) / fn
            if not is_text_file(p):
                continue
            hits = scan_file(p)
            for (line_no, desc, line) in hits:
                failures.append(f"{p.relative_to(scan_path)}:{line_no}: {desc}: {line}")
    
    if failures:
        print("⚠️  Potential secrets detected:")
        for f in failures[:50]:
            print(f"  - {f}")
        if len(failures) > 50:
            print(f"  ... and {len(failures) - 50} more")
        print("\nUse <redacted> for sensitive values in docs.")
        print("Use environment variables for credentials in code.")
        return 2
    
    print("✅ No secrets detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

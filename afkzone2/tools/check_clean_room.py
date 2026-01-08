from __future__ import annotations

import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PATTERNS = [
    # Allow local repo folder name "rustdesk-dev" (not a brand leakage).
    re.compile(r"rustdesk(?!-dev)", re.IGNORECASE),
    re.compile(r"rustdesk\.com", re.IGNORECASE),
    re.compile(r"com\.carriez", re.IGNORECASE),
    re.compile(r"carriez", re.IGNORECASE),
]

TEXT_EXTS = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".dart",
    ".html",
    ".css",
    ".toml",
    ".rs",
    ".sql",
}

IGNORE_DIRS = {
    ".git",
    ".dart_tool",
    "build",
    "node_modules",
    ".venv",
    "__pycache__",
    # We allow RustDesk mentions in internal specs/tools docs.
    "spec",
    "tools",
}


def is_text_file(p: Path) -> bool:
    return p.suffix.lower() in TEXT_EXTS


def should_ignore_dir(name: str) -> bool:
    return name in IGNORE_DIRS


def scan_file(p: Path) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    try:
        data = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return hits
    for i, line in enumerate(data.splitlines(), start=1):
        for pat in FORBIDDEN_PATTERNS:
            if pat.search(line):
                hits.append((i, pat.pattern, line.strip()))
    return hits


def main() -> int:
    failures: list[str] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # prune ignored dirs
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]
        for fn in filenames:
            p = Path(dirpath) / fn
            if not is_text_file(p):
                continue
            hits = scan_file(p)
            for (line_no, pattern, line) in hits:
                failures.append(f"{p.relative_to(ROOT)}:{line_no}: forbidden({pattern}): {line}")

    if failures:
        print("Clean-room violation(s) found:")
        for f in failures[:200]:
            print(f"  - {f}")
        if len(failures) > 200:
            print(f"  ... and {len(failures) - 200} more")
        return 2

    print("OK: clean-room scan passed for afkzone2/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


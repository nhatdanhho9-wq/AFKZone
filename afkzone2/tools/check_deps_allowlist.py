from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "tools" / "dependency_allowlist.json"


def load_allowlist() -> dict:
    return json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))


def parse_requirements(path: Path) -> set[str]:
    """
    Parse requirements.txt into normalized project names.
    Keeps only the package name portion, lowercased.
    """
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # remove env markers and version pins
        name = re.split(r"[<=>\\[]", line, maxsplit=1)[0].strip()
        if name:
            out.add(name.lower())
    return out


def parse_pubspec_deps(path: Path) -> set[str]:
    """
    Lightweight parse of pubspec.yaml dependencies:
    - Reads lines under 'dependencies:' until next top-level key.
    - Extracts dependency names at indentation level 2.
    """
    out: set[str] = set()
    in_deps = False
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.rstrip("\n")
        if not in_deps:
            if line.strip() == "dependencies:":
                in_deps = True
            continue
        # stop at next top-level key
        if line and not line.startswith(" "):
            break
        m = re.match(r"^\\s{2}([A-Za-z0-9_\\-]+)\\s*:", line)
        if m:
            out.add(m.group(1).lower())
    return out


def main() -> int:
    allow = load_allowlist()
    allowed_py = {x.lower() for x in allow.get("python_requirements", [])}
    allowed_flutter = {x.lower() for x in allow.get("flutter_pubspec", [])}

    req_path = ROOT / "backend" / "requirements.txt"
    pubspec_path = ROOT / "clients" / "ug_shell_flutter" / "pubspec.yaml"

    py_deps = parse_requirements(req_path)
    fl_deps = parse_pubspec_deps(pubspec_path)

    bad_py = sorted(d for d in py_deps if d not in allowed_py)
    bad_fl = sorted(d for d in fl_deps if d not in allowed_flutter)

    if bad_py or bad_fl:
        print("Dependency allowlist violation(s):")
        if bad_py:
            print("  - backend/requirements.txt unexpected:", ", ".join(bad_py))
        if bad_fl:
            print("  - clients/ug_shell_flutter/pubspec.yaml unexpected:", ", ".join(bad_fl))
        print("\nUpdate afkzone2/tools/dependency_allowlist.json if these are approved.")
        return 2

    print("OK: dependency allowlist passed for afkzone2/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


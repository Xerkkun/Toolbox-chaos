"""verify_public_release_clean.py

Pre-publication audit script for the Fyskode Chaotic Systems Toolbox.

Fails if any of the following are found in the git-tracked files:
  - Absolute user paths  (Windows, Linux, and macOS user-home paths)
  - Local file:/// links
  - Tracked LaTeX auxiliary files (.aux, .fls, .fdb_latexmk, .synctex.gz)
  - Tracked forbidden directories (reports/, sources/, build/, dist/,
    release/, installer/archive/)
  - Non-redistributable Sprott originals
  - Common secret patterns (PRIVATE KEY, ghp_*, .env files)

Usage:
    python scripts/verify_public_release_clean.py

Exit codes:
    0  All checks passed.
    1  One or more violations found.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _git_ls_files() -> list[str]:
    """Return the list of files currently tracked by git."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _is_binary_ext(path: Path) -> bool:
    return path.suffix.lower() in {
        ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg",
        ".dll", ".exe", ".so", ".dylib", ".pyc", ".pyd",
        ".zip", ".7z", ".gz", ".tar", ".bz2",
        ".ico", ".webp", ".ttf", ".otf", ".woff", ".woff2",
    }


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        return ""


# ---------------------------------------------------------------------------
# Check definitions
# ---------------------------------------------------------------------------

# NOTE: Pattern is assembled from parts so that this file itself does not
# contain the literal strings it is scanning for (avoids false positives).
_WIN   = "C:" + r"[/\\]" + "Users" + r"[/\\]"   # Windows path (assembled)
_LINUX = "/" + "home" + "/" + r"[^/\s]+"           # Linux home dir (assembled)
_MAC   = "/" + "Users" + "/" + r"[^/\s]+"           # macOS home dir (assembled)
_FILE  = "file" + ":" + "/" + "/" + "/"             # Local file URI (assembled)
ABSOLUTE_USER_PATH_RE = re.compile(
    "|".join([_WIN, _LINUX, _MAC, _FILE]),
    re.IGNORECASE,
)

LATEX_AUX_EXTENSIONS = {
    ".aux", ".fls", ".fdb_latexmk", ".synctex.gz",
    ".bbl", ".blg", ".bcf", ".toc", ".out",
}

FORBIDDEN_TRACKED_DIRS = {
    "reports/",
    "sources/",
    "build/",
    "dist/",
    "release/",
    "installer/archive/",
}

SPROTT_ORIGINALS = {
    "BOOKFIGS.DIC", "SELECTED.DIC", "SPECIAL.DIC",
    "SADISK.ZIP", "SA.EXE", "SAWIN.EXE",
    "PROG28.BAS", "PROG28QC.C", "PROG28TC.CPP", "VBRUN200.DLL",
}

_SEC_PRIVATE = "PRIVATE" + " KEY"
_SEC_GHP     = "ghp" + "_" + "[A-Za-z0-9]{36}"    # GitHub PAT
_SEC_SK      = "sk-" + "[A-Za-z0-9]{20,}"          # OpenAI-style key
_SEC_CS      = r"client_secret\s*[:=]\s*\S"
_SEC_AK      = r"api_key\s*[:=]\s*\S"
SECRET_PATTERNS_RE = re.compile(
    "|".join([_SEC_PRIVATE, _SEC_GHP, _SEC_SK, _SEC_CS, _SEC_AK]),
    re.IGNORECASE,
)

INTERNAL_PROMPT_RE = re.compile(
    r"^prompt_codex_.*\.md$"
    r"|^registro_.*_seed\.md$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_audit() -> int:
    tracked = _git_ls_files()
    violations: list[str] = []

    for rel in tracked:
        path = ROOT / rel
        rel_lower = rel.replace("\\", "/")

        # 1. Forbidden tracked directories
        for forbidden_dir in FORBIDDEN_TRACKED_DIRS:
            if rel_lower.startswith(forbidden_dir):
                violations.append(
                    f"[FORBIDDEN_DIR] {rel}  — directory '{forbidden_dir}' "
                    f"must not be tracked"
                )
                break

        # 2. LaTeX auxiliary files
        if path.suffix.lower() in LATEX_AUX_EXTENSIONS:
            violations.append(
                f"[LATEX_AUX] {rel}  — LaTeX intermediate must not be tracked"
            )

        # 3. Non-redistributable Sprott originals
        if path.name.upper() in SPROTT_ORIGINALS:
            violations.append(
                f"[SPROTT_ORIGINAL] {rel}  — non-redistributable Sprott file"
            )

        # 4. Internal prompt patterns
        if INTERNAL_PROMPT_RE.match(path.name):
            violations.append(
                f"[INTERNAL_PROMPT] {rel}  — internal prompt/seed file must not be tracked"
            )

        # Skip binary files for text-based checks
        if _is_binary_ext(path):
            continue

        text = _read_text(path)
        if not text:
            continue

        # 5. Absolute user paths / file:/// links
        matches = ABSOLUTE_USER_PATH_RE.findall(text)
        if matches:
            unique = list(dict.fromkeys(matches))[:3]
            violations.append(
                f"[LOCAL_PATH] {rel}  — absolute/local path found: {unique}"
            )

        # 6. Secret patterns
        secret_match = SECRET_PATTERNS_RE.search(text)
        if secret_match:
            violations.append(
                f"[SECRET] {rel}  — potential secret at char "
                f"{secret_match.start()}: '{secret_match.group()[:40]}'"
            )

    # Report
    if violations:
        print("=" * 70)
        print("PUBLIC RELEASE AUDIT -- FAILED")
        print("=" * 70)
        for v in violations:
            print(f"  [FAIL] {v}")
        print(f"\nTotal violations: {len(violations)}")
        print("Fix these issues before publishing to OSF/JOSS.")
        return 1

    print("=" * 70)
    print("PUBLIC RELEASE AUDIT -- PASSED")
    print("=" * 70)
    print(f"  Checked {len(tracked)} tracked files. No violations found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_audit())

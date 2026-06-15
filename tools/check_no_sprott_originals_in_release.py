#!/usr/bin/env python3
import sys
from pathlib import Path

BANNED_FILES = {
    'BOOKFIGS.DIC', 'SELECTED.DIC', 'SPECIAL.DIC',
    'SADISK.ZIP', 'SA.EXE', 'SAWIN.EXE',
    'PROG28.BAS', 'PROG28QC.C', 'PROG28TC.CPP',
    'VBRUN200.DLL'
}

IGNORED_DIRS = {
    'external', '.git', '.venv', '.venv-build',
    '.venv-webengine', '__pycache__', '.pytest_cache',
    '.pytest_tmp', 'build'
}

def check_release_cleanliness() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[1]
    found_banned = []
    
    for path in repo_root.rglob('*'):
        if path.is_dir():
            continue
        
        try:
            relative = path.relative_to(repo_root)
        except ValueError:
            continue
            
        parts = relative.parts
        # If any part of the path is in the ignored directories, skip
        if any(p in IGNORED_DIRS for p in parts[:-1]):
            continue
            
        if path.name.upper() in BANNED_FILES:
            found_banned.append(path)
            
    return found_banned

def main():
    found = check_release_cleanliness()
    if found:
        print("CRITICAL: Found Sprott original files in the release path or repo root:")
        for fb in found:
            print(f"  - {fb}")
        print("Please remove these files from the release path. They are prohibited from public distribution.")
        sys.exit(1)
        
    print("Sprott release verification: OK. No original files found in release directories.")
    sys.exit(0)

if __name__ == '__main__':
    main()

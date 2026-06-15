from __future__ import annotations

from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
BUNDLED = ROOT / 'resources' / 'bundled'

DOC_SOURCES = {
    ROOT / 'assets' / 'chaos_dictionary.pdf': BUNDLED / 'docs' / 'chaos_dictionary.pdf',
    ROOT / 'assets' / 'sprott' / 'sprott_theory.pdf': BUNDLED / 'docs' / 'sprott_theory.pdf',
    ROOT / 'assets' / 'sprott' / 'sprott_explorer_guide.pdf': BUNDLED / 'docs' / 'sprott_explorer_guide.pdf',
}

SPROTT_FILES = [
    'README.md',
    'attribution.md',
    'code_grammar.md',
    'theory_intro.md',
]

SPROTT_DIRS = [
    'theory',
    'examples',
    'images',
]

DATA_FILES = [
    ROOT / 'data' / 'coexisting_attractors.yaml',
    ROOT / 'data' / 'systems' / 'wang_2021_systems.yaml',
    ROOT / 'data' / 'wang2021' / 'ch01_introduccion.yaml',
    ROOT / 'data' / 'wang2021' / 'ch01_introduccion.md',
]

FORBIDDEN_SUFFIXES = {
    '.tex', '.aux', '.log', '.out', '.toc', '.bbl', '.blg',
    '.fls', '.fdb_latexmk', '.synctex.gz',
}


def _safe_clear(path: Path) -> None:
    full = path.resolve()
    root = ROOT.resolve()
    if root not in full.parents and full != root:
        raise RuntimeError(f'Refusing to clear path outside repository: {full}')
    if path.exists():
        shutil.rmtree(path)


def _copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f'Required runtime resource not found: {src}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _ignore_for_runtime(_directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        lower = name.lower()
        if lower in {'__pycache__', 'build', 'src'}:
            ignored.add(name)
        if any(lower.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
            ignored.add(name)
    return ignored


def prepare() -> Path:
    _safe_clear(BUNDLED)
    (BUNDLED / 'docs').mkdir(parents=True, exist_ok=True)
    (BUNDLED / 'icons').mkdir(parents=True, exist_ok=True)

    for source, target in DOC_SOURCES.items():
        _copy_file(source, target)

    sprott_source = ROOT / 'assets' / 'sprott'
    sprott_target = BUNDLED / 'sprott'
    sprott_target.mkdir(parents=True, exist_ok=True)
    for rel in SPROTT_FILES:
        source = sprott_source / rel
        if source.exists():
            _copy_file(source, sprott_target / rel)
    for rel in SPROTT_DIRS:
        source = sprott_source / rel
        if source.exists():
            shutil.copytree(source, sprott_target / rel, ignore=_ignore_for_runtime)

    for source in DATA_FILES:
        if source.exists():
            _copy_file(source, BUNDLED / 'data' / source.relative_to(ROOT / 'data'))

    icon_svg = BUNDLED / 'icons' / 'chaos-toolbox.svg'
    icon_svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">'
        '<rect width="128" height="128" rx="20" fill="#101820"/>'
        '<path d="M18 76c22-58 44 44 70-16 10-22 16-28 22-30" '
        'fill="none" stroke="#2dd4bf" stroke-width="8" stroke-linecap="round"/>'
        '<circle cx="34" cy="42" r="8" fill="#f7c948"/>'
        '<circle cx="88" cy="86" r="7" fill="#ef4444"/>'
        '</svg>',
        encoding='utf-8',
    )

    return BUNDLED


def main() -> int:
    target = prepare()
    print(f'Runtime resources prepared at {target}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

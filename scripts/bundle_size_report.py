from __future__ import annotations

from pathlib import Path
import argparse


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PATTERNS = (
    '*.tex', '*.aux', '*.log', '*.out', '*.toc', '*.bbl', '*.blg',
    '*.fls', '*.fdb_latexmk', '*.synctex.gz',
)
FORBIDDEN_DIR_NAMES = {'figures', 'images_source', 'build', 'src', '__pycache__'}


def fmt_size(size: int) -> str:
    value = float(size)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if value < 1024 or unit == 'GB':
            return f'{value:.1f} {unit}'
        value /= 1024
    return f'{value:.1f} GB'


def collect_files(target: Path) -> list[Path]:
    return [path for path in target.rglob('*') if path.is_file()]


def report(target: Path) -> str:
    files = collect_files(target)
    total = sum(path.stat().st_size for path in files)
    by_dir: dict[str, int] = {}
    for path in files:
        first = path.relative_to(target).parts[0]
        by_dir[first] = by_dir.get(first, 0) + path.stat().st_size

    lines = ['Bundle size report', f'Target: {target}', f'Total: {fmt_size(total)}', '']
    lines.append('Size by folder:')
    for name, size in sorted(by_dir.items(), key=lambda item: item[1], reverse=True):
        lines.append(f'- {name}: {fmt_size(size)}')

    lines.append('')
    lines.append('Largest files:')
    for index, path in enumerate(sorted(files, key=lambda p: p.stat().st_size, reverse=True)[:20], start=1):
        lines.append(f'{index}. {path.relative_to(target)} - {fmt_size(path.stat().st_size)}')

    lines.append('')
    pdfs = [path.relative_to(target) for path in files if path.suffix.lower() == '.pdf']
    lines.append('PDFs included:')
    lines.extend(f'- {pdf}' for pdf in pdfs)

    forbidden_files = []
    for pattern in FORBIDDEN_PATTERNS:
        forbidden_files.extend(target.rglob(pattern))
    forbidden_dirs = [
        path for path in target.rglob('*')
        if path.is_dir() and path.name.lower() in FORBIDDEN_DIR_NAMES
    ]
    lines.append('')
    lines.append('Forbidden content scan:')
    lines.append('No LaTeX/source auxiliary files found in bundle.' if not forbidden_files else 'Forbidden files found:')
    lines.extend(f'- {path.relative_to(target)}' for path in forbidden_files)
    lines.append('No source figure/build folders found in bundle.' if not forbidden_dirs else 'Forbidden folders found:')
    lines.extend(f'- {path.relative_to(target)}' for path in forbidden_dirs)
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('target', nargs='?', default=str(ROOT / 'resources' / 'bundled'))
    args = parser.parse_args()
    target = Path(args.target)
    if not target.exists():
        raise SystemExit(f'Bundle target does not exist: {target}')
    print(report(target))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

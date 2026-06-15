from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper' / 'paper.md'
BIB = ROOT / 'paper' / 'paper.bib'
CITATION = ROOT / 'CITATION.cff'
LICENSE = ROOT / 'LICENSE'
ARCHIVING = ROOT / 'docs' / 'release_archiving.md'
MANIFEST = ROOT / 'docs' / 'osf_archive_manifest.md'

REQUIRED_SECTIONS = [
    'Summary',
    'Statement of need',
    'State of the field',
    'Software design',
    'Research impact statement',
    'AI usage disclosure',
    'Acknowledgements',
    'References',
]


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _read(path: Path) -> str:
    _check(path.exists(), f'Missing required file: {path}')
    return path.read_text(encoding='utf-8')


def _bib_keys(bib_text: str) -> set[str]:
    keys = set(re.findall(r'@\w+\s*\{\s*([^,\s]+)', bib_text))
    _check(keys, 'paper.bib does not contain BibTeX entries.')
    _check(bib_text.count('{') == bib_text.count('}'), 'paper.bib has unbalanced braces.')
    return keys


def main() -> int:
    license_text = _read(LICENSE)
    _check('MIT License' in license_text, 'LICENSE is not MIT.')
    _check('Permission is hereby granted' in license_text, 'LICENSE does not contain the MIT grant text.')

    citation = _read(CITATION)
    _check('cff-version: 1.2.0' in citation, 'CITATION.cff must declare cff-version 1.2.0.')
    _check('repository-code: "https://github.com/Xerkkun/toolbox-chaos"' in citation, 'CITATION.cff must include repository-code.')
    _check('doi:' not in citation.lower(), 'CITATION.cff must not include a DOI before archival release.')

    paper = _read(PAPER)
    bib = _read(BIB)
    archiving = _read(ARCHIVING)
    manifest = _read(MANIFEST)
    for section in REQUIRED_SECTIONS:
        _check(f'# {section}' in paper, f'paper.md missing required JOSS section: {section}')
    _check('archive_doi' not in paper.lower(), 'paper.md must not include archive_doi before archival release.')
    _check(not re.search(r'10\.\d{4,9}/\S+', paper), 'paper.md should not contain inline DOI strings.')
    _check('OSF' in paper and 'DOI is pending' in paper, 'paper.md must state that the OSF archive DOI is pending.')
    _check('Generative AI tools' in paper, 'AI usage disclosure must explicitly disclose generative AI assistance.')
    _check('author reviewed and edited' in paper, 'AI usage disclosure must state human review of AI-assisted outputs.')
    _check('Zenodo' not in archiving, 'release_archiving.md must describe OSF, not Zenodo, as the archival DOI path.')
    _check('OSF Registration' in archiving, 'release_archiving.md must include OSF Registration steps.')
    for required in ('LICENSE', 'CITATION.cff', 'README.md', 'paper/paper.md', 'paper/paper.bib', 'pyproject.toml', 'tests/', 'docs/', 'examples/'):
        _check(required in manifest, f'OSF archive manifest missing required entry: {required}')

    keys = _bib_keys(bib)
    cited = set()
    for citation_group in re.findall(r'@([A-Za-z0-9_:-]+)', paper):
        cited.add(citation_group)
    _check(cited, 'paper.md does not cite paper.bib entries.')
    missing = sorted(cited - keys)
    _check(not missing, f'paper.md cites missing BibTeX keys: {missing}')

    word_count = len(re.findall(r'\b\w+\b', re.sub(r'^---.*?---', '', paper, flags=re.DOTALL)))
    _check(750 <= word_count <= 1750, f'JOSS paper word count should be 750-1750 words; found {word_count}.')

    print(f'JOSS metadata verification OK ({word_count} words, {len(keys)} references).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

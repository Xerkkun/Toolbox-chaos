# OSF Archive Manifest

Fyskode Chaotic Systems Toolbox 0.1.0 is developed by Maria Fernanda Moreno Lopez (Fer Moreno) and distributed under the MIT License.

This manifest describes the source-release contents intended for a frozen OSF archive used for a JOSS submission. No DOI has been assigned yet; the OSF DOI is pending until the OSF Registration is created.

## Include

Required metadata and paper files:

- `LICENSE`
- `CITATION.cff`
- `README.md`
- `CHANGELOG.md`
- `RELEASE_NOTES.md`
- `NOTICE.md`
- `AUTHORS.md`
- `pyproject.toml`
- `paper/paper.md`
- `paper/paper.bib`

Source code and project files:

- `src/` if the project is reorganized into a standard source-layout package before the archived release.
- `main.py`
- `core/`
- `ui/`
- `scripts/`
- `tools/`
- `data/`
- `packaging/`
- `docs/`
- `tests/`
- `examples/`

Source-layout compatibility note:

- For version 0.1.0, the source roots are `main.py`, `core/`, and `ui/`, not `src/`.

Minimal reproducibility files:

- `requirements.txt`
- `requirements-build.txt`
- `run.ps1`
- `run-linux.sh`
- `run-macos.command`
- `docs/installation.md`
- `docs/user-guide.md`
- `docs/packaging.md`
- `docs/release.md`
- `docs/release_archiving.md`
- `docs/distribution_policy.md`
- `examples/README.md`

Runtime resources:

- `resources/bundled/docs/*.pdf` only when those PDFs are required for the packaged UI.
- `resources/bundled/sprott/` only for redistributable educational runtime files.
- `resources/user/.gitkeep` as a placeholder only; do not include user-private resources.

## Exclude

Exclude heavy, generated, private, or non-reproducible files:

- `.git/`
- `.github/` only if OSF archive policy requires a minimal source archive without CI files; otherwise it may be included for review context.
- `.venv/`, `.venv-build/`, `.venv-webengine/`, `venv/`, `env/`
- `__pycache__/`, `.pytest_cache/`, `.pytest_tmp/`, `.mypy_cache/`, `.ruff_cache/`
- `build/`, `dist/`, `installer/`, `release/`
- Generated installers and previous package artifacts (`installer/*.exe`, `installer/*.msi`, `installer/*.zip`)
- Temporary upload/download folders such as `.tmp.driveupload/` and `.tmp.drivedownload/`
- LaTeX intermediates: `*.aux`, `*.log`, `*.out`, `*.toc`, `*.bbl`, `*.blg`, `*.fls`, `*.fdb_latexmk`, `*.synctex.gz`
- Intermediate `.tex` sources and source-only figure folders unless they are explicitly needed for reproducibility review
- Duplicate outputs and generated plots not needed for a minimal example

**Internal working files (never redistributed):**

- `reports/` — internal render-validation reports and rendered PNG pages
- `sources/` — entire directory including all source-extraction material
- `prompt_codex_*.md` — internal LLM extraction prompts at repository root
- `registro_sistemas_wang2021_seed.md` — internal data-seeding draft
- `docs/sources/` — local developer progress logs and private notes

**Non-redistributable copyrighted material:**

- `sources/Wang - 2021 - Chaotic Systems with Multistability and Hidden Attractors.pdf`
  — commercial publication; not redistributable under any license
- Original Sprott book-disk files: `BOOKFIGS.DIC`, `SELECTED.DIC`, `SPECIAL.DIC`,
  `SADISK.ZIP`, `SA.EXE`, `SAWIN.EXE`, `PROG28.BAS`, `PROG28QC.C`,
  `PROG28TC.CPP`, `VBRUN200.DLL`
- Any other commercial PDF, book, or copyrighted dataset not authored by the project

**Local machine resources:**

- Absolute paths referencing the development machine (Windows, Linux, and macOS user-home directories)
- Local file-URI links (file-colon-slash-slash-slash) in any tracked document
- Private configuration or credential files (`.env`, `*.pem`, `*.key`)

## Repository And Archive Roles

GitHub is the active repository for JOSS review, source code, issues, tests, development history, and future releases.

OSF is the persistent archive for the frozen version submitted to JOSS. The OSF archive DOI must be added only after OSF assigns it.

Numerical results are computational evidence, not automatic mathematical proof.


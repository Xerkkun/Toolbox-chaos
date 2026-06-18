# JOSS Submission Readiness Checklist

This checklist tracks the compliance of the **Fyskode Chaotic Systems Toolbox** repository with the Journal of Open Source Software (JOSS) submission requirements.

## JOSS Readiness Checklist

- [x] **License Present:** `LICENSE` file contains the full MIT Grant text and author attribution.
- [x] **CITATION.cff Present:** Includes version `0.1.0`, correct date-released, authors (Maria Fernanda Moreno Lopez), repo URL, and the active OSF DOI.
- [x] **DOI OSF Assigned:** Frozen source release is archived with the persistent OSF archive DOI `10.17605/OSF.IO/GQMJR`.
- [x] **JOSS Paper (paper.md) Present:** Located under `paper/paper.md` containing all required JOSS sections.
- [x] **Bibliography (paper.bib) Present:** Located under `paper/paper.bib` containing BibTeX entries matching all citations in `paper.md`.
- [x] **JOSS Word Count Verification:** JOSS paper contains between 750 and 1750 words (currently 1004 words).
- [x] **Installation Docs Present:** Detailed source installation and platform installers documented under `docs/installation.md` and `README.md`.
- [x] **Reviewer Guide Present:** Step-by-step instructions for JOSS reviewers created under `docs/reviewer-guide.md`.
- [x] **Contributing Guide Present:** Developer-focused contribution standards, test execution, branching conventions, and PR policies created under `CONTRIBUTING.md`.
- [x] **Changelog Present:** Project changelog `CHANGELOG.md` enriched with `v0.1.0` release features.
- [x] **Tests Documented:** Instructions for running unit tests locally and under headless CI environments included.
- [x] **Reproducible Examples Documented:** GUI workflows for simulations, exponent calculation, and bifurcation diagrams detailed under `docs/reproducible-examples.md`.
- [x] **Desktop Installer Documented:** Windows installer (`.exe`) compilation process with Inno Setup documented.
- [x] **macOS/Linux Packaging Status Documented:** Availability of PyInstaller packaging scripts in `scripts/` and the host-generation requirement documented in `docs/packaging.md`.
- [x] **No Protected Sprott Assets:** Repository is pure and contains no copyrighted dictionary databases (`.DIC`), book figures, or executables. Checked by `verify_public_release_clean.py`.
- [x] **Mathematical Limitations Disclosed:** Explicit warnings documenting that numerical results (Lyapunov exponents, basins, etc.) serve as computational evidence and not mathematical proofs are placed in README, paper, and guides.
- [x] **CI Configuration:** Automated tests and metadata integrity verification set up in `.github/workflows/ci.yml`.

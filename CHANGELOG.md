# Changelog

All notable changes to Chaos Toolbox are documented here. The project follows semantic versioning: `MAJOR.MINOR.PATCH`.

## [0.1.0] - 2026-06-14

### Added

- PyQt6 desktop application packaging metadata with `pyproject.toml` as the version source of truth.
- MIT license, author metadata, citation metadata, notice file, and release notes.
- Help menu with local documentation, results folder, manual update check, automatic update toggle, and About dialog.
- Runtime resource resolver for source and packaged execution.
- Whitelist-based runtime resource bundle under `resources/bundled`.
- PyInstaller/Inno Setup packaging path for Windows and documented macOS/Linux packaging stubs.
- Packaging verification and bundle size report scripts.

### Changed

- PyInstaller packaging now uses prepared runtime resources instead of packaging the full `assets/` source tree.

### Security

- Public release checks continue to reject original Sprott book disk files and now also reject LaTeX source/auxiliary files in the runtime bundle.

# Changelog

All notable changes to Fyskode Chaotic Systems Toolbox are documented here. The project follows semantic versioning: `MAJOR.MINOR.PATCH`.

## [0.1.0] - 2026-06-14

### Added

- PyQt6 desktop application for simulating, analyzing, and visualizing chaotic dynamical systems.
- Closed, registry-backed catalog of classical chaotic systems (Lorenz, Rossler, Chua, Chen, Henon, etc.).
- Visualization features: 3D/2D phase space trajectories, time series plots, and equilibrium points.
- Numerical diagnostics: Lyapunov exponent estimation, Fast Fourier Transform (FFT) spectra, bifurcation sweeps, and coexisting attractors basins where supported.
- Sprott Explorer educational module to load and recreate local `.DIC` files without redistributing copyrighted assets.
- PDF dictionary viewer integrated directly in the UI help menu.
- PyQt6 desktop application packaging metadata with `pyproject.toml` as the version source of truth.
- MIT license, author metadata, citation metadata (archived OSF DOI `10.17605/OSF.IO/GQMJR`), notice file, and release notes.
- Help menu with local documentation, results folder, manual update check, automatic update toggle, and About dialog.
- Runtime resource resolver for source and packaged execution.
- Whitelist-based runtime resource bundle under `resources/bundled`.
- PyInstaller/Inno Setup packaging pipeline for Windows (.exe installer) and prepared macOS/Linux packaging shell scripts.
- Packaging verification, public release cleanliness validation, and bundle size report scripts.

### Changed

- PyInstaller packaging now uses prepared runtime resources instead of packaging the full `assets/` source tree.

### Security

- Public release checks continue to reject original Sprott book disk files and now also reject LaTeX source/auxiliary files in the runtime bundle.

# Changelog

All notable changes to Fyskode Chaotic Systems Toolbox are documented here. The project follows semantic versioning: `MAJOR.MINOR.PATCH`.

## 0.2.0 - 2026-08-28

### Added

- Integrated stable-release updater with semantic-version comparison, release
  notes, platform-specific installer selection, atomic download, consolidated
  `SHA256SUMS` verification, and explicit confirmation before launch.
- Release-workflow checksum manifest for the exact GitHub Release asset names.

### Security

- Reject draft/prerelease metadata, unsafe asset names, unapproved download
  hosts and redirects, oversized responses, checksum mismatches, and installers
  modified between download and launch.

## Added

- PySide6 desktop application for simulating, analyzing, and visualizing chaotic dynamical systems.
- Closed, registry-backed catalog of classical chaotic systems (Lorenz, Rossler, Chua, Chen, Henon, etc.).
- Numerical diagnostics: Lyapunov exponent estimation, Fast Fourier Transform (FFT) spectra, bifurcation sweeps, and coexisting attractors basins where supported.
- Sprott Explorer educational module to load and recreate local `.DIC` files without redistributing copyrighted assets.
- Integrated PDF dictionary viewer for exploring system equations and theory.
- Help menu with local documentation, results folder, update checks, and automatic update settings.
- Platform packaging support for Windows distribution via executables and desktop installers.

## Changed

- Packaging configuration with an explicit allowlist of runtime resources.

## Fixed

- Re-aligned internal path resolution to support relative installation paths.

## Notes

- Public releases strictly exclude original copyrighted database files, book figures, or historical binaries.


# Changelog

All notable changes to Fyskode Chaotic Systems Toolbox are documented here. The project follows semantic versioning: `MAJOR.MINOR.PATCH`.

## Added

- PyQt6 desktop application for simulating, analyzing, and visualizing chaotic dynamical systems.
- Closed, registry-backed catalog of classical chaotic systems (Lorenz, Rossler, Chua, Chen, Henon, etc.).
- Numerical diagnostics: Lyapunov exponent estimation, Fast Fourier Transform (FFT) spectra, bifurcation sweeps, and coexisting attractors basins where supported.
- Sprott Explorer educational module to load and recreate local `.DIC` files without redistributing copyrighted assets.
- Integrated PDF dictionary viewer for exploring system equations and theory.
- Help menu with local documentation, results folder, update checks, and automatic update settings.
- Platform packaging support for Windows distribution via executables and desktop installers.

## Changed

- Optimized packaging configuration to build compact, whitelist-based runtime resource bundles.

## Fixed

- Re-aligned internal path resolution to support relative installation paths.

## Notes

- Public releases strictly exclude original copyrighted database files, book figures, or historical binaries.


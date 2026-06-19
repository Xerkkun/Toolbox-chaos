# Release Notes - Fyskode Chaotic Systems Toolbox 0.1.0

Fyskode Chaotic Systems Toolbox is a PyQt6 desktop application for simulating, analyzing, and exploring chaotic dynamical systems.

## Added
- Closed, registry-backed catalog of classical chaotic systems.
- 2D and 3D trajectory rendering.
- Numerical diagnostics: Lyapunov exponent estimation, Fast Fourier Transform (FFT) spectra, bifurcation sweeps, and coexisting attractors basins where supported.
- Sprott Explorer loader to parse and study local `.DIC` files.
- Integrated PDF dictionary viewer and updater interface.

## Changed
- Optimized build script to assemble a compact runtime bundle under `resources/bundled`.

## Fixed
- Path resolution for relative executables.

## Notes
- Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.
- Sprott Explorer operates locally at runtime and does not bundle or redistribute any copyrighted dictionaries, book figures, or executables.

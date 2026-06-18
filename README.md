# Fyskode Chaotic Systems Toolbox

Fyskode Chaotic Systems Toolbox 0.1.0 is a PyQt6 desktop toolbox for chaotic systems, numerical analysis, visualization, and attractor exploration. It is developed and maintained by Maria Fernanda Moreno Lopez (Fer Moreno) and distributed under the MIT License.

Numerical results produced by the application are computational evidence and not automatic mathematical proof.

## Desktop App

The app includes trajectory projections, time series, 3D attractor views, bifurcation diagrams, equilibrium/eigenvalue views, attraction-basin grids where supported, FFT, Lyapunov diagnostics, coexistence examples, a PDF dictionary, and the Sprott Explorer.

Supported families include Lorenz, Rossler, Chua, Chen, Lu, Duffing-Ueda, Rabinovich-Fabrikant, Rikitake, Sprott systems, Thomas, Hindmarsh-Rose, Henon, logistic, Ikeda, Mackey-Glass, Lorenz-96, and related registry-backed systems.

This version uses a closed catalog of systems supported by the toolbox and numerical backend. Users can modify parameters, initial conditions, and visualization options for available systems, but cannot register arbitrary new dynamical systems from the main UI. Future custom-system support is documented in `docs/custom_systems_future.md`.

## Research Use

Fyskode Chaotic Systems Toolbox is used as a numerical and visual aid in research and education workflows for chaotic dynamical systems. The platform supports:
- **Phase Portraits & Trajectories**: 2D and 3D visualization of trajectories under customizable initial conditions and integration parameters.
- **Time Series & FFT**: Extraction of dynamics and spectral density analysis via Fast Fourier Transform.
- **Lyapunov Diagnostics**: Numerical estimation of the spectrum of Lyapunov exponents to evaluate dynamic complexity and sensitivity to initial conditions.
- **Bifurcation Sweeps**: Sweep-screening of one-dimensional parameter spaces to reveal routes to chaos.
- **Attraction Basins**: Visual identification of coexisting attractors and multistability basins where supported.

All numerical outputs serve as computational evidence and do not represent formal mathematical certification.

## Sprott Explorer Scope

The Sprott Explorer is an educational module designed to modernize the exploration of chaotic equations and historical dictionaries published by J. C. Sprott. It operates under a strict distribution policy:
- **No Redistribution**: The software does not package or distribute original copyrighted disk files, dictionary databases (`.DIC`), book figures, or proprietary code.
- **Local Exploration**: Users can import local `.DIC` files at runtime for personal study. These files are processed locally and are never copied or persisted in the toolbox catalog.

## Public Release Policy

Public releases do not redistribute original Sprott book disk files, dictionaries, executables, source code, figures, or long book text. User-owned `.DIC` files can be selected locally at runtime and remain outside the repository and installer. See `docs/distribution_policy.md`.

The Sprott Explorer `.DIC` loader is an exception for personal local exploration. It does not register a new complete system in the main toolbox, and local `.DIC` files are not copied into the installed package.

For executable distributions, the package does not include the complete LaTeX project. It includes only final PDFs required by the UI under `resources/bundled/docs`. `.tex` files, build images, auxiliary files, intermediate figures, generated outputs, and private resources are excluded.

## Install From Source

```powershell
python -m pip install -r requirements.txt
python main.py
```

Windows helper:

```powershell
.\run.ps1
```

Linux/macOS helpers:

```bash
./run-linux.sh
./run-macos.command
```

## Build And Package

Prepare runtime resources and verify packaging:

```powershell
python scripts\prepare_runtime_resources.py
python scripts\verify_packaging.py
python scripts\bundle_size_report.py
```

Build Windows executable and installer:

```powershell
# Build both executable and installer (default)
.\scripts\build_windows.ps1

# Build executable only (PyInstaller)
.\scripts\build_windows.ps1 -AppOnly

# Build installer only (Inno Setup from existing dist/)
.\scripts\build_windows.ps1 -InstallerOnly
```

Build on macOS or Linux from those systems:

```bash
./scripts/build_macos.sh
./scripts/build_linux.sh
```

Expected artifact names and directories:

- Executable folder: `dist/Chaos Toolbox/Chaos Toolbox.exe`
- Installer file: `installer/chaos-toolbox-v0.1.0-windows-x64-setup.exe`
- Old installers are archived to `installer/archive/` during building.
- `chaos-toolbox-v0.1.0-macos-arm64.dmg`
- `chaos-toolbox-v0.1.0-linux-x64.AppImage`

Windows packaging uses PyInstaller plus Inno Setup. Stale or older installers are archived to prevent confusion. The primary executable distribution is currently compiled for Windows as an installer (`.exe`). macOS and Linux build/packaging scripts are prepared in `scripts/`, but the final distribution packages (such as `.dmg` or AppImage) must be generated on their respective host platforms before publication. Details are in `docs/packaging.md`.

## Updates

Installed builds support assisted update checks through `Ayuda > Buscar actualizaciones`. Automatic checks are non-blocking, weekly by default, and can be disabled from `Ayuda > Revisar actualizaciones automaticamente`.

Set a controlled releases endpoint before publishing:

```powershell
$env:CHAOS_TOOLBOX_RELEASES_API_URL="https://api.github.com/repos/OWNER/REPO/releases/latest"
```

The app never installs updates silently. It shows installed version, available version, publication date, release summary, release notes, and a download action when a platform artifact is available.

## Citation And JOSS Preparation

The Fyskode Chaotic Systems Toolbox version 0.1.0 is archived on the Open Science Framework (OSF) with persistent DOI [10.17605/OSF.IO/GQMJR](https://doi.org/10.17605/OSF.IO/GQMJR). Citation metadata is available in `CITATION.cff`. A draft JOSS software paper is prepared in `paper/paper.md` with references in `paper/paper.bib`. GitHub is the active repository for review, issues, source code, tests, and development; OSF is the persistent archive for the frozen release snapshot. See `docs/project_identity.md` for a summary of author identity, brand, and pseudonym conventions.

## Documentation

- `docs/installation.md`
- `docs/user-guide.md`
- `docs/packaging.md`
- `docs/release.md`
- `docs/troubleshooting.md`
- `docs/versioning.md`
- `docs/license.md`
- `docs/updates.md`
- `docs/custom_systems_future.md`

## Project Structure

- `main.py`: application entry point and startup logging.
- `ui/`: PyQt6 interface, canvases, tabs, PDF viewer, and update/About menu wiring.
- `core/`: numerical routines, native backend integration, metadata, resource paths, and update checker.
- `core/csrc/chaos_core.c`: native C backend source.
- `resources/bundled/`: runtime whitelist for packaged builds.
- `resources/user/`: user/private resources, ignored by Git except for `.gitkeep`.
- `assets/`: source educational/reference assets used to generate final runtime resources.
- `packaging/`: PyInstaller and Inno Setup configuration.
- `scripts/`: packaging, verification, and size-report scripts.

## License

Fyskode Chaotic Systems Toolbox 0.1.0 is licensed under the MIT License. Developer and maintainer: Maria Fernanda Moreno Lopez (Fer Moreno). Project brand: Fyskode. GitHub username: Xerkkun.

# Chaos Toolbox

Chaos Toolbox 0.1.0 is a PyQt6 desktop toolbox for chaotic systems, numerical analysis, visualization, and attractor exploration. It is developed by Fer Moreno and distributed under the MIT License.

Numerical results produced by the application are computational evidence and not automatic mathematical proof.

## Desktop App

The app includes trajectory projections, time series, 3D attractor views, bifurcation diagrams, equilibrium/eigenvalue views, attraction-basin grids where supported, FFT, Lyapunov diagnostics, coexistence examples, a PDF dictionary, and the Sprott Explorer.

Supported families include Lorenz, Rossler, Chua, Chen, Lu, Duffing-Ueda, Rabinovich-Fabrikant, Rikitake, Sprott systems, Thomas, Hindmarsh-Rose, Henon, logistic, Ikeda, Mackey-Glass, Lorenz-96, and related registry-backed systems.

This version uses a closed catalog of systems supported by the toolbox and numerical backend. Users can modify parameters, initial conditions, and visualization options for available systems, but cannot register arbitrary new dynamical systems from the main UI. Future custom-system support is documented in `docs/custom_systems_future.md`.

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

Build Windows executable and installer inputs:

```powershell
.\scripts\build_windows.ps1
```

Build on macOS or Linux from those systems:

```bash
./scripts/build_macos.sh
./scripts/build_linux.sh
```

Expected artifact names:

- `chaos-toolbox-v0.1.0-windows-x64-setup.exe`
- `chaos-toolbox-v0.1.0-macos-arm64.dmg`
- `chaos-toolbox-v0.1.0-linux-x64.AppImage`

Windows packaging uses PyInstaller plus Inno Setup. macOS and Linux PyInstaller builds are prepared, while `.dmg`, AppImage, `.deb`, and `.rpm` publication require platform tools documented in `docs/packaging.md`.

## Updates

Installed builds support assisted update checks through `Ayuda > Buscar actualizaciones`. Automatic checks are non-blocking, weekly by default, and can be disabled from `Ayuda > Revisar actualizaciones automaticamente`.

Set a controlled releases endpoint before publishing:

```powershell
$env:CHAOS_TOOLBOX_RELEASES_API_URL="https://api.github.com/repos/OWNER/REPO/releases/latest"
```

The app never installs updates silently. It shows installed version, available version, publication date, release summary, release notes, and a download action when a platform artifact is available.

## Citation And JOSS Preparation

Citation metadata is available in `CITATION.cff`. A draft JOSS software paper is prepared in `paper/paper.md` with references in `paper/paper.bib`. No DOI has been assigned to the software archive yet. GitHub is the active repository for review, issues, source code, tests, and development; OSF is planned as the persistent archive for the frozen release snapshot and DOI.

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

Chaos Toolbox 0.1.0 is licensed under the MIT License. Developer: Fer Moreno.

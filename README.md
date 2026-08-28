# Fyskode Chaotic Systems Toolbox

Fyskode Chaotic Systems Toolbox version 0.2.0 is a PySide6 desktop application
for exploring chaotic dynamical systems through numerical simulation,
visualization, and diagnostic analysis. It is developed and maintained by
Maria Fernanda Moreno Lopez (Fer Moreno). Its own source code is distributed
under MIT; PySide6/Qt and other dependencies retain their separate licenses.

Version 0.2.0 is the stable release dated 2026-08-28. The project retains its
existing OSF project DOI; no new version-specific DOI is assigned.


## Features

- **Phase Space Visualization**: 2D and 3D trajectory rendering.
- **Time Series & Spectra**: Time-series views, physical amplitude spectra, and one-sided Welch power spectral densities.
- **Lyapunov Exponents**: Finite-time QR--Benettin spectrum estimates for registered three-dimensional integer-order flows.
- **Bifurcation Sweeps**: Sweep-screening of parameter spaces to trace routes to chaos.
- **Attraction Basins**: Grid-sweeping initial conditions to identify coexisting attractors.
- **Sprott Explorer**: Parser/loader for personal study of historical dictionary files.
- **No-code System Editor**: Safe expression-based definition, validation, JSON exchange, simulation, and plotting of flows and maps through Hidden Attractors FO.
- **Updates & PDF Dictionary**: Assisted checks for updates and an integrated PDF viewer.

## Supported Systems

Supported families include Lorenz, Rossler, Chua, Chen, Lu, Wang--Chen,
Nazarimehr's line-equilibrium flow, Duffing-Ueda, Rabinovich-Fabrikant,
Rikitake, Sprott systems, Thomas, Hindmarsh-Rose, Henon, logistic, Ikeda,
Mackey-Glass, Lorenz-96, and related registry-backed systems.

The Wang--Chen and Nazarimehr entries include published basin presets and
coexisting-attractor initial conditions. They are available in the general
system selector and in the coexistence workflow.

## Scientific Scope

Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.

The `Crear sistema` tab accepts variables, parameters, equations, and initial
conditions without Python code. A restricted expression parser rejects
imports, attributes, and arbitrary execution. These systems can be simulated
as flows or maps through the installed Hidden Attractors FO engine. The tab
generates trajectories and plots; advanced catalog diagnostics and a native
kernel are unavailable for custom definitions.

## Sprott Explorer Scope

- No original Sprott copyrighted disk files are bundled.
- No `.DIC` databases are redistributed.
- No book figures or proprietary executables are bundled.
- User-owned `.DIC` files can be loaded locally at runtime for personal exploration.
- Local files are not copied into the package, repository, or installer.

## Installation

Install from source with Python 3.11 or newer. This installs the compatible
Hidden Attractors FO engine declared by the project:
```powershell
python -m pip install .
chaos-toolbox
```

For the embedded HTML theory viewer, install the optional WebEngine component
with `python -m pip install ".[webengine]"`. The application otherwise uses its
plain-text Markdown viewer.

Helper starting scripts:
- Windows: `.\run.ps1`
- Linux: `./run-linux.sh`
- macOS: `./run-macos.command`

## Build and Package

Prepare runtime resources and verify packaging:
```powershell
python scripts\prepare_runtime_resources.py
python scripts\verify_packaging.py
python scripts\bundle_size_report.py
```

Build the Windows installer:
```powershell
.\scripts\build_windows.ps1
```

For macOS and Linux builds, use `./scripts/build_macos.sh` and `./scripts/build_linux.sh` respectively.

## Documentation

- [User Guide](docs/user-guide.md)
- [Installation](docs/installation.md)
- [Packaging](docs/packaging.md)
- [Distribution Policy](docs/distribution_policy.md)
- [Public Documentation Policy](docs/public_documentation_policy.md)


Documentation style and public-facing wording follow `docs/public_documentation_policy.md`.

## License and Citation

Fyskode Chaotic Systems Toolbox's own source code is licensed under MIT.
Binary distributions also contain separately licensed dependencies. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md),
[`docs/license.md`](docs/license.md), and the CycloneDX SBOM shipped with each
release.

Citation DOI: [10.17605/OSF.IO/GQMJR](https://doi.org/10.17605/OSF.IO/GQMJR). Refer to `CITATION.cff` for detailed academic citation metadata.

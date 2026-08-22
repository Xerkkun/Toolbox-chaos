# Packaging

Fyskode Chaotic Systems Toolbox 0.2.0 is developed by Maria Fernanda Moreno
Lopez (Fer Moreno). Its own source is MIT-licensed; dependencies retain their
separate license terms.

## Framework Choice

The real UI framework is Python desktop with PySide6. Packaging therefore uses PyInstaller for the desktop app bundle. Windows installation uses Inno Setup. macOS `.app`/`.dmg` and Linux AppImage/`.deb`/`.rpm` are documented platform builds around the PyInstaller output.

## Runtime Resource Policy

Packaging is whitelist-based. The executable bundle includes:

- application code;
- native runtime backend when available;
- strictly required Python runtime libraries collected by PyInstaller;
- PySide6-Addons as a base runtime dependency because QtSvg and QtPdf are used
  outside the optional WebEngine view;
- final PDFs in `resources/bundled/docs`;
- minimal Sprott Markdown, examples, thumbnails, and generated educational images required by the UI;
- default system data/configuration files;
- Sprott Explorer local-runtime loading: no original Sprott copyrighted disk files are bundled; no `.DIC` databases are redistributed; no book figures or proprietary executables are bundled; user-owned `.DIC` files can be loaded locally at runtime for personal exploration, and local files are not copied into the package or repository.
- project license, third-party notices, LGPLv3/GPLv3 texts, dependency
  metadata, authors, release notes, and minimal user docs.

The bundle excludes `.tex`, LaTeX auxiliary files, source figure folders used only for document compilation, tests, caches, development outputs, previous installers, private resources, and original Sprott protected files.


The source wheel installs the `chaos-toolbox` graphical entry point, the
versioned Hidden Attractors FO dependency, the Python packages and native C
source, runtime resources under `share/chaos-toolbox`, and the operable local
guides. The PyInstaller build explicitly collects only the supported Hidden
Attractors FO modules and recursively preserves installed metadata/licenses for
the full runtime dependency closure. The `Crear sistema` tab is included; its
trajectory-only scientific boundary is documented in `custom_systems.md`.

`python scripts/verify_hafo_release.py` is the public dependency gate. It must
find a published `hidden-attractors-fo>=1.1,<2` artifact before CI or a release
may proceed. HAFO 1.0 does not satisfy the runtime API contract; packaging does
not silently lower the requirement or import another source checkout.

Prepare resources:

```powershell
python scripts\prepare_runtime_resources.py
```

Report bundle size:

```powershell
python scripts\bundle_size_report.py
```

Verify package policy:

```powershell
python scripts\verify_packaging.py
python scripts\verify_distribution_compliance.py --check-installed --require-webengine
```

## License evidence and SBOM

The wheel and sdist carry the project license, `NOTICE.md`,
`THIRD_PARTY_NOTICES.md`, LGPLv3/GPLv3, and the Chromium/WebEngine notices as
installed data and package license files. PyInstaller collects the same files,
installed dependency metadata, the exact Python runtime license, the Qt/PySide
source and security manifests, and the required Qt WebEngine runtime resource.
Release CI executes a silent Windows install, mounts the DMG, and installs the
DEB in clean Ubuntu 24.04 before native self-test/first-paint validation.

The Python-distribution job generates a reproducible CycloneDX 1.6 SBOM from
the isolated wheel environment. Each native build also hashes every file in
its completed bundle into a separate CycloneDX SBOM, including the Python
runtime, Qt/Chromium resources, native libraries, and distribution metadata.
The compliance checker rejects a missing PySide6 component, pin drift, any
legacy Qt binding, altered notice, incomplete archive metadata, or bundle hash
mismatch. All `*.cdx.json` evidence is retained with its platform artifact.

Official binary builds also apply `requirements-release.txt`. It pins
PySide6-Essentials, PySide6-Addons, Shiboken6, HAFO, PyInstaller, and the
PyInstaller hook set; `requirements-bootstrap.txt` pins the official build pip.
This prevents silent drift of those reviewed components, while the platform
SBOM records the remaining resolved closure. It is not a claim of bit-for-bit
cross-platform reproducibility.
The public dependency ranges in `pyproject.toml` remain compatible ranges for
source installations; the release constraint is an artifact-build policy.

PyInstaller one-directory mode preserves Qt/PySide shared files separately.
See `license.md` for installation information for a coherent modified
PySide6/Qt build and the corresponding-source release policy.
QtSvg/Qt6Svg remain for direct renderer/generator use, under restricted global
parser options and a decoded-PNG-only input boundary. Optional QtSvgWidgets,
QtCore5Compat, QtXml, and Qt5Compat QML content are excluded and rejected by
artifact validation. The packaged security inventory records the residual
CVE-2026-8168 risk without claiming the PySide6 6.11.1 wheel is patched.

## Platform Builds

Windows:

Build both the executable and the installer:

```powershell
.\scripts\build_windows.ps1
```

Build the PyInstaller executable bundle only:

```powershell
.\scripts\build_windows.ps1 -AppOnly
```

Build the Inno Setup installer installer only (requires an existing `dist/Chaos Toolbox/` build):

```powershell
.\scripts\build_windows.ps1 -InstallerOnly
```

### Inno Setup Compiler Detection
The installer build process requires Inno Setup 6 (`ISCC.exe`). It is automatically detected in:
1. The path specified by the `$env:INNO_SETUP_ISCC` environment variable.
2. The system `PATH`.
3. User AppData location `%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`.
4. Standard location `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`.
5. Standard location `C:\Program Files\Inno Setup 6\ISCC.exe`.

If not found, a detailed message is displayed, the PyInstaller executable remains intact, and the script exits with an error code.

For commercial distribution, record the project's Inno Setup decision before
building the public installer. The author's official purchase page asks
commercial users to buy a license/support package, while the official FAQ
clarifies that a purchase is requested rather than a technical prerequisite.
This policy question is separate from the licenses of the application source
and its bundled dependencies. See
<https://jrsoftware.org/isorder.php> and <https://jrsoftware.org/isinfo.php>.

### Installer Archiving & Artifacts
- Main Executable: `dist/Chaos Toolbox/Chaos Toolbox.exe`
- Main Installer: `installer/chaos-toolbox-v0.2.0-windows-x64-setup.exe`
- Prior to compiling a new installer, all existing `*.exe` files in the `installer/` directory are moved to the `installer/archive/` folder.
- Stale installers with the old name format (e.g., `ChaosToolboxSetup-0.1.0.exe`) are considered obsolete and are automatically archived to prevent user confusion.

macOS:

```bash
./scripts/build_macos.sh
```

Build the `.dmg` from the generated `.app`. Signing and notarization require Apple Developer credentials.

Linux:

```bash
./scripts/build_linux.sh
```

Build AppImage from the PyInstaller output with AppImage tooling. `.deb` and `.rpm` publication require distro packaging tools and signing policy.

Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.


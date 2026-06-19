# Packaging

Fyskode Chaotic Systems Toolbox 0.1.0 is developed by Maria Fernanda Moreno Lopez (Fer Moreno) and distributed under the MIT License.

## Framework Choice

The real UI framework is Python desktop with PyQt6. Packaging therefore uses PyInstaller for the desktop app bundle. Windows installation uses Inno Setup. macOS `.app`/`.dmg` and Linux AppImage/`.deb`/`.rpm` are documented platform builds around the PyInstaller output.

## Runtime Resource Policy

Packaging is whitelist-based. The executable bundle includes:

- application code;
- native runtime backend when available;
- strictly required Python runtime libraries collected by PyInstaller;
- final PDFs in `resources/bundled/docs`;
- minimal Sprott Markdown, examples, thumbnails, and generated educational images required by the UI;
- default system data/configuration files;
- Sprott Explorer local-runtime loading: no original Sprott copyrighted disk files are bundled; no `.DIC` databases are redistributed; no book figures or proprietary executables are bundled; user-owned `.DIC` files can be loaded locally at runtime for personal exploration, and local files are not copied into the package or repository.
- license, notice, authors, release notes, and minimal user docs.

The bundle excludes `.tex`, LaTeX auxiliary files, source figure folders used only for document compilation, tests, caches, development outputs, previous installers, private resources, and original Sprott protected files.


Version 0.1.0 does not package or expose a user-facing system-registration framework for the main toolbox. The supported-system catalog is closed for this release; custom systems are planned for a future version.

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
```

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

### Installer Archiving & Artifacts
- Main Executable: `dist/Chaos Toolbox/Chaos Toolbox.exe`
- Main Installer: `installer/chaos-toolbox-v0.1.0-windows-x64-setup.exe`
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


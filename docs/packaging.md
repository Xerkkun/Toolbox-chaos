# Packaging

Chaos Toolbox 0.1.0 is developed by Fer Moreno and distributed under the MIT License.

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
- local `.DIC` loading support for the Sprott Explorer, without bundling user `.DIC` files;
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

```powershell
.\scripts\build_windows.ps1
```

Expected installer: `chaos-toolbox-v0.1.0-windows-x64-setup.exe`.

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

Numerical outputs are computational evidence, not automatic mathematical proof.

# Release Notes - Fyskode Chaotic Systems Toolbox 0.1.0

Fyskode Chaotic Systems Toolbox 0.1.0 prepares the PyQt6 desktop application for distributable builds.

Highlights:

- Developer: Maria Fernanda Moreno Lopez (Fer Moreno).
- License: MIT.
- Version source of truth: `pyproject.toml`.
- Packaging backend: PyInstaller for the Python/PyQt app; Inno Setup for the Windows installer.
- Runtime bundle: `resources/bundled`, with final PDFs and runtime data only.
- Update flow: assisted checks from GitHub Releases or another configured release API using `CHAOS_TOOLBOX_RELEASES_API_URL`.

Known manual steps:

- Windows code signing requires a signing certificate.
- macOS signing and notarization require Apple Developer credentials.
- Linux AppImage, `.deb`, and `.rpm` publication require platform-specific tooling and signing policy.

Academic warning: numerical results are computational evidence and not automatic mathematical proof.

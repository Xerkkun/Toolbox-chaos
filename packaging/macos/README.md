# macOS Packaging

Chaos Toolbox 0.2.0 uses PyInstaller to create a `.app` bundle on macOS.

Create the `.app` on a macOS build host:

```bash
./scripts/build_macos.sh
```

Then create a `.dmg` using local release tooling. A complete public macOS release requires Apple Developer signing and notarization credentials.

Developer: Maria Fernanda Moreno Lopez (Fer Moreno). The project's own source
is MIT-licensed. PySide6/Qt and other bundled dependencies retain their
separate licenses; the `.app` must include `THIRD_PARTY_NOTICES.md`, the
LGPLv3/GPLv3 texts, and dependency metadata.

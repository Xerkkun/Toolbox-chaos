# macOS Packaging

Chaos Toolbox 0.1.0 uses PyInstaller to create a `.app` bundle on macOS.

Create the `.app` on a macOS build host:

```bash
./scripts/build_macos.sh
```

Then create a `.dmg` using local release tooling. A complete public macOS release requires Apple Developer signing and notarization credentials.

Developer: Fer Moreno. License: MIT.

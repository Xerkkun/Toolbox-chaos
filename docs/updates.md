# Updates

Chaos Toolbox 0.1.0 is developed by Fer Moreno and distributed under the MIT License.

The installed app supports assisted update checks. It does not install updates silently.

## Manual Check

Use:

```text
Ayuda > Buscar actualizaciones
```

The dialog shows installed version, available version, publication date, release summary, release notes, and a download action when the release contains a matching platform artifact.

## Automatic Check

Automatic checks run in the background and do not block startup. The default frequency is weekly. Disable them from:

```text
Ayuda > Revisar actualizaciones automaticamente
```

If there is no internet, the app continues normally.

## Release Source

Configure a controlled latest-release endpoint:

```powershell
$env:CHAOS_TOOLBOX_RELEASES_API_URL="https://api.github.com/repos/OWNER/REPO/releases/latest"
```

Artifacts should follow:

- `chaos-toolbox-v0.1.0-windows-x64-setup.exe`
- `chaos-toolbox-v0.1.0-macos-arm64.dmg`
- `chaos-toolbox-v0.1.0-linux-x64.AppImage`

Windows installers are configured for installation over a previous version while preserving user configuration and generated results. macOS automatic replacement can require signing and notarization. Linux AppImage supports guided download; `.deb`/`.rpm` updates should use the system package manager when those packages are published.

Numerical results are computational evidence, not automatic mathematical proof.

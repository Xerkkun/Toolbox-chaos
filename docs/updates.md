# Updates

Fyskode Chaotic Systems Toolbox 0.1.0 is developed by Maria Fernanda Moreno Lopez (Fer Moreno) and distributed under the MIT License.

The installed app supports assisted update checks. It does not install updates silently.

The updater accepts only HTTPS GitHub API and release hosts, validates
redirects, and limits metadata size. This reduces accidental or malicious link
substitution, but version 0.1.0 does not cryptographically verify a downloaded
installer or platform package. Before running it, confirm that the URL is the official
GitHub Release and compare a publisher-provided checksum when one is available.

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

A clean installation uses the official latest-release endpoint:

```text
https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest
```

A controlled deployment can override it with:

```powershell
$env:CHAOS_TOOLBOX_RELEASES_API_URL="https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest"
```

Artifacts should follow:

- `chaos-toolbox-v0.1.0-windows-x64-setup.exe`
- `chaos-toolbox-v0.1.0-macos-arm64.dmg`
- `chaos-toolbox-v0.1.0-linux-x64.deb`

Windows installers are configured for installation over a previous version while preserving user configuration and generated results. macOS automatic replacement can require signing and notarization. The automated Linux release artifact is a `.deb`; the updater can guide its download, and installation should use the system package manager.

Numerical results are computational evidence, not automatic mathematical proof.

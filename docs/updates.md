# Updates

Fyskode Chaotic Systems Toolbox is developed by Maria Fernanda Moreno Lopez
(Fer Moreno) and distributed under the MIT License.

The application checks only the latest stable GitHub Release. Drafts,
prereleases, and non-semantic tags are rejected. An update is never downloaded
or installed silently.

## Manual Check

Use:

```text
Ayuda > Buscar actualizaciones
```

The dialog reports the installed and latest stable versions. If an update is
available, it shows the publication date, release summary, notes, and the exact
asset selected for the current operating system and architecture.

## Verified Download and Installer Launch

`Descargar y verificar` is enabled only when the same GitHub Release contains:

- a matching installer named with the platform tag; and
- either the consolidated `SHA256SUMS` asset or a sidecar named
  `<installer>.sha256`.

The application downloads to its user-data `updates` directory through a
temporary file, enforces size limits, and compares the exact file against the
published SHA-256 digest. A failed, cancelled, timed-out, or incomplete
download is discarded. The hash and size are recalculated immediately before
launch, which detects modifications made before that second check and narrows
the time-of-check/time-of-use window. It cannot eliminate that window or stop
another process running as the same user from replacing the file after the
recheck. Platform code signing remains the stronger publisher-authentication
control, and the current release installers are not yet signed.

After verification, a separate dialog shows the local path, size, and SHA-256.
The installer runs only if the user explicitly presses `Ejecutar instalador`.
Choosing `Más tarde` leaves the verified file available without launching it.

## Automatic Check

Automatic checks run in the background and do not block startup. The default frequency is weekly. Disable them from:

```text
Ayuda > Revisar actualizaciones automaticamente
```

Offline connections, timeouts, malformed metadata, missing platform assets,
missing checksums, and hash mismatches produce a bounded error message. They do
not prevent the application from starting or continuing normally.

## Release Source

A clean installation uses the official latest-release endpoint:

```text
https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest
```

A controlled deployment can override it with:

```powershell
$env:CHAOS_TOOLBOX_RELEASES_API_URL="https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest"
```

Installable assets must follow:

- `chaos-toolbox-v<version>-windows-x64-setup.exe`
- `chaos-toolbox-v<version>-macos-arm64.dmg`
- `chaos-toolbox-v<version>-linux-x64.deb`

The release workflow produces the Actions artifact
`chaos-toolbox-release-manifest`, containing a consolidated `SHA256SUMS` with
the exact basenames of the verified release assets. Publishing remains manual:
attach that `SHA256SUMS` and the exact binaries it describes to the same stable
GitHub Release. A standard line is:

```text
<64 lowercase hexadecimal characters>  chaos-toolbox-v<version>-windows-x64-setup.exe
```

Do not rename an installer after generating the manifest. Do not publish two
assets with the same basename.

Windows installers are configured for installation over a previous version while preserving user configuration and generated results. macOS automatic replacement can require signing and notarization. The automated Linux release artifact is a `.deb`; the updater can guide its download, and installation should use the system package manager.

SHA-256 detects corruption or substitution relative to the manifest in the
same release. It does not replace Windows code signing, Apple signing and
notarization, Linux package signing, or protection of the GitHub account. The
explicit launch button remains required even after a matching digest.

Numerical results are computational evidence, not automatic mathematical proof.

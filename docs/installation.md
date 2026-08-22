# Installation

Fyskode Chaotic Systems Toolbox is developed by Maria Fernanda Moreno Lopez
(Fer Moreno). Its own source code is MIT-licensed; PySide6, Qt, and other
dependencies retain their separate licenses. Installed packages include
`THIRD_PARTY_NOTICES.md` and the LGPLv3/GPLv3 texts.

## Supported Platforms

- Windows 10/11 x64.
- macOS 13+ on x64 or arm64, built on macOS.
- Modern Linux x64 distributions with desktop Qt support.

## End Users

When a platform package is published for a release, install the matching artifact:

- Windows: `chaos-toolbox-v0.2.0-windows-x64-setup.exe`.
- macOS: `.app` inside `chaos-toolbox-v0.2.0-macos-arm64.dmg` or matching architecture.
- Linux: `chaos-toolbox-v0.2.0-linux-x64.deb`, or the matching architecture when published.

Installing a newer version over an older version should not remove user configuration, generated results, configured external resources, or local galleries.

## Source Install

Use Python 3.11 or newer:

```powershell
python -m pip install .
chaos-toolbox
```

The Python wheel is universal and deliberately does not include `core/bin`.
Wheel and source installations compile the C11 backend from
`core/csrc/chaos_core.c` into the per-user cache on first native use. They
therefore require `gcc` or `clang` on `PATH`. PyInstaller executables include
the native library for their platform and do not require a C toolchain on the
destination computer.

The normal installation includes the compatible
`hidden-attractors-fo>=1.1,<2` scientific engine. To enable the embedded HTML
theory viewer, install `python -m pip install ".[webengine]"`; without it the
same local Markdown is shown in a text-safe viewer.

When migrating an existing checkout, recreate environments that previously
contained another Qt binding. The launch and build scripts fail closed when a
legacy binding remains importable; installing PySide6 beside it is not treated
as a clean migration.

Toolbox uses APIs that are not present in HAFO 1.0, so the dependency must not
be downgraded. If the package index does not yet offer a compatible 1.1 release,
source installation and public release are intentionally blocked. For an
authorized development validation, first build and install the HAFO 1.1 wheel
from its release source, then install Toolbox normally; no sibling-checkout or
personal-path fallback is supported.

For modified PySide6/Qt builds, install the coherent replacement package set
in a fresh environment before installing Toolbox Chaos. See `license.md` for
the relinking and release-source policy.

Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.


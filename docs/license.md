# License

Fyskode Chaotic Systems Toolbox 0.1.0 is developed by Maria Fernanda Moreno
Lopez (Fer Moreno). The project's own source code is distributed under the
MIT License. See `LICENSE` for that complete text.

Dependencies retain their own licenses. In particular, the community
PySide6, Shiboken6, and Qt components used by official binary builds are
distributed using their applicable open-source terms; this project selects
the LGPLv3 route for the Qt/PySide components that offer it. This does not
change the MIT license of the application's own code.

Qt Charts, Qt Data Visualization, Qt Graphs, Qt Quick 3D, Qt Quick Timeline,
and Qt Virtual Keyboard are not used and are removed from binary bundles
because their community licensing is GPLv3 rather than LGPLv3. The release
verifier fails closed if any of those module families reappears.

Every wheel, source archive, PyInstaller bundle, and installer must retain:

- `NOTICE.md`;
- `THIRD_PARTY_NOTICES.md`;
- `LICENSES/LGPL-3.0-only.txt`;
- `LICENSES/GPL-3.0-only.txt`;
- `LICENSES/Chromium-BSD-3-Clause.txt`;
- `LICENSES/QtWebEngine-Third-Party-NOTICE.txt`;
- `LICENSES/Qt-PySide-6.11.1-Corresponding-Source.txt`;
- `LICENSES/Qt-6.11.1-Security-Inventory.txt`;
- upstream distribution metadata and license files for dependencies embedded
  by PyInstaller.

Native PyInstaller bundles additionally copy the exact license from the
Python interpreter being redistributed into `LICENSES/Python/` and retain the
Qt WebEngine runtime resource. That binary `.pak` is not treated as a readable
license inventory. The release workflow produces a normalized
Python-environment CycloneDX SBOM and a separate file-hash SBOM for each
platform bundle. The installer and DMG gates extract or mount their final
artifacts before publication. An SBOM is an inventory, not a replacement for
license notices or corresponding source obligations.

## Relinking and modified Qt/PySide builds

The source distribution can be installed in a fresh virtual environment
against a compatible modified build of PySide6/Qt, followed by installation
of Toolbox Chaos itself. Platform applications are built in PyInstaller
one-directory mode: Qt shared libraries and PySide6 extension modules remain
separate files inside the application bundle. A replacement must use a
coherent, ABI-compatible set matching the recorded SBOM rather than swapping
one DLL or extension in isolation.

Official installers impose no additional term that prohibits reverse
engineering for the purpose of debugging modifications to LGPL-covered
libraries. Release maintainers must retain the corresponding source for the
exact Qt/PySide components they distribute, including any modifications, and
provide it with the release or through a valid written offer under their
control. An upstream link alone is not treated by this project as completion
evidence for that obligation.
The release workflow therefore downloads and verifies the exact Qt 6.11.1 and
PySide 6.11.1 source archives, and public release procedure requires attaching
them to the same durable GitHub Release as every binary; the temporary Actions
artifact is only staging evidence and is not a written offer.

QtSvg remains present because Matplotlib and pyqtgraph use its renderer and
generator. `QSvgRenderer` is configured before adapter imports with restricted
Tiny 1.2 features and animations disabled, and user/gallery/Markdown image
input is confined to decoded PNG. The later official CVE-2026-8168 QtSvg patch
series is not claimed to be present in public PySide6 6.11.1 wheels. See the
packaged security inventory; public freeze requires recorded acceptance of
that residual trusted-input risk.

The Qt Company's licensing guidance and the license texts themselves remain
the controlling references. This document is an engineering distribution
policy, not legal advice.

The public distribution does not include original Sprott protected
dictionaries, executables, source code, book disk files, figures, or long
book text. User-local resources remain outside the installer.

Numerical results are computational evidence, not automatic mathematical
proof.

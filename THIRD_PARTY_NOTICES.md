# Third-party notices

This file records the principal third-party components used by Fyskode
Chaotic Systems Toolbox. It does not change the MIT license of the project's
own source code and it does not replace the license files or metadata shipped
by each dependency. The CycloneDX SBOM attached to each release records the
resolved package versions for that build.

## PySide6, Shiboken6, and Qt

The desktop interface uses the official Qt for Python bindings:

- PySide6-Essentials;
- PySide6-Addons when Qt WebEngine is included;
- Shiboken6;
- the dynamically loaded Qt libraries distributed by those packages.

The community Qt for Python distribution is available under LGPLv3/GPLv3.
Official binary builds of Toolbox Chaos use the LGPLv3 option for the
components that offer it. The project's MIT-licensed code remains a separate
work using those dynamically loaded libraries. The complete texts are
included as:

Qt Charts, Qt Data Visualization, Qt Graphs, Qt Quick 3D, Qt Quick Timeline,
and Qt Virtual Keyboard are not used by Toolbox. They are removed from binary
bundles because their community licensing is GPLv3 rather than LGPLv3, and the
artifact verifier fails if any of those module families reappears.

- `LICENSES/LGPL-3.0-only.txt`;
- `LICENSES/GPL-3.0-only.txt` (LGPLv3 incorporates and supplements GPLv3).

Qt WebEngine includes Chromium and other third-party open-source components.
Their exact notices depend on the resolved Qt version. Qt's versioned
third-party license documentation and corresponding source remain the
controlling technical inventory for those embedded components.
The release also carries `LICENSES/Chromium-BSD-3-Clause.txt`,
`LICENSES/QtWebEngine-Third-Party-NOTICE.txt`, and the exact source manifest
`LICENSES/Qt-PySide-6.11.1-Corresponding-Source.txt`. The residual QtSvg
risk and trusted-input boundary are recorded in
`LICENSES/Qt-6.11.1-Security-Inventory.txt`. Native bundles
preserve `qtwebengine_resources.pak` because it is required runtime data;
this project does not treat that binary resource as a human-readable license
inventory.

Qt and PySide are trademarks of The Qt Company Ltd. This notice identifies
technical dependencies and does not imply endorsement.

Official references:

- <https://doc.qt.io/qtforpython-6/>
- <https://doc.qt.io/qtforpython-6/licenses.html>
- <https://doc.qt.io/qt-6/licensing.html>
- <https://www.qt.io/development/open-source-lgpl-obligations>
- <https://www.gnu.org/licenses/lgpl-3.0.html>
- <https://www.gnu.org/licenses/gpl-3.0.html>

## Other redistributed runtime and build components

PyInstaller bundles a Python runtime and the installed runtime libraries into
the platform application. The principal components and their upstream license
identifiers or license families are:

- Python: Python Software Foundation License;
  PyInstaller bundles copy the exact interpreter license from
  `sys.base_prefix` into `LICENSES/Python/`;
- NumPy: BSD-3-Clause plus the licenses of its bundled components;
- Matplotlib: Matplotlib License plus bundled font and component licenses;
- pyqtgraph: MIT;
- PyYAML: MIT;
- Pillow: HPND;
- packaging: Apache-2.0 or BSD-2-Clause;
- Hidden Attractors FO: MIT;
- PyInstaller bootloader: GPL-2.0-or-later with the PyInstaller bootloader
  exception.

The PyInstaller bundle retains installed distribution metadata and license
files for these components. Those upstream files remain controlling; this
summary does not replace them. The release SBOM is the machine-readable
inventory of the exact resolved versions. Source wheel and sdist installations
receive each dependency as a separate Python distribution with its own
metadata and license files.

## Lazaros Moysis attribution

This attribution records methodological inspiration from user-provided MATLAB
code attributed to Lazaros Moysis for the Lorenz system. The distributed
repository contains its C/Python implementation and does not redistribute the
MATLAB file.

Reference:

- Lazaros Moysis, *Bifurcation diagram for the Lorenz Chaotic system*,
  MATLAB Central File Exchange:
  <https://www.mathworks.com/matlabcentral/fileexchange/156752-bifurcation-diagram-for-the-lorenz-chaotic-system>.
- The supplied reference code simulates the Lorenz system, discards a
  transient, and records intersections with a selected plane.

No source file from that submission is included in the distributed package.
If source from it is introduced later, release must remain blocked until its
exact copyright notice, conditions, and disclaimer are included.

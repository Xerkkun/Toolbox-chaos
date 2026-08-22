# Troubleshooting

Fyskode Chaotic Systems Toolbox 0.2.0 is developed by Maria Fernanda Moreno Lopez (Fer Moreno) and distributed under the MIT License.

## PDF Viewer

If the embedded PDF viewer is unavailable, install a PySide6 build with QtPdf support or use the external-open button in the PDF tab.

## HTML Theory Viewer

Install `python -m pip install ".[webengine]"` to use the Qt WebEngine view.
The application probes both the import and construction of a WebEngine page.
If that probe fails, including on `offscreen` or `minimal` Qt platforms, it
shows the same local Markdown with the text-safe viewer.

## Native Backend

Frozen Windows builds use the bundled `core/bin/chaos_core.dll`. A source or
wheel installation with the C source available builds a content-addressed
library in the application-data cache, never in the installed package. Install
GCC or Clang if that source build reports that no compiler is available.

## Hidden Attractors FO

Toolbox requires `hidden-attractors-fo>=1.1,<2`. Reinstall the project with
`python -m pip install .` if the custom-system tab reports a missing,
incompatible, or incomplete engine. Toolbox does not search a neighbouring
source checkout.

## Fixed time grids

Choose `T` and `dt` so `T/dt` is an integer. The application rejects a
nonuniform final partial step rather than assigning it an incorrect timestamp.

## Updates

If update checks report no configured source, set
`CHAOS_TOOLBOX_RELEASES_API_URL` to the official `https://api.github.com/...`
latest-release endpoint. Other schemes, hosts, credentials, ports, oversized
responses, and untrusted asset links are rejected. If there is no internet,
the app continues normally.

## Packaging

Run `python scripts\verify_packaging.py` before PyInstaller. It fails when required PDFs are missing or forbidden LaTeX/source files enter `resources/bundled`.

Numerical results are computational evidence, not automatic mathematical proof.

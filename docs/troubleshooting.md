# Troubleshooting

Chaos Toolbox 0.1.0 is developed by Fer Moreno and distributed under the MIT License.

## PDF Viewer

If the embedded PDF viewer is unavailable, install a PyQt6 build with QtPdf support or use the external-open button in the PDF tab.

## Native Backend

Windows builds use `core/bin/chaos_core.dll`. Rebuild it through `packaging/windows/build.ps1` if backend loading fails.

## Updates

If update checks report no configured source, set `CHAOS_TOOLBOX_RELEASES_API_URL` to a controlled latest-release API endpoint. If there is no internet, the app continues normally.

## Packaging

Run `python scripts\verify_packaging.py` before PyInstaller. It fails when required PDFs are missing or forbidden LaTeX/source files enter `resources/bundled`.

Numerical results are computational evidence, not automatic mathematical proof.

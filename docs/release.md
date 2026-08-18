# Release Process

Fyskode Chaotic Systems Toolbox 0.1.0 is developed by Maria Fernanda Moreno
Lopez (Fer Moreno). Its own source is MIT-licensed; bundled dependencies
retain their separate licenses.

1. Update `pyproject.toml` using semantic versioning `MAJOR.MINOR.PATCH`.
2. Update `CHANGELOG.md`, `RELEASE_NOTES.md`, `CITATION.cff`, and documentation references.
   Review `requirements-release.txt` as one locked runtime set. Update the three
   equal PySide6-Essentials/PySide6-Addons/Shiboken6 pins deliberately when
   changing Qt for Python, and revalidate every scientific and plotting pin.
   Official release jobs use Python 3.14.6, HAFO 1.2.0, PyInstaller 6.22.0,
   hooks 2026.6, and the exact `pip==26.2.1` bootstrap in
   `requirements-bootstrap.txt`.
3. Run:

```powershell
python scripts\prepare_runtime_resources.py
python scripts\verify_hafo_release.py
python scripts\verify_packaging.py
python scripts\verify_distribution_compliance.py --check-installed --require-webengine --check-release-pins --check-build-pins
python scripts\bundle_size_report.py
python -m pytest tests\test_packaging_metadata.py tests\test_ui_refactoring.py -q
python -m build --sdist --wheel
python -m twine check dist\*
```

The HAFO gate intentionally blocks publication until a compatible
`hidden-attractors-fo>=1.1,<2` wheel is public. A locally built HAFO wheel may
be used for integration evidence, but it is not evidence that public users can
install Toolbox from the package index.

4. Create the exact tag `v<project.version>` and run the release workflow from that tag. The gate reads `APP_VERSION` from `pyproject.toml` and rejects branches or mismatched tags before any artifact is built.
5. Build platform artifacts on their native OS. The release workflow builds the Python wheel and source distribution once in a dedicated job, validates both with `twine`, and installs and executes the native self-test from each distribution independently.
6. Preserve the Python-environment CycloneDX SBOM beside the wheel/source archive and the file-hash CycloneDX SBOM produced from each Windows, macOS, and Linux bundle. Verify PySide6-Essentials, PySide6-Addons, Shiboken6, the Python runtime, native files, and absence of the legacy Qt binding.
7. Confirm by inspecting the wheel, sdist, PyInstaller bundle, installed Windows image, mounted DMG, and clean-installed DEB that they retain `THIRD_PARTY_NOTICES.md`, LGPLv3/GPLv3, Chromium notices, the source/security manifests, and the exact Python runtime license where Python is bundled. Also confirm that the unused GPL-only Qt module families named in `docs/license.md` are absent.
8. Attach both verified Qt/PySide 6.11.1 source archives, `SHA256SUMS`, and their manifest to the same persistent GitHub Release as the binaries. The 90-day Actions artifact alone is not durable delivery and no written offer is asserted.
9. Review the Qt security inventory and record acceptance of the residual CVE-2026-8168 trusted-input risk; do not describe the public PySide6 6.11.1 binary as fully patched.
10. Upload all remaining artifacts to the GitHub Release for that exact tag.
11. A clean installation already uses the official GitHub latest-release API. `CHAOS_TOOLBOX_RELEASES_API_URL` is an optional controlled-deployment override.
12. For release archiving, archive the stable release in OSF, create an OSF Registration for the frozen version, generate the OSF DOI, and add that DOI to `CITATION.cff` and `README.md` only after it exists.

The exact interpreter, runtime, Qt, HAFO, and PyInstaller pins constrain version
resolution, and the SBOM records every delivered file. The project still does
not claim bit-for-bit equality across operating systems because native compiler,
runner image, code-signing, and platform packaging outputs differ.

GitHub remains the active development repository for issues, source code, tests, and pull-request history. OSF is the persistent archive for the frozen release snapshot and DOI.


Signing and notarization are manual. Until signed artifacts and published
checksums are part of a release, the application must not claim cryptographic
verification: users are directed to the official GitHub Release and its
checksums before executing a downloaded artifact.

Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.


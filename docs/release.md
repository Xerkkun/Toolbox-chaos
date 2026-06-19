# Release Process

Fyskode Chaotic Systems Toolbox 0.1.0 is developed by Maria Fernanda Moreno Lopez (Fer Moreno) and distributed under the MIT License.

1. Update `pyproject.toml` using semantic versioning `MAJOR.MINOR.PATCH`.
2. Update `CHANGELOG.md`, `RELEASE_NOTES.md`, `CITATION.cff`, and documentation references.
3. Run:

```powershell
python scripts\prepare_runtime_resources.py
python scripts\verify_packaging.py
python scripts\bundle_size_report.py
python -m pytest tests\test_packaging_metadata.py tests\test_ui_refactoring.py -q
```

4. Build platform artifacts on their native OS.
5. Upload artifacts to a GitHub Release tagged `v0.1.0`.
6. Configure `CHAOS_TOOLBOX_RELEASES_API_URL` to the GitHub latest-release API URL for update checks.
7. For release archiving, archive the stable release in OSF, create an OSF Registration for the frozen version, generate the OSF DOI, and add that DOI to `CITATION.cff` and `README.md` only after it exists.

GitHub remains the active development repository for issues, source code, tests, and pull-request history. OSF is the persistent archive for the frozen release snapshot and DOI.


Signing and notarization remain manual until certificates are configured.

Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.


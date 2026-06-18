# Release Archiving With OSF

Fyskode Chaotic Systems Toolbox 0.1.0 is developed by Maria Fernanda Moreno Lopez (Fer Moreno) and distributed under the MIT License.

The final archival DOI has been assigned as `10.17605/OSF.IO/GQMJR` and added to `CITATION.cff`, `README.md`, and `paper/paper.md`.

## Roles

GitHub is the active repository for JOSS review, issues, source code, tests, pull requests, development history, and release tags.

OSF is the persistent archive for the frozen source snapshot associated with the JOSS submission. OSF will provide the archival DOI after registration.

## Procedure

1. Create a release tag in GitHub:

```powershell
git tag v0.1.0
git push origin v0.1.0
```

2. Generate the source archive from the tagged state. Use a clean checkout or GitHub's generated source archive. Confirm it follows `docs/osf_archive_manifest.md`.

3. Create a public OSF project or component for Chaos Toolbox.

4. Upload the source archive and required metadata files to OSF. Include at minimum `LICENSE`, `CITATION.cff`, `README.md`, `paper/paper.md`, `paper/paper.bib`, `pyproject.toml`, source code, tests, docs, examples, and reproducibility files.

5. Create an OSF Registration for the frozen release snapshot. The registration is the immutable archival record for the submitted version.

6. Generate or request the OSF DOI for the registration.

7. After the DOI exists, update:

- `CITATION.cff` with the DOI field.
- `README.md` citation section with the DOI.
- `paper/paper.md` metadata or narrative with the final archive DOI.
- `docs/release.md` and `RELEASE_NOTES.md` if needed.

8. Re-run:

```powershell
python scripts\verify_joss_metadata.py
python scripts\verify_packaging.py
python -m pytest tests\test_packaging_metadata.py tests\test_ui_refactoring.py -q
```

9. Submit the GitHub repository and OSF DOI to JOSS. Keep GitHub as the review location and OSF as the persistent frozen archive.

## DOI Policy Before OSF Assignment

Before OSF assignment, the policy was:

- Omit `doi` from `CITATION.cff`.
- Do not include fake DOI strings in `paper/paper.md`.
- Use narrative text such as "OSF DOI pending" or "DOI to be assigned after OSF archival release" only in documentation.

*(Note: The archive has now been frozen and registered with DOI `10.17605/OSF.IO/GQMJR`.)*

Numerical results are computational evidence, not automatic mathematical proof.

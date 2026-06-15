# Versioning

Chaos Toolbox 0.1.0 is developed by Fer Moreno and distributed under the MIT License.

The source of truth for the software version is:

```text
pyproject.toml
```

The app reads this version through `core/app_metadata.py`. The same version is used by UI metadata, documentation, release notes, PyInstaller/Inno packaging scripts, and artifact names.

The version policy is semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Numerical results are computational evidence, not automatic mathematical proof.

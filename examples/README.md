# Examples

Chaos Toolbox 0.1.0 is developed by Fer Moreno and distributed under the MIT License.

This directory is reserved for minimal reproducibility examples to include in an OSF archive and future JOSS review.

Current reproducibility entry points:

- Run the desktop app from source: `python main.py`.
- Prepare runtime resources: `python scripts\prepare_runtime_resources.py`.
- Verify package and JOSS metadata: `python scripts\verify_packaging.py` and `python scripts\verify_joss_metadata.py`.
- Run focused tests: `python -m pytest tests\test_packaging_metadata.py tests\test_ui_refactoring.py -q`.

The Sprott Explorer can load user-local `.DIC` files for personal exploration. Those files are not examples for the public archive and must not be uploaded to OSF unless redistribution rights are explicitly documented.

Numerical results are computational evidence, not automatic mathematical proof.

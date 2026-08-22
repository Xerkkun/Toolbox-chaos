# Examples

Fyskode Chaotic Systems Toolbox 0.2.0 is developed by Maria Fernanda Moreno Lopez (Fer Moreno) and distributed under the MIT License. This source tree corresponds to the stable 0.2.0 release.

This directory is reserved for minimal reproducibility examples to include in the release archive.

Current reproducibility entry points:

- Run the installed desktop app: `chaos-toolbox`.
- Prepare runtime resources: `python scripts\prepare_runtime_resources.py`.
- Verify package: `python scripts\verify_packaging.py`.
- Run focused tests: `python -m pytest tests\test_packaging_metadata.py tests\test_ui_refactoring.py -q`.

The Sprott Explorer can load user-owned `.DIC` files locally at runtime for personal exploration. Original Sprott disk files, `.DIC` databases, book figures, or proprietary executables are not bundled or redistributed with the software, and local files must not be copied into the repository or package.

Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.



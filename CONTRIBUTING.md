# Contributing Guidelines

Thank you for your interest in contributing to **Fyskode Chaotic Systems Toolbox**. These guidelines are designed to help you set up the development environment, run tests, and propose changes in a structured way that respects the project's architecture and release policies.

## Development Environment Setup

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/Xerkkun/Toolbox-chaos.git
   cd Toolbox-chaos
   ```

2. **Create and activate a virtual environment:**
   - On Windows:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - On macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies:**
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install ".[test]"
   ```

4. **Run the application from source:**
   ```powershell
   python main.py
   ```

## Running Tests and Verifications

Before proposing any changes, verify that the existing tests and packaging metadata constraints pass.

1. **Run the pytest suite:**
   ```powershell
   python -m pytest -q
   ```

2. **Verify release and packaging checks:**
   ```powershell
   python scripts\verify_packaging.py
   python scripts\verify_distribution_compliance.py --check-installed
   python scripts\verify_public_release_clean.py
   ```


Note that on Linux CI/headless environments, PySide6 requires a virtual display. Use the `QT_QPA_PLATFORM=offscreen` environment variable to run tests headlessly:
```bash
QT_QPA_PLATFORM=offscreen python -m pytest
```

## Proposing Changes

Pull Requests are proposed changes from a branch that can be reviewed before being merged into main. To ensure traceability, use the following branching structure when submitting your work:

- **Documentation and release prep:** Prefix branches with `docs/`, for example:
  - `docs/release-prep`
- **Packaging, builds, and installation fixes:** Prefix branches with `fix/`, for example:
  - `fix/packaging-docs`
- **Catalog expansions and core features:** Prefix branches with `feature/`, for example:
  - `feature/system-catalog`

### Branch Workflow
1. Create a branch from `main` with the appropriate prefix.
2. Commit logical changes with clear, concise commit messages.
3. Push your branch to GitHub and open a Pull Request against `main`.

## Contribution Style & Standards

- **Code Style:** Follow PEP 8 guidelines for Python code. Ensure PySide6 widgets and signal-slot connections are clear and decoupled from the numerical simulation logic.
- **Backend Optimization:** The computational engine uses a native C library under `core/csrc/chaos_core.c` for performance. If you propose modifications to the numerical integration methods, ensure the Python fallback implementations are kept in sync.
- **System Catalog:** Curated systems belong in `SYSTEM_REGISTRY`, with matching Python/native contracts and regression tests where applicable. The existing `Crear sistema` tab is for safe trajectory-only user definitions; it does not promote those definitions into the curated registry or its advanced diagnostics.
- **Documentation Policy:** All public-facing documentation must adhere to the [Public Documentation Policy](docs/public_documentation_policy.md). Ensure that user guides, release notes, and README files contain only neutral, current-state facts and omit internal histories, AI-generated traces, or submission strategies.



## Reporting Errors

- **Numerical/Integration Errors:** When reporting incorrect orbits, divergent trajectories, or calculation discrepancies, provide the exact parameter values, initial conditions, and numerical solver settings (e.g., step size, duration).
- **Interface Errors:** When reporting UI glitches, canvas freezing, or PySide6 errors, please include log tracebacks, operating system version, and desktop resolution.

## Critical Security and Copyright Policy

To comply with licensing and publication standards, the following guidelines are strictly enforced:
- **No Proprietary Sprott Materials:** **Do not** add, commit, or package original `.DIC` files, book figures, historical executables, or copyrighted texts from J. C. Sprott. The Sprott Explorer is designed only to load user-local files at runtime.
- **No Large Binaries or Installers:** Do not commit compiled `.exe`, `.dmg`, AppImage files, or heavy LaTeX build folders. Only release scripts and configuration source files should be committed.

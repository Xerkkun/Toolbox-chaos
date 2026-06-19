# Public Documentation Policy

This policy governs all public-facing documentation for the **Fyskode Chaotic Systems Toolbox**. All user guides, installation manuals, release notes, website contents, and metadata files must adhere to these guidelines.

## 1. Scope and Tone
- **Neutral and Current-State Focused**: Documentation must describe the current functionality of the software as of the release version.
- **No Editorial or Journal Strategy**: Do not include information about editorial processes, journal submission strategies (e.g., JOSS preparation/readiness details, word counts, or peer review workflows) in general-user documents like `README.md`, `RELEASE_NOTES.md`, or website pages. Keep submission-specific details confined strictly to designated files (e.g., `docs/joss-readiness.md` and `docs/reviewer-guide.md`).
- **No Internal Development History**: Remove details of internal refactoring history, audit logs, obsolete folders/layouts, or progress narratives.
- **No AI References**: Do not reference AI, Codex, ChatGPT, automated traces, or internal prompt files in public documentation.

## 2. Technical and Path Conventions
- **No Absolute Paths**: Use repository-relative paths only. Never include machine-specific paths or local file URIs (such as `file:///`).
- **Consistent Warnings**: Avoid repeating the same numerical limitations warning in every section. A single, concise scope statement should be placed in `README.md` and user guides where necessary.
  - Recommended wording: *“Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.”*
- **Sprott Explorer Scope and Legal Boundaries**: The Sprott Explorer is strictly a local educational tool. Wording must be conservative and clear:
  - No original Sprott copyrighted disk files are bundled.
  - No `.DIC` databases are redistributed.
  - No book figures or proprietary executables are bundled.
  - User-owned `.DIC` files can be loaded locally at runtime for personal exploration.
  - Local files are not copied into the package, repository, or installer.

## 3. Scientific and Feature Claims
- **Numerical Diagnostics**: Describe Lyapunov exponents, FFT, bifurcation sweeps, phase portraits, attraction basins, and trajectories as numerical diagnostics or approximations, not formal mathematical proofs.
- **No Overclaiming**: Do not state that the toolbox "proves" chaos, "certifies" hidden attractors, or offers "complete reproduction" of all published systems.
- **Planned vs. Current Features**: Future features (e.g., custom systems/arbitrary equations) must be explicitly marked as planned/future, not current functionality.

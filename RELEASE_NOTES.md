# Release Notes - Fyskode Chaotic Systems Toolbox 0.2.0

Release date: 2026-08-28. This release retains the existing OSF project DOI;
no new version-specific DOI is assigned.

## Added

- No-code editor for safe expression-defined flows and maps through the
  compatible Hidden Attractors FO engine.
- Expanded trajectory, spectrum, Lyapunov, bifurcation, basin, coexistence,
  custom-system, and Sprott exploration workflows.
- Integrated stable-release updater with semantic-version comparison, release
  notes, platform-specific installer selection, atomic download, SHA-256
  verification, explicit launch confirmation, cancellation, and a total
  download deadline.
- Consolidated `SHA256SUMS` generation in release CI for the exact installer
  asset basenames. GitHub Release publication remains manual.

## Changed

- Desktop UI and packaging use PySide6 consistently.
- Windows packaging validates the frozen self-test before generating the Inno
  Setup installer and preserves user configuration during upgrades.
- Local manuals and generated educational resources are synchronized with the
  0.2.0 release identity.

## Security

- Release metadata must identify one exact canonical installer for the current
  version, platform, and architecture; drafts, prereleases, ambiguous assets,
  unsafe names, and untrusted redirects are rejected.
- Downloads are size-bounded, written through a temporary file, and discarded
  after checksum, cancellation, timeout, or local-I/O failures. Hash and size
  are checked again immediately before launch, narrowing but not eliminating
  the time-of-check/time-of-use window.

## Notes

- Numerical outputs are computational evidence and do not represent automatic
  mathematical proof.
- Sprott Explorer operates locally and does not bundle or redistribute
  copyrighted dictionaries, book figures, or executables.
- The existing OSF DOI identifies the current project/archive record; no
  additional version-specific DOI is assigned.

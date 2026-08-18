# Website Integration

This repository connects to the Fyskode public website to display up-to-date software details.

## General Information
- The public website consumes the repository metadata through its configured synchronization source; no workstation path is part of this contract.
- This repository exposes project facts via `docs/project_metadata.json`.
- When changes are made here (such as version bumps or new features), the website pulls updates using its synchronization script.

## Exposed Assets
- **Metadata**: Exclusively defined in [project_metadata.json](project_metadata.json). Personal absolute paths and file URIs must never be stored in this file.
- **Screenshots**: Place official software screenshots in the [assets/screenshots/](../assets/screenshots/) folder. Use the standard filenames suggested in its README.

## Excluded Files (Do Not Expose)
- Do not reference local absolute file paths.
- Do not include commercial books or copyrighted PDFs.
- Do not commit Sprott's original text database files.
- Do not copy build artifacts, logs, or installation packages (`dist/`, `build/`, `reports/`, `.venv/`) to the metadata or website integration pathways.

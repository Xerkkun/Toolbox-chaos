# Website Integration

This repository connects to the Fyskode public website to display up-to-date software details.

## General Information
- The public website source code resides in `Desktop/Codes/fyskode`.
- This repository exposes project facts via `docs/project_metadata.json`.
- When changes are made here (such as version bumps or new features), the website pulls updates using its synchronization script.

## Exposed Assets
- **Metadata**: Exclusively defined in [project_metadata.json](file:///c:/Users/moren/Desktop/Codes/Toolbox%20chaos/docs/project_metadata.json). No local paths (like `C:/Users` or `file:///`) should ever be stored in this file.
- **Screenshots**: Place official software screenshots in the [assets/screenshots/](file:///c:/Users/moren/Desktop/Codes/Toolbox%20chaos/assets/screenshots/) folder. Use the standard filenames suggested in its README.

## Excluded Files (Do Not Expose)
- Do not reference local absolute file paths.
- Do not include commercial books or copyrighted PDFs.
- Do not commit Sprott's original text database files.
- Do not copy build artifacts, logs, or installation packages (`dist/`, `build/`, `reports/`, `.venv/`) to the metadata or website integration pathways.

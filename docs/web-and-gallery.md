# Website and Gallery Integration

This document outlines the public web presentation and screenshot guidelines for **Fyskode Chaotic Systems Toolbox**.

## 1. Web Portal Integration

The project facts and release metadata are synchronized with the Fyskode public search platform:
- **Public URL:** [https://search.fyskode.com/toolbox_chaos](https://search.fyskode.com/toolbox_chaos)
- **Metadata Source:** The website reads project fields dynamically from [project_metadata.json](project_metadata.json). To prevent leakage, do not store absolute paths (e.g., user home directory paths) in the metadata file.

## 2. Screenshot Gallery Guidelines

When updating the web gallery or adding inline images to the documentation, compile screenshots of the following nine key views:

1. **Inicio (Main Dashboard):** The application home screen showing initial greeting and layout.
2. **Selector de sistemas (System Catalog Selector):** The catalog menu list showcasing classical, multistable, and no-equilibrium categories.
3. **Visualizador 3D (3D Trajectory Canvas):** A rendering of a 3D chaotic attractor showing rotation and zoom capability.
4. **Exponentes de Lyapunov (Lyapunov Tab):** The calculated spectrum showing convergence curves over iteration steps.
5. **Diagrama de Bifurcaciones (Bifurcation View):** Sweeps displaying period-doubling cascades and chaotic regions.
6. **Espectro FFT (FFT Analyzer):** Power spectral density graphs displaying frequency distribution.
7. **Cuencas de Atracción (Basins of Attraction Grid):** Multistable attraction maps colored by attractor destination.
8. **Sprott Explorer:** The custom loader interface displaying local `.DIC` parsing.
9. **Diccionario PDF (PDF Document Viewer):** The integrated help document reader.

## 3. Sprott Figure Safety Policy

To comply with release and publication copyright guidelines, follow this rule strictly:
- **Do Not Copy Book Assets:** Screenshots of the Sprott Explorer **must not** contain diagrams, charts, or images scanned or copied from Julien C. Sprott's books, publications, or historical websites.
- **Toolbox Recreations Only:** All visual assets of Sprott systems displayed on the website or documentation must be **screenshots of local simulations generated in real-time by the Fyskode Chaotic Systems Toolbox itself**.

## 4. Linking guidelines

When linking the web gallery from the repository readme or documentation files, use the relative path to screenshots under `assets/screenshots/` and external link pointers to the public Fyskode website:
```markdown
For interactive features and screenshots, see the [Fyskode Portal](https://search.fyskode.com/toolbox_chaos).
```

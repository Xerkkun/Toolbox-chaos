# User Guide

Fyskode Chaotic Systems Toolbox is a PyQt6 desktop application developed by Maria Fernanda Moreno Lopez (Fer Moreno) under the MIT License.

Use the main tabs to simulate systems, visualize attractors, inspect time series, compare methods, calculate FFT/Lyapunov diagnostics, explore bifurcations, inspect basins where supported, and open the local PDF dictionary.

Version 0.1.0 uses a closed catalog of supported systems. Users can modify parameters, initial conditions, method choices, colors, and visualization options for registered systems, but cannot register arbitrary new systems from the main interface.

Generated plots and user-side Sprott gallery outputs are saved to user-selected locations or the local application data folder. Use `Ayuda > Abrir carpeta de resultados` to open the default results folder.

The Sprott Explorer can load user-owned `.DIC` files locally at runtime for personal exploration. This does not register a new complete system in the main toolbox. Original Sprott disk files, `.DIC` databases, book figures, or proprietary executables are not bundled or redistributed with the software, and local files are not copied into the repository or package.

Use `Ayuda > Documentacion` for local docs, `Ayuda > Buscar actualizaciones` for manual update checks, and `Ayuda > Acerca de` for version, license, developer, dependency credits, and academic-use notice.

Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.


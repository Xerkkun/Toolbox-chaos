# User Guide

Fyskode Chaotic Systems Toolbox is a PySide6 desktop application developed by
Maria Fernanda Moreno Lopez (Fer Moreno). Its own source code is MIT-licensed;
PySide6/Qt and other dependencies retain their separate licenses.

Use the main tabs to simulate systems, visualize attractors, inspect time series, compare methods, calculate FFT/Lyapunov diagnostics, explore bifurcations, inspect basins where supported, and open the local PDF dictionary.

Version 0.2.0 exposes 38 executable systems in its registry-backed selector.
Selecting a system loads its parameter and initial-condition defaults
automatically. Users can then modify those values, the numerical method,
colors, and visualization options.

The `Crear sistema` tab also accepts expression-defined flows and maps without
Python code. It validates, imports, exports, simulates, and plots these models
through the installed Hidden Attractors FO engine. Custom models remain
trajectory-only in this interface: the tab does not infer chaos, attraction,
stability, or hiddenness and does not generate a native kernel or the catalog
diagnostics automatically.

The main selector includes **Wang-Chen (variable equilibria)** and
**Nazarimehr (line of equilibria)**. Their published initial conditions are
also available from the coexistence selector, while the basin tab loads the
reference plane and domain as defaults.

Generated plots and user-side Sprott gallery outputs are saved to user-selected locations or the local application data folder. Use `Ayuda > Abrir carpeta de resultados` to open the default results folder.

The Sprott Explorer can load user-owned `.DIC` files locally at runtime for personal exploration. This does not add an entry to the curated main-system registry. Original Sprott disk files, `.DIC` databases, book figures, or proprietary executables are not bundled or redistributed with the software, and local files are not copied into the repository or package.

For trajectories with at least three state components, the Sprott Explorer also provides an `esfera unitaria` view. It maps each nonzero $(x,y,z)$ direction to $(x,y,z)/\sqrt{x^2+y^2+z^2}$ while deriving colour from the original state. Zero states are omitted because their direction is undefined. The view intentionally discards amplitude and is a visualization aid, not evidence of chaos, attraction, or hiddenness.

Use `Ayuda > Documentacion` for local docs, `Ayuda > Buscar actualizaciones`
for manual update checks, and `Ayuda > Acerca de` for version, project
license, developer, dependency credits, and academic-use notice. Complete
third-party notices and LGPLv3/GPLv3 texts are installed with the application.

Fixed-step simulations require the requested duration to be an integer
multiple of `dt`, within the documented floating-point tolerance. For example,
`T=0.9, dt=0.3` is accepted and `T=1, dt=0.3` is rejected instead of silently
labelling a partial final step. The Lyapunov panel is available only for
registered three-dimensional integer-order flows.

Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.

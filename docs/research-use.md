# Research Use and Scientific Workflows

**Fyskode Chaotic Systems Toolbox** serves as a lightweight, reproducible environment for the exploratory analysis and numerical characterization of chaotic dynamical systems. This document outlines how researchers and instructors utilize the toolbox's core analytical capabilities.

## 1. Visual Phase Space and Trajectory Analysis

Researchers use the phase space visualization panels to:
- Generate high-resolution 2D and 3D phase portraits of trajectories.
- Study attractor shapes, projections, and time-evolution of states under varying initial conditions.
- Visualise time-series signals and analyze dynamical trends (convergence, periodicity, or chaotic fluctuations).
- Export publication-quality vector and raster graphics using consistent color palettes and layout settings.

## 2. Lyapunov Exponent Estimation

The estimation of Lyapunov exponents is critical for characterizing sensitivity to initial conditions and screening possible chaotic behavior.
- **Spectrum Computation:** For integer-order 3D flows, the toolbox integrates the state and variational system together with fixed-step RK4, uses the system Jacobian, and applies periodic QR reorthogonalization.
- **Diagnostics:** The finite-time sign pattern provides numerical evidence about expansion and contraction over the declared horizon; it does not, by itself, prove asymptotic chaos or identify every invariant set.
- **Verification:** Researchers use this panel to screen catalog parameters, then repeat the calculation with different steps, horizons, initial conditions, and independent implementations.

## 3. Bifurcation sweeping

Bifurcation analysis reveals how system dynamics change as a control parameter varies.
- **Parametric Sweeps:** Users sweep one-dimensional parameters over continuous intervals, simulating trajectories from stable initial states.
- **Window Identification:** The resulting bifurcation diagrams help identify periodic windows, routes to chaos (e.g., period-doubling cascades), and sudden boundary crises.

## 4. Coexisting Attractors and Basins of Attraction

In multistable systems, different initial conditions converge to distinct coexisting attractors (e.g., chaotic attractors, limit cycles, or stable nodes).
- **Grid Sweeping:** The toolbox sweeps a grid of initial conditions on a user-selected 2D plane.
- **Basin Maps:** Each pixel on the grid is colored based on the final attractor destination, producing basin of attraction maps. This is an essential aid for researching hidden attractors, where the basin does not intersect any neighborhood of unstable equilibrium points.
- **Published research cases:** The Wang--Chen preset separates unbounded,
  periodic, and bounded-residual initial conditions. The residual class is not
  automatically labelled chaotic. The Nazarimehr preset treats
  convergence to the full invariant line
  \(E^*=\{(x,0,0):x\in\mathbb{R}\}\), rather than replacing that continuum by
  a single equilibrium point.

## 5. Spectral analysis

- **Welch PSD:** The recommended mode computes a one-sided power spectral density using Hann-windowed Welch averaging and density scaling. If a state variable has units `U` and time is expressed in seconds, the ordinate has units `U²/Hz`.
- **Amplitude spectrum:** The alternative mode computes a one-sided Hann-windowed amplitude spectrum; it is not labelled as a PSD.
- **Evidence boundary:** Peaks and broadband structure support interpretation of a time series, but a spectrum alone does not certify periodicity, chaos, attraction, or hiddenness.

## 6. Classroom and Educational Exploration

- **Historical Exploration:** The `Sprott Explorer` lets instructors and students load historical Sprott equations locally, providing a modern visual interface for educational exploration without distributing protected dictionary databases.
- **Equation Catalog:** A registry-backed catalog provides an interactive
  dictionary of chaotic dynamical equations and equilibrium information. The
  installed interface exposes verified systems. The `Crear sistema` tab also
  accepts safe expression-based flows and maps through Hidden Attractors FO;
  those user models remain distinct from curated and scientifically validated
  catalog entries.

## 7. Extending the source for research

The architecture separates system metadata, vector fields, numerical
integration, and presentation. A new three-dimensional flow is incorporated
by adding its metadata to `SYSTEM_REGISTRY`, implementing the same right-hand
side in Python and native C, assigning a stable native ID, and adding
Python-to-C parity and scientific-regression tests. Basin classifiers may also
need a model-specific contract, as illustrated by the periodic return map of
Wang--Chen and the equilibrium manifold of Nazarimehr.

This process is deliberately explicit: editing a YAML record alone does not
make a system numerically available.

## 8. Bibliographic References

The Fyskode Chaotic Systems Toolbox has been used as a numerical and graphical utility in preparation for dynamical systems research and manuscripts.

- X. Wang and G. Chen, "Constructing a chaotic system with any number of
  equilibria," *Nonlinear Dynamics*, 71, 429--436 (2013),
  DOI: 10.1007/s11071-012-0669-7.
- A. Bayani, M.-A. Jafari, S. Jafari, and V.-T. Pham, "A Comprehensive
  Analysis on the Wang-Chen System," in *Chaotic Systems with Multistability
  and Hidden Attractors* (2021),
  DOI: 10.1007/978-3-030-75821-9_23.
- F. Nazarimehr et al., "A New Chaotic System with Equilibria Located on a
  Line and Its Circuit Implementation," in the same volume (2021),
  DOI: 10.1007/978-3-030-75821-9_22.

---

Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.

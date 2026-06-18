# Research Use and Scientific Workflows

**Fyskode Chaotic Systems Toolbox** serves as a lightweight, reproducible environment for the exploratory analysis and numerical characterization of chaotic dynamical systems. This document outlines how researchers and instructors utilize the toolbox's core analytical capabilities.

## 1. Visual Phase Space and Trajectory Analysis

Researchers use the phase space visualization panels to:
- Generate high-resolution 2D and 3D phase portraits of trajectories.
- Study attractor shapes, projections, and time-evolution of states under varying initial conditions.
- Visualise time-series signals and analyze dynamical trends (convergence, periodicity, or chaotic fluctuations).
- Export publication-quality vector and raster graphics using consistent color palettes and layout settings.

## 2. Lyapunov Exponent Estimation

The estimation of Lyapunov exponents is critical for characterizing the sensitivity to initial conditions and the presence of chaos.
- **Spectrum Computation:** The toolbox implements numerical integration routines to compute the spectrum of Lyapunov exponents (for integer-order 3D and high-dimensional systems in the catalog).
- **Diagnostics:** Positive maximum exponents identify chaotic orbits, while zero and negative exponents classify stable limit cycles, quasiperiodic tori, or fixed points.
- **Verification:** Researchers use this panel to screen catalog parameters for chaotic windows.

## 3. Bifurcation sweeping

Bifurcation analysis reveals how system dynamics change as a control parameter varies.
- **Parametric Sweeps:** Users sweep one-dimensional parameters over continuous intervals, simulating trajectories from stable initial states.
- **Window Identification:** The resulting bifurcation diagrams help identify periodic windows, routes to chaos (e.g., period-doubling cascades), and sudden boundary crises.

## 4. Coexisting Attractors and Basins of Attraction

In multistable systems, different initial conditions converge to distinct coexisting attractors (e.g., chaotic attractors, limit cycles, or stable nodes).
- **Grid Sweeping:** The toolbox sweeps a grid of initial conditions on a user-selected 2D plane.
- **Basin Maps:** Each pixel on the grid is colored based on the final attractor destination, producing basin of attraction maps. This is an essential aid for researching hidden attractors, where the basin does not intersect any neighborhood of unstable equilibrium points.

## 5. Spectral Density (FFT Analysis)

- **Fourier Transform:** The FFT panel computes the power spectral density of time-series trajectories.
- **Signature Identification:** Smooth, discrete peaks in the FFT output represent periodic or quasiperiodic motion, whereas broadband noise distributions indicate chaotic dynamics.

## 6. Classroom and Educational Exploration

- **Historical Exploration:** The `Sprott Explorer` lets instructors and students load historical Sprott equations locally, providing a modern visual interface for educational exploration without distributing protected dictionary databases.
- **Equation Catalog:** A closed catalog of classical systems provides an interactive dictionary of chaotic dynamical equations, equilibrium points, and pre-calculated matrices for teaching.

## 7. Bibliographic References

The Fyskode Chaotic Systems Toolbox has been used by the author and collaborators as a numerical and graphical utility in preparation for publications and dynamic systems manuscripts.

`TODO: add bibliographic references to publications using the toolbox`

---

*Academic Warning: Numerical integrations and exponent calculations represent computational approximations (evidence) and must not be used as automatic mathematical proofs of chaos or the formal existence of attractors.*

# Reproducible Examples

This document describes step-by-step procedures to reproduce key simulations and analysis outputs using **Fyskode Chaotic Systems Toolbox 0.1.0**. 

Because the toolbox is designed primarily as a desktop GUI application, there are no user-facing command-line integration scripts. Reproducibility is achieved by loading predefined configurations from the internal catalog and running the numerical backend from the interface.

---

## 1. GUI Reproducibility Workflows

### Example A: Simulating the Lorenz Attractor
1. Launch the toolbox from source (`python main.py`) or run the installed executable.
2. In the system catalog panel (left sidebar), select **Lorenz** under the classical systems category.
3. Click the **Cargar parámetros por defecto** (Load Defaults) button. This loads:
   - Parameters: $\sigma = 10$, $\beta = 8/3$, $\rho = 28$
   - Initial conditions: $x_0 = 1$, $y_0 = 1$, $z_0 = 1$
   - Solver parameters: step size $h = 0.01$, integration time $T = 50$
4. Click the **Simular** (Simulate) button.
5. **Expected Output:** A 3D phase space trajectory of the Lorenz butterfly attractor will render on the canvas. You can rotate, zoom, and pan the 3D attractor.
6. **Export:** Click the **Exportar Figura** button in the canvas controls to save a `.png` of the current view to your designated results folder.

### Example B: Lyapunov Exponent Estimation for the Chen System
1. In the system catalog panel, select **Chen**.
2. Click **Cargar parámetros por defecto** to initialize parameters ($a=35, b=3, c=28$) and initial conditions ($x_0=-10, y_0=0, z_0=37$).
3. Navigate to the **Exponentes de Lyapunov** tab in the diagnostic panels.
4. Set the integration duration to a longer span (e.g., $N = 10000$ steps) to allow the QR orthonormalization method to converge.
5. Click **Calcular Exponentes**.
6. **Expected Output:** The calculated spectrum will converge to approximately:
   - $\lambda_1 > 0$ (finite-time evidence of expansion)
   - $\lambda_2 \approx 0$ (direction of the flow)
   - $\lambda_3 < 0$ (strong phase volume contraction)

Repeat the calculation with a smaller step and a longer horizon before
interpreting this sign pattern. It is a numerical diagnostic, not an automatic
proof of asymptotic chaos.

### Example C: Bifurcation sweep of the Rössler Attractor
1. Select **Rossler** from the system catalog.
2. Load defaults ($a = 0.2$, $b = 0.2$, $c = 5.7$).
3. Open the **Bifurcaciones** tab.
4. Select parameter $c$ as the sweep variable, setting the range from $2.0$ to $6.0$.
5. Select coordinate $z$ or $x$ as the projection variable.
6. Click **Iniciar Barrido** (Start Sweep).
7. **Expected Output:** A bifurcation diagram plotting the local maxima/minima of the trajectory against the parameter $c$, revealing periodic windows and chaotic bands.

### Example D: Wang--Chen multistable basin

1. Select **Wang-Chen (equilibrios variables)**.
2. Keep \(a=0.218\), RK4, \(h=0.01\), and open **Cuencas**.
3. Use the reference preset:
   \(z_0=0.4716\), \(x_0\in[-1,10]\), and
   \(y_0\in[-25,10]\).
4. Set \(T=200\). Increase the grid resolution only after a lower-resolution
   exploratory run.
5. **Expected topology:** an unbounded exterior region containing an
   interleaved bounded-residual region with detected periodic bands. The published
   periodic seed is \((3.022,1.196,1.643)\), and the chaotic seed is
   \((1.276,-0.190,0.471)\).

The implementation uses
\(\dot z=-y+3y^2-x^2-xz+a\). Equation (1) in the cited book chapter prints
\(-xy\), but its Jacobian, circuit, and the original system definition are
consistent with \(-xz\). The toolbox follows the chapter's
\(+a\) convention.

### Example E: Nazarimehr basin with a line of equilibria

1. Select **Nazarimehr (línea de equilibrios)**.
2. Keep \(k=-0.2\), RK4, \(h=0.01\), and open **Cuencas**.
3. Use \(z_0=0\), \(x_0\in[-2,4]\), \(y_0\in[-2,2]\), and \(T=200\).
4. **Expected topology:** a narrow wedge converging to
   \(E^*=\{(x,0,0):x\in\mathbb{R}\}\), surrounded by a bounded-residual
   region. The source reports the following chaotic seed:
   \((-1.53,0.33,0.39)\).

For this preset, convergence requires that the maximum orthogonal distance
to \(E^*\) over the second half of the integration be at most 0.05. This is a
declared finite-time numerical contract, not an asymptotic proof.

---

## 2. Automated CLI Verification

The repository contains automated scripts that act as developer-level reproducibility checks. They can be executed from a terminal to verify backend solver consistency and packaging states:

1. **Verify public release purity (Sprott copyright compliance):**
   ```powershell
   python scripts\verify_public_release_clean.py
   ```

2. **Execute smoke test suite (validates PyQt6 window rendering and core math flow):**
   ```powershell
   python scripts\smoke_test.py
   ```
3. **Run core unit tests:**
   ```powershell
   python -m pytest tests/test_native_backend.py -v
   ```

4. **Run the basin-system regression tests:**
   ```powershell
   python -m pytest tests/test_research_basin_systems.py -v
   ```

*Note: Headless environments must execute command-line tests with the environment variable `QT_QPA_PLATFORM=offscreen` set.*

# Reproducible Examples

This document describes step-by-step procedures to reproduce key simulations and analysis outputs using **Fyskode Chaotic Systems Toolbox 0.1.0**. 

Because the toolbox is designed primarily as a desktop GUI application, there are no user-facing command-line integration scripts. Reproducibility is achieved by loading predefined configurations from the internal catalog and running the numerical backend from the interface.

---

## 1. GUI Reproducibility Workflows

### Example A: Simulating the Lorenz Attractor
1. Launch the toolbox from source (`python main.py`) or run the installed executable.
2. Open the **Atractor 3D** tab.
3. In the left parameter panel of that tab, choose **Lorenz** in the **Sistema** selector. This loads:
   - Parameters: $\sigma = 10$, $\beta = 8/3$, $\rho = 28$
   - Initial conditions: $x_0 = y_0 = z_0 = 0.1$
   - Solver parameters: step size $dt = 0.01$, integration time $T = 40$
4. Click **Generar atractor 3D**.
5. **Expected output:** A finite-time 3D Lorenz trajectory renders on the canvas. You can rotate, zoom, and pan the view.
6. **Export:** Click **Guardar gráfica...** and choose the destination and supported image format.

### Example B: Lyapunov Exponent Estimation for the Chen System
1. Open the **Lyapunov** tab.
2. In the left parameter panel of that tab, choose **Chen** in the **Sistema** selector. This loads parameters ($a=35, b=3, c=28$) and initial conditions ($x_0=y_0=z_0=0.1$).
3. Set `dt`, **Burn-in time**, **Tiempo final**, and **QR cada N pasos**. The integrator is fixed to RK4; keep both time values exact integer multiples of `dt`.
4. Click **Calcular exponentes de Lyapunov**.
5. **Interpretation:** A sufficiently resolved finite-time spectrum is commonly expected to show:
   - $\lambda_1 > 0$ (finite-time evidence of expansion)
   - $\lambda_2 \approx 0$ (direction of the flow)
   - $\lambda_3 < 0$ (strong phase volume contraction)

Repeat the calculation with a smaller step and a longer horizon before
interpreting this sign pattern. It is a numerical diagnostic, not an automatic
proof of asymptotic chaos.

### Example C: Bifurcation sweep of the Rössler Attractor
1. Open the **Bifurcación** tab.
2. In the left parameter panel of that tab, choose **Rossler** in the **Sistema** selector. This loads defaults ($a = 0.2$, $b = 0.2$, $c = 5.7$).
3. Select parameter $c$ as the sweep variable, setting the range from $2.0$ to $6.0$.
4. Select coordinate $z$ or $x$ as the projection variable.
5. Click **Calcular bifurcación**.
6. **Expected output:** The diagram plots detected local maxima of the selected coordinate against $c$. Apparent bands and windows are finite-resolution screening evidence and depend on the declared transitory, useful time, step, and sampling density.

### Example D: Wang--Chen multistable basin

1. Open the **Cuenca de atracción** tab.
2. In the left parameter panel of that tab, choose **Wang-Chen (equilibrios variables)** in the **Sistema** selector.
3. Keep \(a=0.218\), RK4, and \(h=0.01\), then use the reference preset:
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

1. Open the **Cuenca de atracción** tab.
2. In the left parameter panel of that tab, choose **Nazarimehr (línea de equilibrios)** in the **Sistema** selector.
3. Keep \(k=-0.2\), RK4, and \(h=0.01\); use \(z_0=0\), \(x_0\in[-2,4]\), \(y_0\in[-2,2]\), and \(T=200\).
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

2. **Execute smoke test suite (validates PySide6 window rendering and core math flow):**
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

*Note: Headless environments can execute ordinary Qt tests with
`QT_QPA_PLATFORM=offscreen`. Qt WebEngine construction requires a viable
display platform and is exercised separately under a virtual display in CI.*

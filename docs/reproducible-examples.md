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
   - $\lambda_1 > 0$ (confirming chaotic expansion)
   - $\lambda_2 \approx 0$ (direction of the flow)
   - $\lambda_3 < 0$ (strong phase volume contraction)

### Example C: Bifurcation sweep of the Rössler Attractor
1. Select **Rossler** from the system catalog.
2. Load defaults ($a = 0.2$, $b = 0.2$, $c = 5.7$).
3. Open the **Bifurcaciones** tab.
4. Select parameter $c$ as the sweep variable, setting the range from $2.0$ to $6.0$.
5. Select coordinate $z$ or $x$ as the projection variable.
6. Click **Iniciar Barrido** (Start Sweep).
7. **Expected Output:** A bifurcation diagram plotting the local maxima/minima of the trajectory against the parameter $c$, revealing periodic windows and chaotic bands.

---

## 2. Automated CLI Verification

The repository contains automated scripts that act as developer-level reproducibility checks. They can be executed from a terminal to verify backend solver consistency and packaging states:

1. **Verify metadata constraints:**
   ```powershell
   python scripts\verify_joss_metadata.py
   ```
2. **Verify public release purity (Sprott copyright compliance):**
   ```powershell
   python scripts\verify_public_release_clean.py
   ```
3. **Execute smoke test suite (validates PyQt6 window rendering and core math flow):**
   ```powershell
   python scripts\smoke_test.py
   ```
4. **Run core unit tests:**
   ```powershell
   python -m pytest tests/test_native_backend.py -v
   ```

*Note: Headless environments must execute command-line tests with the environment variable `QT_QPA_PLATFORM=offscreen` set.*

# Chaos Theory Toolbox

Interactive desktop toolbox for exploring nonlinear dynamical systems and chaos theory.

## Included systems

- Continuous flows: Lorenz, Rossler, Chua, Chen, Lu, Duffing-Ueda, Rabinovich-Fabrikant, Rikitake, Sprott A, Thomas, Hindmarsh-Rose.
- Discrete maps: Henon, logistic, Ikeda.
- Other models: Mackey-Glass delay equation and Lorenz-96 high-dimensional ring model.

The app shows trajectory projections, time series, 3D attractor views, bifurcation diagrams, equilibrium/eigenvalue views, and attraction-basin grids where the model type supports them. Implemented systems run the heavy trajectory, bifurcation, and attraction-basin calculations through the native C backend. Independent bifurcation sweeps and basin rows are split across multiple worker processes; continuation sweeps stay sequential because each parameter step depends on the previous final state.

## Requirements

- Python 3.12 or compatible
- PyQt6
- NumPy
- Matplotlib
- pyqtgraph

Install dependencies with:

```powershell
python -m pip install -r requirements.txt
```

## Run

From PowerShell:

```powershell
.\run.ps1
```

Or directly:

```powershell
python main.py
```

## Project Structure

- `main.py`: application entry point.
- `ui/`: PyQt6 interface, canvases, widgets, and rendering helpers.
- `core/`: numerical routines and native backend integration.
- `assets/`: supporting educational/reference materials.

# Chaos Theory Toolbox

Interactive desktop toolbox for exploring nonlinear dynamical systems and chaos theory.

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

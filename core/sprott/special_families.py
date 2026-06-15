from __future__ import annotations

import math
import numpy as np


class SpecialFamily:
    """Base class for educational, independent reimplementation of Sprott's special families."""
    letter: str
    name: str
    dimension: int
    coefficient_count: int
    kind: str = "special"

    def __init__(self, coefficients: list[float]):
        self.coefficients = coefficients
        self.warnings: list[str] = []

    def step(self, state: list[float] | np.ndarray, n: int, nmax: int) -> list[float]:
        """Perform a single iterative step."""
        raise NotImplementedError("Each special family must implement the step method.")

    def equations_text(self) -> str:
        """Return a formatted string representing the system equations."""
        raise NotImplementedError("Each special family must implement the equations_text method.")

    def simulate(self, initial: list[float] | np.ndarray, n_iter: int, divergence_threshold: float = 1e6) -> np.ndarray:
        """Simulate the trajectory of the special family map."""
        trajectory = []
        state = list(initial)
        
        # Ensure state has length 4
        if len(state) < 4:
            state = state + [0.1] * (4 - len(state))
        elif len(state) > 4:
            state = state[:4]
            
        trajectory.append(state)
        
        for n in range(1, n_iter):
            try:
                state = self.step(state, n, n_iter)
            except (OverflowError, ValueError, ZeroDivisionError):
                state = [float('inf'), float('inf'), float('inf'), float('inf')]
            
            # Check for non-finite values early
            if not all(math.isfinite(x) for x in state):
                state = [float('inf'), float('inf'), float('inf'), float('inf')]
                trajectory.append(state)
                break
                
            trajectory.append(state)
            
            # Check for divergence threshold crossing
            if any(abs(x) > divergence_threshold for x in state):
                break
                
        return np.array(trajectory, dtype=float)


class AbsoluteValueFamily(SpecialFamily):
    letter = "Y"
    name = "Absolute value special family Y"
    dimension = 4
    coefficient_count = 10
    kind = "special"

    def step(self, state: list[float] | np.ndarray, n: int, nmax: int) -> list[float]:
        x, y, z, w = state
        a = self.coefficients
        x_new = a[0] + a[1] * x + a[2] * y + a[3] * abs(x) + a[4] * abs(y)
        y_new = a[5] + a[6] * x + a[7] * y + a[8] * abs(x) + a[9] * abs(y)
        z_new = x_new**2 + y_new**2
        w_new = (n - 1000) / (nmax - 1000) if nmax > 1000 else 0.0
        return [x_new, y_new, z_new, w_new]

    def equations_text(self) -> str:
        a = self.coefficients
        return (
            f"X' = {a[0]:.2f} + {a[1]:.2f}*X + {a[2]:.2f}*Y + {a[3]:.2f}*|X| + {a[4]:.2f}*|Y|\n"
            f"Y' = {a[5]:.2f} + {a[6]:.2f}*X + {a[7]:.2f}*Y + {a[8]:.2f}*|X| + {a[9]:.2f}*|Y|\n"
            f"Z' = X^2 + Y^2\n"
            f"W' = (N - 1000) / (NMAX - 1000)"
        )


class PowerAbsoluteFamily(SpecialFamily):
    letter = "["
    name = "Power absolute special family ["
    dimension = 4
    coefficient_count = 14
    kind = "special"

    def step(self, state: list[float] | np.ndarray, n: int, nmax: int) -> list[float]:
        x, y, z, w = state
        a = self.coefficients
        
        def safe_abs_pow(val, exp):
            base = abs(val)
            if base == 0.0 and exp < 0:
                return float('inf')
            res = base ** exp
            if not math.isfinite(res):
                return float('inf')
            return res

        x_new = a[0] + a[1] * x + a[2] * y + a[3] * safe_abs_pow(x, a[4]) + a[5] * safe_abs_pow(y, a[6])
        y_new = a[7] + a[8] * x + a[9] * y + a[10] * safe_abs_pow(x, a[11]) + a[12] * safe_abs_pow(y, a[13])
        z_new = x_new**2 + y_new**2
        w_new = (n - 1000) / (nmax - 1000) if nmax > 1000 else 0.0
        return [x_new, y_new, z_new, w_new]

    def equations_text(self) -> str:
        a = self.coefficients
        return (
            f"X' = {a[0]:.2f} + {a[1]:.2f}*X + {a[2]:.2f}*Y + {a[3]:.2f}*|X|^{a[4]:.2f} + {a[5]:.2f}*|Y|^{a[6]:.2f}\n"
            f"Y' = {a[7]:.2f} + {a[8]:.2f}*X + {a[9]:.2f}*Y + {a[10]:.2f}*|X|^{a[11]:.2f} + {a[12]:.2f}*|Y|^{a[13]:.2f}\n"
            f"Z' = X^2 + Y^2\n"
            f"W' = (N - 1000) / (NMAX - 1000)"
        )


class SineFamily(SpecialFamily):
    letter = "\\"
    name = "Sine special family \\"
    dimension = 4
    coefficient_count = 18
    kind = "special"

    def step(self, state: list[float] | np.ndarray, n: int, nmax: int) -> list[float]:
        x, y, z, w = state
        a = self.coefficients
        x_new = a[0] + a[1]*x + a[2]*y + a[3]*math.sin(a[4]*x + a[5]) + a[6]*math.sin(a[7]*y + a[8])
        y_new = a[9] + a[10]*x + a[11]*y + a[12]*math.sin(a[13]*x + a[14]) + a[15]*math.sin(a[16]*y + a[17])
        z_new = x_new**2 + y_new**2
        w_new = (n - 1000) / (nmax - 1000) if nmax > 1000 else 0.0
        return [x_new, y_new, z_new, w_new]

    def equations_text(self) -> str:
        a = self.coefficients
        return (
            f"X' = {a[0]:.2f} + {a[1]:.2f}*X + {a[2]:.2f}*Y + {a[3]:.2f}*sin({a[4]:.2f}*X + {a[5]:.2f}) + {a[6]:.2f}*sin({a[7]:.2f}*Y + {a[8]:.2f})\n"
            f"Y' = {a[9]:.2f} + {a[10]:.2f}*X + {a[11]:.2f}*Y + {a[12]:.2f}*sin({a[13]:.2f}*X + {a[14]:.2f}) + {a[15]:.2f}*sin({a[16]:.2f}*Y + {a[17]:.2f})\n"
            f"Z' = X^2 + Y^2\n"
            f"W' = (N - 1000) / (NMAX - 1000)"
        )


class RotationalSineFamily(SpecialFamily):
    letter = "]"
    name = "Rotational sine special family ]"
    dimension = 4
    coefficient_count = 6
    kind = "special"

    def step(self, state: list[float] | np.ndarray, n: int, nmax: int) -> list[float]:
        x, y, z, w = state
        a = self.coefficients
        
        denom = 13.0 + 10.0 * a[5]
        if abs(denom) < 1e-9:
            theta = 0.0
            if "Denominador de theta cercano a cero: se usó theta = 0." not in self.warnings:
                self.warnings.append("Denominador de theta cercano a cero: se usó theta = 0.")
        else:
            theta = 2.0 * math.pi / denom
            
        term = x + a[1] * math.sin(a[2] * y + a[3])
        x_new = 10.0 * a[0] + term * math.cos(theta) + y * math.sin(theta)
        y_new = 10.0 * a[4] - term * math.sin(theta) + y * math.cos(theta)
        z_new = x_new**2 + y_new**2
        w_new = (n - 1000) / (nmax - 1000) if nmax > 1000 else 0.0
        return [x_new, y_new, z_new, w_new]

    def equations_text(self) -> str:
        a = self.coefficients
        denom = 13.0 + 10.0 * a[5]
        theta_str = f"2*pi / {denom:.2f}" if abs(denom) >= 1e-9 else "0.0 (error de division)"
        return (
            f"theta = {theta_str}\n"
            f"X' = 10*{a[0]:.2f} + [X + {a[1]:.2f}*sin({a[2]:.2f}*Y + {a[3]:.2f})] * cos(theta) + Y * sin(theta)\n"
            f"Y' = 10*{a[4]:.2f} - [X + {a[1]:.2f}*sin({a[2]:.2f}*Y + {a[3]:.2f})] * sin(theta) + Y * cos(theta)\n"
            f"Z' = X^2 + Y^2\n"
            f"W' = (N - 1000) / (NMAX - 1000)"
        )


class ForcedOscillatorFamily(SpecialFamily):
    letter = "^"
    name = "Forced oscillator special family ^"
    dimension = 4
    coefficient_count = 9
    kind = "special"

    def step(self, state: list[float] | np.ndarray, n: int, nmax: int) -> list[float]:
        x, y, z, w = state
        a = self.coefficients
        x_new = x + 0.1 * a[0] * y
        y_new = y + 0.1 * (a[1]*x + a[2]*(x**3) + a[3]*(x**2)*y + a[4]*x*(y**2) + a[5]*y + a[6]*(y**3) + a[7]*math.sin(z))
        z_new = (z + 0.1 * (a[8] + 1.3)) % (2.0 * math.pi)
        w_new = (n - 1000) / (nmax - 1000) if nmax > 1000 else 0.0
        return [x_new, y_new, z_new, w_new]

    def equations_text(self) -> str:
        a = self.coefficients
        return (
            f"X' = X + 0.1*{a[0]:.2f}*Y\n"
            f"Y' = Y + 0.1*({a[1]:.2f}*X + {a[2]:.2f}*X^3 + {a[3]:.2f}*X^2*Y + {a[4]:.2f}*X*Y^2 + {a[5]:.2f}*Y + {a[6]:.2f}*Y^3 + {a[7]:.2f}*sin(Z))\n"
            f"Z' = (Z + 0.1*({a[8]:.2f} + 1.3)) mod 2*pi\n"
            f"W' = (N - 1000) / (NMAX - 1000)"
        )


SPECIAL_FAMILY_REGISTRY = {
    "Y": AbsoluteValueFamily,
    "[": PowerAbsoluteFamily,
    "\\": SineFamily,
    "]": RotationalSineFamily,
    "^": ForcedOscillatorFamily,
    "Z": {
        "name": "AND/OR special family",
        "status": "pending_semantics_validation"
    }
}

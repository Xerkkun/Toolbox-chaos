# Explorador Sprott

## What is a strange attractor?

A strange attractor is a long-term geometric pattern produced by a deterministic
system whose nearby trajectories separate in a sensitive way. The orbit remains
bounded, but it does not settle to a simple equilibrium or a short periodic
cycle. This makes the object useful both as a mathematical diagnostic and as a
visual signature of nonlinear dynamics.

$$\|x_n-y_n\|\approx \|x_0-y_0\|e^{\lambda n}$$

## What did Sprott's software explore?

Sprott's historical software made it practical to search large families of
compactly encoded equations and visualize the resulting dynamics. The important
idea for this toolbox is not to copy that implementation, but to preserve the
research pattern: generate a compact code, decode it into equations, simulate,
filter, and visualize.

## Discrete maps

A map updates a state directly from one step to the next. In a polynomial map,
each next variable is a weighted sum of monomials such as `1`, `x`, `y`, `x^2`,
or `x*y`. Iterating the map can reveal fixed points, cycles, or bounded
irregular motion.

$$x_{n+1}=F(x_n), \qquad F_i(x)=\sum_j c_{ij}m_j(x)$$

## Continuous flows

A flow defines derivatives such as `dx/dt`, `dy/dt`, and `dz/dt`. This module
supports polynomial right-hand sides and integrates them with Euler or RK4.
Euler with larger historical steps is useful for comparison, while RK4 is a
modern numerical option for cleaner experiments.

$$\dot{x}=F(x), \qquad x(t+h)\approx x(t)+hF(x(t))$$

## Compact codes

The first character selects a family: dimension, order, and whether the system
is a map or a flow. Later characters encode coefficients. In this first phase,
families A-X cover polynomial maps and flows; special-function families are
documented as pending.

$$c=\frac{\operatorname{ord}(\mathrm{letter})-77}{10}$$

## Automatic search

Automatic search generates many coefficient strings, simulates them, rejects
divergent or collapsed trajectories, and keeps bounded candidates for deeper
diagnostics. The current implementation is deliberately small and synchronous;
future versions can move search into a worker thread.

## Maximum Lyapunov exponent

A positive maximum Lyapunov estimate is a useful early filter for sensitive
dependence. It is not a final proof of chaos. This toolbox uses a simple
two-trajectory estimate for quick screening and reserves full spectra for a
later phase.

## Fractal and correlation dimensions

Dimension estimates describe how an attractor fills space across scales. They
are sensitive to data length, noise, transients, and sampling. This phase keeps
clean placeholders for correlation dimension and Kaplan-Yorke dimension.

$$C(r)=\frac{2}{N(N-1)}\sum_{i<j}\mathbf{1}\{\|x_i-x_j\|<r\}$$

## 2D, 3D, and 4D visualization

Low-dimensional systems can be plotted directly. Four-dimensional systems need
projections, component views, or interactive slicing. The explorer starts with
2D projections and stores enough metadata to add richer views later.

## Art and science

Sprott's work is important because the same computation can support rigorous
experiments and striking visual forms. Chaos Toolbox treats images as evidence
only when paired with equations, parameters, simulation settings, and metrics.

## Modern extensions

Planned extensions include detailed `.DIC` import from user-local files,
thumbnail generation, background search workers, full Lyapunov spectra,
correlation dimension, and side-by-side comparison with historical references
loaded locally by the user.

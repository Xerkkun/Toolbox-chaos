# Code Grammar

## Family letters

$$
\begin{array}{c c c c c}
\mathrm{Letters} & \mathrm{Kind} & \mathrm{Dimension} & \mathrm{Coefficients} & \mathrm{Description}\\
A-D & \mathrm{Polynomial\ map} & 1 & D \times \binom{D+O}{O} & \mathrm{Orders\ 2,3,4,5}\\
E-H & \mathrm{Polynomial\ map} & 2 & D \times \binom{D+O}{O} & \mathrm{Orders\ 2,3,4,5}\\
I-L & \mathrm{Polynomial\ map} & 3 & D \times \binom{D+O}{O} & \mathrm{Orders\ 2,3,4,5}\\
M-P & \mathrm{Polynomial\ map} & 4 & D \times \binom{D+O}{O} & \mathrm{Orders\ 2,3,4,5}\\
Q-T & \mathrm{Polynomial\ flow} & 3 & D \times \binom{D+O}{O} & \mathrm{Orders\ 2,3,4,5}\\
U-X & \mathrm{Polynomial\ flow} & 4 & D \times \binom{D+O}{O} & \mathrm{Orders\ 2,3,4,5}\\
Y & \mathrm{Special\ map} & 4 & 10 & \mathrm{Absolute\ Values}\\
[ & \mathrm{Special\ map} & 4 & 14 & \mathrm{Power\ Absolute\ Values}\\
\backslash & \mathrm{Special\ map} & 4 & 18 & \mathrm{Sine\ functions}\\
] & \mathrm{Special\ map} & 4 & 6 & \mathrm{Rotational\ Sine}\\
^ & \mathrm{Special\ map} & 4 & 9 & \mathrm{Forced\ Oscillator\ Map}\\
Z & \mathrm{Special\ map} & 4 & 10 & \mathrm{AND/OR\ (Pending\ validation)}
\end{array}
$$

Within each four-letter polynomial group (A-X), the first letter means order 2, the second order
3, the third order 4, and the fourth order 5.

## Coefficients

After the family letter, each character encodes one coefficient with the initial
rule:

`coefficient = (ord(character) - 77) / 10`

This maps `M` to `0.0`, `A` to `-1.2`, and `Y` to `1.2`.

## Monomial count

For dimension `D` and polynomial order `O`, the monomial basis contains:

`comb(D + O, O)`

$$N_m=\binom{D+O}{O}$$

The basis includes the constant term and all monomials with total degree less
than or equal to `O`.

## Coefficient count

Maps and flows both use one polynomial for each state component, so the
coefficient count is:

`D * comb(D + O, O)`

$$N_c=D\binom{D+O}{O}$$

For example, a 2D quadratic map needs `2 * comb(4, 2) = 12` coefficients. Special families use a fixed number of coefficients (10, 14, 18, 6, 9) as specified in their formulas.

## Familias especiales implementadas

This project includes a modern, clean, and independent educational reimplementation of Sprott's special-function families:
- **A-X**: Polynomial maps and flows.
- **Y, `[`, `\`, `]`, `^`**: Non-polynomial special families with absolute values, powers, sines, rotations, and forced oscillator integrations.
- **Z**: A special-function family using AND/OR logic, which remains pending semantics validation.

These implementations are developed from the mathematical equations described in Appendix E of *Strange Attractors* for study and visualization, with no copy of original software source code.

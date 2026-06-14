# Code Grammar

## Family letters

$$
\begin{array}{c c c c}
\mathrm{Letters} & \mathrm{Kind} & \mathrm{Dimension} & \mathrm{Orders}\\
A-D & \mathrm{Polynomial\ map} & 1 & 2,3,4,5\\
E-H & \mathrm{Polynomial\ map} & 2 & 2,3,4,5\\
I-L & \mathrm{Polynomial\ map} & 3 & 2,3,4,5\\
M-P & \mathrm{Polynomial\ map} & 4 & 2,3,4,5\\
Q-T & \mathrm{Polynomial\ flow} & 3 & 2,3,4,5\\
U-X & \mathrm{Polynomial\ flow} & 4 & 2,3,4,5\\
Y-Z & \mathrm{Special\ functions} & \mathrm{pending} & \mathrm{pending}
\end{array}
$$

Within each four-letter group, the first letter means order 2, the second order
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

For example, a 2D quadratic map needs `2 * comb(4, 2) = 12` coefficients.

## Pending families

Special-function families are intentionally documented but not implemented in
this phase. They should be added only as independent implementations with clear
attribution and tests.

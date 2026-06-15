# 02 - Mapas Iterados

Un **mapa iterado** es un sistema dinámico discreto gobernado por una regla de recurrencia:

$$x_{n+1} = F(x_n), \qquad x_n \in \mathbb{R}^D$$

Donde cada estado sucesivo se obtiene aplicando directamente la función al estado actual.

## Representación por Base Monomial
Para representar mapas no lineales arbitrarios en la toolbox, las componentes de $F(x)$ se expanden como una combinación lineal de monomios de grado total menor o igual al orden polinomial $O$. Para dimensión $D$ y orden $O$, el número de monomios de la base es:

$$N_m = \binom{D+O}{O}$$

### Base en 2D de Orden 2
Para la familia polinomial cuadrática 2D (`E`), los 6 monomios correspondientes son:
$$\mathcal{M}_{2,2} = \{1, x, y, x^2, xy, y^2\}$$
Las ecuaciones del mapa se definen mediante 12 coeficientes:
$$x_{n+1} = a_0 + a_1 x_n + a_2 y_n + a_3 x_n^2 + a_4 x_n y_n + a_5 y_n^2$$
$$y_{n+1} = b_0 + b_1 x_n + b_2 y_n + b_3 x_n^2 + b_4 x_n y_n + b_5 y_n^2$$

## El Transitorio
Al iniciar la iteración desde una condición inicial arbitraria $x_0$, la trayectoria tarda un número de pasos $N_T$ en converger a la estructura atractora estable (el conjunto límite). Este tramo se denomina **transitorio** y debe descartarse para poder visualizar la geometría persistente y limpia del atractor fractal.

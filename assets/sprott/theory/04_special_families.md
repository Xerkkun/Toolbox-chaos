# 04 - Familias Especiales No Polinomiales

Las familias especiales implementan dinámicas discontinuas o de base trigonométrica en dimensiones efectivas 2D, expandiendo su estado a 4D para visualización:

- **Familia `Y` (Valores Absolutos):**
  $$x_{n+1} = a_0 + a_1 x_n + a_2 y_n + a_3 |x_n| + a_4 |y_n|$$
  $$y_{n+1} = a_5 + a_6 x_n + a_7 y_n + a_8 |x_n| + a_9 |y_n|$$
  $$z_{n+1} = x_{n+1}^2 + y_{n+1}^2$$
  $$w_{n+1} = \frac{n - 1000}{N_{\max} - 1000}$$

- **Familia `[` (Potencia de Valores Absolutos):**
  $$x_{n+1} = a_0 + a_1 x_n + a_2 y_n + a_3 |x_n|^{a_4} + a_5 |y_n|^{a_6}$$
  $$y_{n+1} = a_7 + a_8 x_n + a_9 y_n + a_{10} |x_n|^{a_{11}} + a_{12} |y_n|^{a_{13}}$$
  $$z_{n+1} = x_{n+1}^2 + y_{n+1}^2$$
  $$w_{n+1} = \frac{n - 1000}{N_{\max} - 1000}$$
  *(Contiene protección de división por cero si base es 0 y exponente es negativo).*

- **Familia `\` (Senos):**
  $$x_{n+1} = a_0 + a_1 x_n + a_2 y_n + a_3 \sin(a_4 x_n + a_5) + a_6 \sin(a_7 y_n + a_8)$$
  $$y_{n+1} = a_9 + a_{10} x_n + a_{11} y_n + a_{12} \sin(a_{13} x_n + a_{14}) + a_{15} \sin(a_{16} y_n + a_{17})$$
  $$z_{n+1} = x_{n+1}^2 + y_{n+1}^2$$
  $$w_{n+1} = \frac{n - 1000}{N_{\max} - 1000}$$

- **Familia `]` (Seno Rotacional):**
  $$\theta = \frac{2\pi}{13 + 10a_5}$$
  $$u_n = x_n + a_1 \sin(a_2 y_n + a_3)$$
  $$x_{n+1} = 10a_0 + u_n \cos\theta + y_n \sin\theta$$
  $$y_{n+1} = 10a_4 - u_n \sin\theta + y_n \cos\theta$$
  $$z_{n+1} = x_{n+1}^2 + y_{n+1}^2$$
  $$w_{n+1} = \frac{n - 1000}{N_{\max} - 1000}$$

- **Familia `^` (Oscilador Forzado):**
  $$x_{n+1} = x_n + 0.1 a_0 y_n$$
  $$y_{n+1} = y_n + 0.1 (a_1 x_n + a_2 x_n^3 + a_3 x_n^2 y_n + a_4 x_n y_n^2 + a_5 y_n + a_6 y_n^3 + a_7 \sin z_n)$$
  $$z_{n+1} = (z_n + 0.1(a_8 + 1.3)) \bmod 2\pi$$
  $$w_{n+1} = \frac{n - 1000}{N_{\max} - 1000}$$

- **Familia `Z` (Lógica AND/OR):**
  El parser reconoce la familia de 10 coeficientes, pero el simulador la
  mantiene deshabilitada: el contrato público actual no especifica una
  semántica numérica validada. La interfaz comunica esta limitación en lugar de
  producir una trayectoria ambigua.

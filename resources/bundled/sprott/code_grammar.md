# Gramática de Códigos del Explorador Sprott

Este documento detalla la estructura sintáctica de los códigos compactos que el **Explorador Sprott** utiliza para parametrizar de forma compacta y reproducible las ecuaciones de sus sistemas dinámicos.

---

## 1. Letras de Familia

El primer carácter del código (siempre una letra o un símbolo especial) determina la **familia** del sistema dinámico. Las familias se dividen en polinomiales estándar (`A-X`) y especiales no polinomiales (`Y`, `[`, `\`, `]`, `^`, `Z`).

### Familias Polinomiales Estándar

Las familias polinomiales se agrupan en bloques de 4 letras. Cada bloque comparte la misma dimensión y tipo (mapa o flujo). Dentro de cada bloque, las letras sucesivas representan órdenes polinomiales crecientes del 2 al 5:

$$
\begin{array}{c c c c l}
\text{Letras} & \text{Tipo} & \text{Dimensión} & \text{Ordenes} & \text{Estructura} \\
\hline
\text{A - D} & \text{Mapa polinomial} & 1 & 2, 3, 4, 5 & x_{n+1} = P_O(x_n) \\
\text{E - H} & \text{Mapa polinomial} & 2 & 2, 3, 4, 5 & (x, y)_{n+1} = (P_O(x, y), Q_O(x, y)) \\
\text{I - L} & \text{Mapa polinomial} & 3 & 2, 3, 4, 5 & (x, y, z)_{n+1} = (P_O(x,y,z), Q_O(x,y,z), R_O(x,y,z)) \\
\text{M - P} & \text{Mapa polinomial} & 4 & 2, 3, 4, 5 & (x, y, z, w)_{n+1} = (P_O(x,y,z,w), \ldots) \\
\text{Q - T} & \text{Flujo polinomial} & 3 & 2, 3, 4, 5 & (\dot{x}, \dot{y}, \dot{z}) = (P_O(x,y,z), Q_O(x,y,z), R_O(x,y,z)) \\
\text{U - X} & \text{Flujo polinomial} & 4 & 2, 3, 4, 5 & (\dot{x}, \dot{y}, \dot{z}, \dot{w}) = (P_O(x,y,z,w), \ldots)
\end{array}
$$

*Nota didáctica:* La primera letra de cada grupo (A, E, I, M, Q, U) representa orden 2 (cuadrático); la segunda representa orden 3 (cúbico); la tercera, orden 4; y la cuarta, orden 5 (quíntico).

### Familias Especiales No Polinomiales

Las familias especiales implementan dinámicas específicas con funciones no lineales complejas (valores absolutos, senos, rotaciones y osciladores forzados) y cuentan con un número fijo de coeficientes.

- **`Y` (Especial - Valores Absolutos):** Mapa 4D con 10 coeficientes.
- **`[` (Especial - Potencia de Valores Absolutos):** Mapa 4D con 14 coeficientes.
- **`\` (Especial - Senos):** Mapa 4D con 18 coeficientes.
- **`]` (Especial - Seno Rotacional):** Mapa 4D con 6 coeficientes.
- **`^` (Especial - Oscilador Forzado):** Mapa 4D con 9 coeficientes.
- **`Z` (Especial - Lógica AND/OR):** Mapa 4D con 10 coeficientes *(pendiente de validación semántica en la simulación).*

---

## 2. Decodificación de Coeficientes

A partir del segundo carácter, cada símbolo individual del código representa un coeficiente del sistema dinámico. El carácter se convierte a un valor decimal mediante la fórmula:

$$\text{coeficiente} = \frac{\operatorname{ord}(\text{carácter}) - 77}{10}$$

Donde $\operatorname{ord}(\cdot)$ devuelve el valor ASCII del carácter.

Ejemplos comunes de correspondencia:
- El carácter `M` (ASCII 77) equivale a `0.0`.
- El carácter `A` (ASCII 65) equivale a `-1.2`.
- El carácter `Y` (ASCII 89) equivale a `1.2`.
- Los caracteres anteriores a `M` codifican coeficientes negativos.
- Los caracteres posteriores a `M` codifican coeficientes positivos.

---

## 3. Conteo de Monomios y Coeficientes

Para una dimensión dada $D$ y un orden polinomial $O$, el número de monomios distintos en la base (que incluye el término constante) es:

$$N_m = \binom{D + O}{O}$$

Como el sistema requiere definir una ecuación diferencial o una regla de iteración independiente para cada una de las $D$ componentes de estado, el número total de coeficientes esperados $N_c$ es:

$$N_c = D \binom{D + O}{O}$$

### Ejemplo de Conteo
Para un mapa de la familia **`E`** (Mapa polinomial 2D de orden 2):
- Dimensión $D = 2$, Orden $O = 2$.
- Monomios en la base: $N_m = \binom{2+2}{2} = 6$. Monomios: $\{1, x_n, y_n, x_n^2, x_n y_n, y_n^2\}$.
- Número total de coeficientes: $N_c = 2 \times 6 = 12$ coeficientes.
- Un código de la familia `E` con sus 12 coeficientes completos requiere 13 caracteres en total (por ejemplo, `EWMWAMMMPMMMM`).

---

## 4. Diferencia Importante: Familias de Codificación A-X vs. Flujos Clásicos Sprott A-S

> [!WARNING]
> Existe una distinción crucial en la nomenclatura de la literatura:
> - **Familias de codificación `A-X`:** Son los identificadores del sistema de código compacto de la toolbox para mapas y flujos polinomiales arbitrarios de dimensiones 1 a 4 y órdenes 2 a 5.
> - **Sistemas clásicos Sprott `A-S`:** Son diecinueve modelos de flujos caóticos tridimensionales algebraicamente simples presentados por Julien C. Sprott en su artículo original de 1994 (*Some simple chaotic flows*). Estos flujos se describen con ecuaciones explícitas y no coinciden con las familias de codificación polinomial directa `A-S` de la toolbox.

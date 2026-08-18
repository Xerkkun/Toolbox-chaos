# 03 - Flujos Polinomiales e Integración Numérica

Un **flujo dinámico continuo** se modela mediante un sistema de ecuaciones diferenciales ordinarias (EDO) autónomas:

$$\dot{x} = f(x), \qquad x(t) \in \mathbb{R}^D$$

Donde $f(x)$ representa un campo vectorial en el espacio de fases de dimensión $D$. En Chaos Toolbox, las componentes de $f(x)$ se definen mediante combinaciones de monomios de base polinomial.

## Métodos de Integración Numérica

Como normalmente no se dispone de una solución cerrada útil para el horizonte
de interés, la trayectoria se aproxima discretizando el tiempo en pasos fijos
de tamaño $h$:

### 1. Método de Euler (Primer Orden)
Es el esquema más sencillo y requiere una evaluación del campo por paso, pero
tiene mayor error de truncamiento local (de orden $\mathcal{O}(h^2)$):
$$x_{k+1} = x_k + h f(x_k)$$

### 2. Método de Heun (Segundo Orden)

Heun combina una predicción de Euler con una corrección trapezoidal:
$$x^* = x_k + h f(x_k), \qquad
x_{k+1} = x_k + \frac{h}{2}\left(f(x_k)+f(x^*)\right).$$

### 3. Método de Runge-Kutta de 4º Orden (RK4)
Es un estándar clásico de alta fidelidad que reduce significativamente el error de truncamiento local (a orden $\mathcal{O}(h^5)$). Requiere evaluar el campo vectorial en cuatro puntos intermedios por cada paso temporal:
$$\begin{aligned}
k_1 &= f(x_k) \\
k_2 &= f\left(x_k + \frac{h}{2} k_1\right) \\
k_3 &= f\left(x_k + \frac{h}{2} k_2\right) \\
k_4 &= f(x_k + h k_3) \\
x_{k+1} &= x_k + \frac{h}{6}(k_1 + 2k_2 + 2k_3 + k_4)
\end{aligned}$$

*Importancia didáctica:* RK4 suele reducir el error local frente a Euler y
Heun, pero no elimina inestabilidad, error acumulado ni sensibilidad al paso.
Una interpretación científica requiere repetir con pasos menores, comparar
métodos y declarar el horizonte y los umbrales usados.

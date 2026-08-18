# Teoría del Explorador Sprott

Esta página resume el marco teórico que fundamenta el módulo **Explorador Sprott** de Chaos Toolbox. La herramienta está inspirada en el trabajo pionero de Julien C. Sprott, especialmente en su libro *Strange Attractors: Creating Patterns in Chaos* (1993) y sus artículos científicos posteriores. El software es una reimplementación educativa e independiente que no distribuye los diccionarios, programas ni láminas protegidas originales.

---

## 1. ¿Qué explora el módulo Sprott?

El Explorador Sprott está diseñado para la búsqueda automatizada y el análisis didáctico de sistemas dinámicos discretos (mapas) y continuos (flujos) que exhiben comportamiento caótico. La filosofía central de Sprott es que reglas matemáticas sumamente simples y deterministas son capaces de generar geometrías de increíble complejidad (fractales) y dinámicas impredecibles.

El módulo permite al usuario:
- Decodificar y simular sistemas polinomiales y de funciones especiales a partir de códigos compactos.
- Filtrar de manera automática trayectorias no triviales (candidatos caóticos).
- Estudiar la sensibilidad a condiciones iniciales y estimar exponentes de Lyapunov.
- Explorar fenómenos avanzados como la multistabilidad y los atractores ocultos.

---

## 2. Sistemas dinámicos discretos y continuos

Un **sistema dinámico discreto** (mapa iterado) actualiza su estado en pasos de tiempo discretos mediante una función de transición:

$$x_{n+1} = F(x_n), \qquad x_n \in \mathbb{R}^D$$

Donde $D$ es la dimensión del sistema. Tras descartar una cantidad inicial de iteraciones (el transitorio), se busca una trayectoria $\{x_0, x_1, x_2, \ldots\}$ que permanezca confinada en una región acotada del espacio de fases.

Un **sistema dinámico continuo** (flujo autónomo) se define por medio de ecuaciones diferenciales ordinarias (EDO):

$$\frac{dx}{dt} = f(x), \qquad x(t) \in \mathbb{R}^D$$

La trayectoria continua $\{x(t) : t \geq 0\}$ se obtiene aproximando numéricamente la solución del sistema.

En ambos casos, el caos se caracteriza por la **sensibilidad exponencial a las condiciones iniciales**. Si dos trayectorias se inician a una distancia infinitesimal $\|x_0 - y_0\|$, su separación promedio crece temporalmente como:

$$\|x_n - y_n\| \approx \|x_0 - y_0\| e^{\lambda n}$$

$$\|x(t) - y(t)\| \approx \|x(0) - y(0)\| e^{\lambda t}$$

Donde $\lambda$ representa el exponente de Lyapunov. Un atractor se considera caótico si el máximo exponente de Lyapunov es estrictamente positivo ($\lambda_{\max} > 0$) y la trayectoria permanece acotada.

---

## 3. Mapas polinomiales

En Chaos Toolbox, las funciones de los mapas polinomiales se representan como combinaciones lineales de una base monomial de grado total menor o igual a un orden $O$:

$$x_{i,n+1} = F_i(x_n) = \sum_{j=1}^{N_m} c_{ij} m_j(x_n), \qquad i = 1, \ldots, D$$

Donde $m_j(x)$ representa un monomio (como $1$, $x$, $y$, $x^2$, $xy$, $y^2$ para $D=2$, $O=2$). El número de monomios necesarios $N_m$ y la cantidad total de coeficientes $N_c$ se calculan como:

$$N_m = \binom{D+O}{O}$$

$$N_c = D \binom{D+O}{O}$$

Por ejemplo, un mapa cuadrático en 2D ($D=2$, $O=2$) cuenta con $N_m = \binom{4}{2} = 6$ monomios, lo que requiere un total de $N_c = 12$ coeficientes. Su base monomial es $\{1, x, y, x^2, xy, y^2\}$, y sus ecuaciones toman la forma clásica:

$$x_{n+1} = a_0 + a_1 x_n + a_2 y_n + a_3 x_n^2 + a_4 x_n y_n + a_5 y_n^2$$

$$y_{n+1} = b_0 + b_1 x_n + b_2 y_n + b_3 x_n^2 + b_4 x_n y_n + b_5 y_n^2$$

---

## 4. Flujos polinomiales

Los flujos polinomiales se definen de manera análoga a los mapas, pero interpretando el polinomio como el campo vectorial de derivadas temporales:

$$\dot{x}_i = f_i(x) = \sum_{j=1}^{N_m} c_{ij} m_j(x), \qquad i = 1, \ldots, D$$

Para simular la trayectoria del flujo, la toolbox resuelve numéricamente la EDO con un paso de tiempo $h$. Se implementan tres métodos de integración:
- **Euler explícito (histórico):**
  $$x_{k+1} = x_k + h f(x_k)$$
- **Heun (predictor-corrector de segundo orden):**
  $$x^* = x_k + h f(x_k), \qquad x_{k+1} = x_k + \frac{h}{2}\left(f(x_k)+f(x^*)\right)$$
- **Runge-Kutta de 4º orden (RK4, recomendado):**
  $$k_1 = f(x_k)$$
  $$k_2 = f\left(x_k + \frac{h}{2} k_1\right)$$
  $$k_3 = f\left(x_k + \frac{h}{2} k_2\right)$$
  $$k_4 = f(x_k + h k_3)$$
  $$x_{k+1} = x_k + \frac{h}{6}(k_1 + 2k_2 + 2k_3 + k_4)$$

RK4 tiene menor error de truncamiento local que Euler y Heun bajo las
hipótesis usuales de suavidad, pero ningún método fijo garantiza por sí solo
que una trayectoria represente la dinámica continua. Se debe repetir el
cálculo con pasos menores y comparar métodos.

---

## 5. Códigos compactos

El Explorador conserva los códigos de caracteres compactos de Sprott para parametrizar ecuaciones. Una cadena tipo Sprott se estructura como una letra de familia seguida de caracteres de coeficientes:

$$\text{código} = L \, s_1 s_2 \cdots s_k$$

Donde la primera letra $L$ selecciona el tipo de sistema (mapa o flujo, dimensión y orden), y cada carácter sucesivo $s_j$ se decodifica en un coeficiente real $c_j$ mediante la regla aritmética:

$$c_j = \frac{\operatorname{ord}(s_j) - 77}{10}$$

Esta regla asigna el carácter `M` a $0.0$, letras anteriores como `A` a $-1.2$, y posteriores como `Y` a $1.2$. Los códigos se completan con ceros si son más cortos que la cantidad de coeficientes esperada, y se truncan si son más largos.

---

## 6. Familias especiales

Además de las polinomiales estándar (familias `A-X`), Sprott introdujo familias de **funciones especiales** no polinomiales para explorar discontinuidades, términos trigonométricos y oscilaciones forzadas. La dinámica efectiva ocurre en $(x,y)$, mientras que $z$ y $w$ sirven como variables de proyección y tiempo en la toolbox:

### Familia `Y` (Valores Absolutos)
Introduce derivadas no continuas en los ejes coordenados mediante 10 coeficientes:
$$x_{n+1} = a_0 + a_1 x_n + a_2 y_n + a_3 |x_n| + a_4 |y_n|$$
$$y_{n+1} = a_5 + a_6 x_n + a_7 y_n + a_8 |x_n| + a_9 |y_n|$$
$$z_{n+1} = x_{n+1}^2 + y_{n+1}^2$$
$$w_{n+1} = \frac{n-1000}{N_{\max}-1000}$$

### Familia `[` (Potencia de Valores Absolutos)
Generaliza la familia `Y` usando exponentes variables en 14 coeficientes:
$$x_{n+1} = a_0 + a_1 x_n + a_2 y_n + a_3 |x_n|^{a_4} + a_5 |y_n|^{a_6}$$
$$y_{n+1} = a_7 + a_8 x_n + a_9 y_n + a_{10} |x_n|^{a_{11}} + a_{12} |y_n|^{a_{13}}$$
$$z_{n+1} = x_{n+1}^2 + y_{n+1}^2$$
$$w_{n+1} = \frac{n-1000}{N_{\max}-1000}$$
*(Protegido contra bases nulas con exponentes negativos).*

### Familia `\` (Senos)
Aplica pliegues periódicos y simetrías mediante funciones sinusoidales en 18 coeficientes:
$$x_{n+1} = a_0 + a_1 x_n + a_2 y_n + a_3 \sin(a_4 x_n + a_5) + a_6 \sin(a_7 y_n + a_8)$$
$$y_{n+1} = a_9 + a_{10} x_n + a_{11} y_n + a_{12} \sin(a_{13} x_n + a_{14}) + a_{15} \sin(a_{16} y_n + a_{17})$$
$$z_{n+1} = x_{n+1}^2 + y_{n+1}^2$$
$$w_{n+1} = \frac{n-1000}{N_{\max}-1000}$$

### Familia `]` (Seno Rotacional)
Combina una perturbación sinusoidal con una rotación de ángulo $\theta$ en 6 coeficientes:
$$\theta = \frac{2\pi}{13 + 10a_5}$$
$$u_n = x_n + a_1 \sin(a_2 y_n + a_3)$$
$$x_{n+1} = 10a_0 + u_n \cos\theta + y_n \sin\theta$$
$$y_{n+1} = 10a_4 - u_n \sin\theta + y_n \cos\theta$$
$$z_{n+1} = x_{n+1}^2 + y_{n+1}^2$$
$$w_{n+1} = \frac{n-1000}{N_{\max}-1000}$$

### Familia `^` (Oscilador Forzado)
Representa un mapa de integración de un oscilador de Duffing forzado sinusoidalmente con 9 coeficientes:
$$x_{n+1} = x_n + 0.1 a_0 y_n$$
$$y_{n+1} = y_n + 0.1 (a_1 x_n + a_2 x_n^3 + a_3 x_n^2 y_n + a_4 x_n y_n^2 + a_5 y_n + a_6 y_n^3 + a_7 \sin z_n)$$
$$z_{n+1} = (z_n + 0.1(a_8 + 1.3)) \bmod 2\pi$$
$$w_{n+1} = \frac{n-1000}{N_{\max}-1000}$$

### Familia `Z` (AND/OR Lógica)
Se reconoce como familia de lógica AND/OR de 10 coeficientes. La simulación
está deshabilitada porque el contrato público actual no define una semántica
numérica validada; el parser devuelve ese motivo explícito.

---

## 7. Simulación, transitorio y visualización

En la exploración práctica, no todos los puntos de la simulación son de interés. Se calcula una trayectoria total de $N_{\max}$ iteraciones, pero se descartan los primeros $N_T$ puntos (el **transitorio**):

$$\mathcal{T}_{\text{post}} = \{x_{N_T}, x_{N_T+1}, \ldots, x_{N_{\max}}\}$$

El transitorio representa la fase inicial en la que la órbita viaja desde una condición inicial arbitraria hasta aproximarse a la estructura del atractor. Un descarte de transitorio insuficiente distorsiona la geometría real del atractor, mientras que uno excesivo reduce el detalle visual disponible.

La condición inicial por defecto en la toolbox se sitúa en $x_0 = (0.1, 0.1, \ldots, 0.1)$. Para estudiar atractores múltiples (multistabilidad), es imprescindible variar esta condición inicial sistemáticamente en distintas regiones del espacio.

---

## 8. Clasificación de candidatos

El algoritmo de búsqueda automática en Chaos Toolbox descarta combinaciones
triviales mediante filtros rápidos aplicados a la trayectoria post-transitorio:
- **Divergente (`divergent`):** Si la norma $\|x_n\|$ supera un umbral de escape (por defecto $R_{\max} = 10^6$) o contiene valores no finitos (`NaN` o `Inf`), la simulación se detiene de inmediato.
- **Punto Fijo (`fixed_point`):** Si la trayectoria colapsa asintóticamente a un único estado, es decir:
  $$\max_{n \in \text{cola}} \|x_n - x_{N_{\max}}\| \leq \varepsilon$$
  la órbita representa dinámica puntual no caótica.
- **Baja Complejidad o Periódico (`periodic_or_low_complexity`):** Si tras redondear los valores de la cola de la trayectoria a baja precisión, esta se compone únicamente de ciclos repetitivos cortos o dispersiones numéricas triviales.
- **Candidato Caótico (`candidate_chaotic`):** Trayectorias acotadas, finitas, y no colapsadas a puntos o ciclos periódicos evidentes bajo los filtros rápidos.

> [!IMPORTANT]
> La etiqueta `candidate_chaotic` NO es una demostración formal de caos matemático. Representa únicamente un sistema acotado no colapsado y de apariencia compleja que resulta idóneo para un análisis dinámico riguroso secundario.

---

## 9. Lyapunov, dimensión de Kaplan--Yorke y límites de la evidencia

Para evaluar con mayor rigor numérico la naturaleza dinámica de un candidato, se estiman sus exponentes de Lyapunov:

$$\lambda_1 \geq \lambda_2 \geq \cdots \geq \lambda_D$$

La evidencia numérica de caos disipativo suele buscar que $\lambda_1 > 0$ y que la suma de todos los exponentes sea negativa ($\sum \lambda_i < 0$). Esta suma negativa indica contracción media o asintótica a lo largo de la órbita y de la ventana estudiadas; es un diagnóstico numérico y no demuestra por sí sola contracción global del volumen en todo el espacio de fases. En flujos autónomos tridimensionales ($D=3$), un atractor caótico típico presenta la firma $(\lambda_1, 0, \lambda_3)$ con $\lambda_1 > 0$, $\lambda_2 \approx 0$ (en la dirección de la trayectoria) y $\lambda_3 < -\lambda_1$.

A partir de los exponentes de Lyapunov, la **dimensión de Kaplan-Yorke** ($D_{KY}$) estima la dimensión fractal del atractor:

$$D_{KY} = j + \frac{\sum_{i=1}^{j} \lambda_i}{|\lambda_{j+1}|}$$

Donde $j$ es el mayor entero tal que la suma acumulada de los exponentes ordenados es no negativa ($\sum_{i=1}^j \lambda_i \geq 0$). Esta dimensión fractal refleja el grado de complejidad geométrica del atractor extraño.

---

## 10. Atractores ocultos y multistabilidad

La investigación moderna en sistemas dinámicos (Wang, Leonov, Kuznetsov, Chen) clasifica los atractores en dos tipos:
- **Atractores Autoexcitados:** La cuenca de atracción del atractor intersecta una vecindad arbitrariamente pequeña de algún punto de equilibrio inestable. Se localizan fácilmente iniciando simulaciones en las cercanías de los equilibrios del sistema.
- **Atractores Ocultos:** La cuenca de atracción no intersecta vecindades de ningún punto de equilibrio. Formalmente:
  $$\mathcal{B}(A) \cap U_\varepsilon(E_i) = \varnothing$$
  para toda vecindad $U_\varepsilon$ de radio $\varepsilon$ pequeño alrededor de cualquier equilibrio $E_i$.

Los atractores ocultos ocurren con frecuencia en:
1. **Sistemas sin equilibrios:** Donde es imposible aplicar el método estándar de iniciación en equilibrios inestables.
2. **Sistemas con un único equilibrio estable:** Donde iniciar cerca del punto de equilibrio conduce de forma asintótica al sumidero estable, requiriendo barreras iniciales remotas para hallar el atractor caótico coexistente.
3. **Sistemas con infinitos puntos de equilibrio:** Como variedades de equilibrios lineales, circulares o planos.

El Explorador Sprott permite explorar sistemas que caen en estas categorías. La identificación de atractores ocultos requiere un estudio sistemático y global de las cuencas de atracción del espacio de fases, y no puede determinarse a partir de una única integración aislada.

---

## 11. Reproducibilidad y atribución

Para cumplir con la política de distribución ética de Chaos Toolbox:
- **Sin archivos protegidos:** La versión pública del software no incluye archivos de diccionarios propietarios de Sprott (`BOOKFIGS.DIC`, `SELECTED.DIC`, etc.), códigos fuente originales, ejecutables ni DLLs históricas.
- **Carga local de usuario:** Los archivos `.DIC` son leídos en tiempo de ejecución de manera local y exclusiva por el usuario. El programa no copia ni distribuye dichos contenidos.
- **Metadatos de visualización:** Las entradas guardadas en la galería local incluyen un archivo lateral `metadata.json` con el código Sprott, transitorio, iteraciones, paso $h$, método, proyección, estilo y clasificación. La exportación aislada de una imagen no incorpora necesariamente ese archivo. Conservar ambos ayuda a repetir el cálculo, sin garantizar identidad entre plataformas o versiones.

---

## 12. Referencias

- Sprott, J. C. (1993). *Strange Attractors: Creating Patterns in Chaos*. M&T Books.
- Sprott, J. C. (1993). *Strange Attractors: Creating Patterns in Chaos* (Official Online Manuscript), University of Wisconsin: https://sprott.physics.wisc.edu/fractals/booktext/SABOOK.HTM
- Sprott, J. C. (1994). Some simple chaotic flows. *Physical Review E*, 50(2), R647-R650. https://doi.org/10.1103/PhysRevE.50.R647
- Wang, X., Kuznetsov, N. V., & Chen, G. (Eds.). (2021). *Chaotic Systems with Multistability and Hidden Attractors*. Springer. https://doi.org/10.1007/978-3-030-75821-9
- Leonov, G. A., & Kuznetsov, N. V. (2013). Hidden attractors in dynamical systems. From hidden oscillations in Hilbert--Kolmogorov, Aizerman, and Kalman problems to hidden chaotic attractor in Chua circuits. *International Journal of Bifurcation and Chaos*, 23(01), 1330002.
- Dudkowski, D., Jafari, S., Kapitaniak, T., Kuznetsov, N. V., Leonov, G. A., & Prasad, A. (2016). Hidden attractors in dynamical systems. *Physics Reports*, 637, 1-50.

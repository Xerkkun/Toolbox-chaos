# Complemento teórico para el módulo **Explorador Sprott** de Chaos Toolbox

> Documento de trabajo para complementar `assets/sprott/theory_intro.md`, `assets/sprott/theory/*.md` y `assets/sprott/code_grammar.md`.
>
> Alcance: explicación matemática, computacional y de implementación del explorador inspirado en Julien C. Sprott, con énfasis en mapas, flujos, codificación compacta, familias especiales, simulación, filtrado de candidatos y relación con atractores ocultos/multistabilidad.
>
> Restricción de distribución: este texto debe ser original. No debe copiar texto extenso, imágenes, diccionarios `.DIC`, código fuente histórico, ejecutables ni láminas originales de Sprott. La toolbox pública debe conservar una separación estricta entre reimplementación educativa propia y material local de estudio personal.

---

## 1. Diagnóstico del documento actual

El documento actual ya cumple una función introductoria: presenta el Explorador Sprott como una reimplementación educativa independiente, cita el libro *Strange Attractors: Creating Patterns in Chaos* y aclara que no se redistribuyen diccionarios, programas ni láminas originales. También introduce la idea de sensibilidad a condiciones iniciales, la ecuación logística, mapas polinomiales, flujos polinomiales, códigos compactos y búsqueda automatizada.

Lo que falta para que la sección de teoría sea más fuerte es desarrollar la conexión entre:

1. la teoría matemática de sistemas dinámicos discretos y continuos;
2. la gramática real de códigos implementada en `core/sprott/codes.py`;
3. las familias polinomiales `A-X` y las familias especiales `Y`, `Z`, `[`, `\`, `]`, `^`;
4. la simulación numérica actual: mapas por iteración directa, flujos por Euler/RK4 y backend C;
5. los criterios de clasificación computacional usados por la toolbox;
6. el lenguaje visual de Sprott: proyección, densidad, color y transitorio;
7. la relación moderna con atractores ocultos, atractores autoexcitados, multistabilidad y sistemas con equilibrios estables o sin equilibrios;
8. los límites epistemológicos: una figura acotada y compleja no prueba caos, y una etiqueta `candidate_chaotic` no prueba atractor oculto.

La teoría debe quedar dividida en secciones cortas y navegables para la interfaz, pero con ecuaciones suficientes para que el usuario vea que cada imagen procede de un sistema dinámico explícito.

---

## 2. Idea central: de reglas simples a dinámica compleja

El punto de partida de Sprott es práctico: buscar reglas deterministas simples que generen trayectorias acotadas, no periódicas en apariencia y con estructura geométrica rica. La herramienta no debe presentar los atractores como “dibujos bonitos”, sino como resultados de una regla matemática reproducible.

Un sistema dinámico discreto se escribe como

$$
x_{n+1}=F(x_n), \qquad x_n\in\mathbb{R}^D.
$$

Un sistema dinámico continuo autónomo se escribe como

$$
\frac{dx}{dt}=f(x), \qquad x(t)\in\mathbb{R}^D.
$$

En ambos casos se busca una trayectoria

$$
\{x_0,x_1,x_2,\ldots\}
\quad\text{o}\quad
\{x(t):t\geq 0\}
$$

que, después de descartar un transitorio, permanezca en una región acotada y exhiba estiramiento, plegamiento y sensibilidad a condiciones iniciales. En forma heurística, dos órbitas cercanas pueden separarse como

$$
\|x_n-y_n\|\approx \|x_0-y_0\|e^{\lambda n},
$$

para mapas, o

$$
\|x(t)-y(t)\|\approx \|x(0)-y(0)\|e^{\lambda t},
$$

para flujos. Si el máximo exponente de Lyapunov satisface

$$
\lambda_{\max}>0,
$$

existe sensibilidad exponencial promedio a condiciones iniciales. Aun así, la estimación de Lyapunov por sí sola debe tratarse como evidencia numérica, no como demostración formal.

---

## 3. Mapas iterados

Un mapa iterado actualiza el estado por sustitución directa:

$$
x_{n+1}=F(x_n).
$$

Para dimensión $D$, se escribe

$$
x_n=(x_{1,n},x_{2,n},\ldots,x_{D,n})^\top,
$$

y cada componente se calcula como

$$
x_{i,n+1}=F_i(x_n),\qquad i=1,\ldots,D.
$$

En las familias polinomiales de la toolbox, $F_i$ se representa como una combinación lineal de monomios:

$$
F_i(x)=\sum_{j=1}^{N_m} c_{ij}m_j(x),
$$

donde $m_j(x)$ recorre todos los monomios de grado total menor o igual que $O$. Para dimensión $D$ y orden polinomial $O$, el número de monomios es

$$
N_m=\binom{D+O}{O}.
$$

Como cada una de las $D$ componentes tiene su propia combinación de monomios, el número total de coeficientes es

$$
N_c=D\binom{D+O}{O}.
$$

Ejemplo: para un mapa cuadrático 2D, $D=2$ y $O=2$, por lo que

$$
N_m=\binom{4}{2}=6,\qquad N_c=2\binom{4}{2}=12.
$$

Una base monomial típica en 2D y orden 2 es

$$
\mathcal{M}_{2,2}=\{1,x,y,x^2,xy,y^2\}.
$$

Entonces un mapa cuadrático 2D tiene forma

$$
\begin{aligned}
x_{n+1}&=a_0+a_1x_n+a_2y_n+a_3x_n^2+a_4x_ny_n+a_5y_n^2,\\
y_{n+1}&=b_0+b_1x_n+b_2y_n+b_3x_n^2+b_4x_ny_n+b_5y_n^2.
\end{aligned}
$$

Este formato permite que una cadena compacta codifique un sistema completo.

---

## 4. Flujos polinomiales

Un flujo continuo define derivadas en lugar de actualizar el estado directamente:

$$
\dot{x}=f(x).
$$

En la toolbox, los flujos polinomiales siguen la misma base monomial que los mapas, pero se interpretan como campos vectoriales:

$$
\dot{x}_i=f_i(x)=\sum_{j=1}^{N_m}c_{ij}m_j(x),\qquad i=1,\ldots,D.
$$

Para simularlos se aproxima la solución de la EDO. El esquema de Euler explícito es

$$
x_{k+1}=x_k+h f(x_k),
$$

y el esquema RK4 usado como opción moderna es

$$
\begin{aligned}
k_1 &= f(x_k),\\
k_2 &= f\!\left(x_k+\frac{h}{2}k_1\right),\\
k_3 &= f\!\left(x_k+\frac{h}{2}k_2\right),\\
k_4 &= f(x_k+hk_3),\\
x_{k+1}&=x_k+\frac{h}{6}(k_1+2k_2+2k_3+k_4).
\end{aligned}
$$

Euler es útil para explicar la idea histórica de integración paso a paso. RK4 es preferible para uso educativo moderno porque reduce errores locales para un mismo paso $h$, aunque no elimina la necesidad de verificar estabilidad numérica, sensibilidad al paso y convergencia cualitativa.

---

## 5. Gramática compacta de códigos Sprott

La toolbox conserva la idea de códigos compactos como interfaz educativa. Una cadena se interpreta como

$$
\text{código}=L\,s_1s_2\cdots s_k,
$$

donde $L$ es la letra o símbolo de familia y $s_j$ son caracteres que codifican coeficientes.

La regla actual de decodificación de coeficientes es

$$
c_j=\frac{\operatorname{ord}(s_j)-77}{10}.
$$

De esta forma:

$$
M\mapsto 0.0,\qquad A\mapsto -1.2,\qquad Y\mapsto 1.2.
$$

La primera letra no es un coeficiente: selecciona el tipo de sistema. Las letras posteriores sí se leen como coeficientes. Cuando faltan coeficientes, la implementación los completa con cero para reconstruir una ecuación simulable; cuando sobran, los simuladores ignoran los excedentes.

---

## 6. Familias polinomiales `A-X`

La tabla siguiente resume la convención implementada para familias polinomiales.

| Letras | Tipo | Dimensión | Orden por letra | Coeficientes esperados |
|---|---:|---:|---:|---:|
| `A B C D` | mapa polinomial | 1 | 2, 3, 4, 5 | $1\binom{1+O}{O}$ |
| `E F G H` | mapa polinomial | 2 | 2, 3, 4, 5 | $2\binom{2+O}{O}$ |
| `I J K L` | mapa polinomial | 3 | 2, 3, 4, 5 | $3\binom{3+O}{O}$ |
| `M N O P` | mapa polinomial | 4 | 2, 3, 4, 5 | $4\binom{4+O}{O}$ |
| `Q R S T` | flujo polinomial | 3 | 2, 3, 4, 5 | $3\binom{3+O}{O}$ |
| `U V W X` | flujo polinomial | 4 | 2, 3, 4, 5 | $4\binom{4+O}{O}$ |

Dentro de cada grupo de cuatro letras, la primera letra corresponde a orden 2, la segunda a orden 3, la tercera a orden 4 y la cuarta a orden 5.

La forma general reconstruida para una familia polinomial es:

$$
\boxed{x_{n+1}=C\,\Phi_O(x_n)}
\quad\text{(mapa)}
$$

或

$$
\boxed{\dot{x}=C\,\Phi_O(x)}
\quad\text{(flujo)},
$$

donde $C\in\mathbb{R}^{D\times N_m}$ es la matriz de coeficientes y $\Phi_O(x)$ es el vector de monomios de grado total $\leq O$.

---

## 7. Familias especiales implementadas

Las familias especiales no son errores de lectura ni caracteres basura. Son familias no polinomiales de Sprott. En la toolbox actual, las familias `Y`, `[`, `\`, `]` y `^` están implementadas; `Z` está reconocida, pero permanece pendiente de validación semántica.

### 7.1 Familia `Y`: valores absolutos

La familia `Y` es un mapa especial 4D con 10 coeficientes. La dinámica efectiva ocurre en $(x,y)$, mientras que $z$ y $w$ se usan como variables auxiliares para visualización:

$$
\begin{aligned}
x_{n+1}&=a_0+a_1x_n+a_2y_n+a_3|x_n|+a_4|y_n|,\\
y_{n+1}&=a_5+a_6x_n+a_7y_n+a_8|x_n|+a_9|y_n|,\\
z_{n+1}&=x_{n+1}^2+y_{n+1}^2,\\
w_{n+1}&=\frac{n-1000}{N_{\max}-1000}.
\end{aligned}
$$

Esta familia permite discontinuidades de derivada en $x=0$ o $y=0$, porque aparecen términos de valor absoluto. Es útil para estudiar atractores generados por mapas por tramos o mapas con no suavidad débil.

### 7.2 Familia `[`: potencias de valores absolutos

La familia `[` generaliza la anterior usando potencias variables de valores absolutos y 14 coeficientes:

$$
\begin{aligned}
x_{n+1}&=a_0+a_1x_n+a_2y_n+a_3|x_n|^{a_4}+a_5|y_n|^{a_6},\\
y_{n+1}&=a_7+a_8x_n+a_9y_n+a_{10}|x_n|^{a_{11}}+a_{12}|y_n|^{a_{13}},\\
z_{n+1}&=x_{n+1}^2+y_{n+1}^2,\\
w_{n+1}&=\frac{n-1000}{N_{\max}-1000}.
\end{aligned}
$$

Se debe manejar con cuidado cuando la base es cero y el exponente es negativo. La implementación actual protege este caso marcando valores no finitos y deteniendo trayectorias divergentes.

### 7.3 Familia `\`: senos

La familia `\` es un mapa especial 4D con 18 coeficientes. Introduce términos sinusoidales:

$$
\begin{aligned}
x_{n+1}&=a_0+a_1x_n+a_2y_n+a_3\sin(a_4x_n+a_5)+a_6\sin(a_7y_n+a_8),\\
y_{n+1}&=a_9+a_{10}x_n+a_{11}y_n+a_{12}\sin(a_{13}x_n+a_{14})+a_{15}\sin(a_{16}y_n+a_{17}),\\
z_{n+1}&=x_{n+1}^2+y_{n+1}^2,\\
w_{n+1}&=\frac{n-1000}{N_{\max}-1000}.
\end{aligned}
$$

Este tipo de mapa puede generar plegamientos repetidos, bandas y simetrías asociadas a periodicidad trigonométrica.

### 7.4 Familia `]`: seno rotacional

La familia `]` tiene 6 coeficientes y combina una perturbación sinusoidal con una rotación:

$$
\theta=\frac{2\pi}{13+10a_5}.
$$

Definiendo

$$
u_n=x_n+a_1\sin(a_2y_n+a_3),
$$

la actualización es

$$
\begin{aligned}
x_{n+1}&=10a_0+u_n\cos\theta+y_n\sin\theta,\\
y_{n+1}&=10a_4-u_n\sin\theta+y_n\cos\theta,\\
z_{n+1}&=x_{n+1}^2+y_{n+1}^2,\\
w_{n+1}&=\frac{n-1000}{N_{\max}-1000}.
\end{aligned}
$$

El denominador $13+10a_5$ debe evitar valores cercanos a cero. La implementación actual usa una protección numérica cuando el denominador es demasiado pequeño.

### 7.5 Familia `^`: oscilador forzado

La familia `^` tiene 9 coeficientes y representa un mapa tipo integración discreta de un oscilador forzado:

$$
\begin{aligned}
x_{n+1}&=x_n+0.1a_0y_n,\\
y_{n+1}&=y_n+0.1\big(a_1x_n+a_2x_n^3+a_3x_n^2y_n+a_4x_ny_n^2+a_5y_n+a_6y_n^3+a_7\sin z_n\big),\\
z_{n+1}&=\big[z_n+0.1(a_8+1.3)\big]\bmod 2\pi,\\
w_{n+1}&=\frac{n-1000}{N_{\max}-1000}.
\end{aligned}
$$

Aquí $z$ actúa como fase periódica de forzamiento. Esta familia no debe explicarse como polinomio autónomo puro, sino como mapa discreto no polinomial con fase angular.

### 7.6 Familia `Z`: AND/OR pendiente

La familia `Z` se reconoce como familia especial de lógica AND/OR con 10 coeficientes, pero debe permanecer marcada como:

$$
\texttt{pending\_semantics\_validation}.
$$

No se debe simular como si estuviera validada. La interfaz debe explicar que `Z` no es un error de parsing: es una familia especial identificada, pero falta confirmar la semántica exacta antes de usarla para resultados educativos o reproducibles.

---

## 8. Simulación, transitorio y trayectoria post-transitorio

La herramienta debe explicar que no se grafica toda la simulación con el mismo peso. Se calcula una trayectoria completa,

$$
\{x_0,x_1,\ldots,x_N\},
$$

pero se descartan los primeros $N_T$ puntos:

$$
\mathcal{T}_{\mathrm{post}}=\{x_{N_T},x_{N_T+1},\ldots,x_N\}.
$$

El transitorio representa el arranque desde una condición inicial arbitraria. La geometría persistente del atractor suele verse mejor después de descartarlo. Para mapas y flujos caóticos, un transitorio insuficiente puede mezclar el acercamiento inicial con la dinámica asintótica; un transitorio excesivo puede dejar muy pocos puntos para visualizar.

La simulación actual usa una condición inicial por defecto cercana a

$$
x_0=(0.1,0.1,\ldots,0.1),
$$

ajustada a la dimensión de la familia. Para estudiar multistabilidad o atractores ocultos, esta condición inicial no es suficiente: deben compararse múltiples regiones del espacio de fases.

---

## 9. Clasificación computacional de candidatos

El botón de búsqueda aplica filtros rápidos. Estos filtros son útiles para exploración, pero no equivalen a una prueba matemática de caos.

### 9.1 Divergencia

Una trayectoria se marca como divergente si contiene valores no finitos o si su norma supera un umbral:

$$
\|x_n\|\geq R_{\max}.
$$

En la toolbox se usa un umbral configurable, por ejemplo

$$
R_{\max}=10^6.
$$

### 9.2 Colapso a punto fijo

Se marca posible punto fijo si la cola de la trayectoria se aproxima a un único estado. Para una cola de longitud $q$,

$$
\max_{n\in \mathrm{cola}}\|x_n-x_N\|\leq \varepsilon.
$$

Si esto ocurre, la figura puede mostrar una estructura transitoria interesante, pero la dinámica final no es un atractor extraño.

### 9.3 Baja complejidad o periodicidad corta

Una trayectoria se marca como periódica o de baja complejidad cuando su cola tiene poca dispersión o demasiados estados repetidos después de redondear. Este criterio detecta ciclos cortos y nubes degeneradas.

### 9.4 Candidato caótico

Una trayectoria recibe la etiqueta `candidate_chaotic` si es acotada, finita, no colapsa a punto fijo y no muestra baja complejidad bajo los filtros rápidos. La lectura correcta es:

$$
\texttt{candidate\_chaotic}\neq \text{prueba de caos}.
$$

Para fortalecer la evidencia deben añadirse diagnósticos como:

1. máximo exponente de Lyapunov y, preferiblemente, espectro completo;
2. sensibilidad a condiciones iniciales con renormalización;
3. secciones de Poincaré para flujos;
4. diagramas de bifurcación al variar un parámetro o coeficiente;
5. espectro de frecuencia de series temporales;
6. dimensión de Kaplan--Yorke o dimensión de correlación;
7. verificación de robustez frente a paso $h$, método numérico y transitorio.

---

## 10. Exponentes de Lyapunov y dimensión de Kaplan--Yorke

Para una trayectoria de un sistema dinámico, los exponentes de Lyapunov miden tasas promedio de expansión y contracción. Para un sistema $D$-dimensional, se ordenan como

$$
\lambda_1\geq \lambda_2\geq\cdots\geq\lambda_D.
$$

Una señal típica de caos disipativo es

$$
\lambda_1>0,\qquad \sum_{i=1}^{D}\lambda_i<0.
$$

Para un flujo autónomo continuo ideal, suele aparecer un exponente cercano a cero asociado a la dirección de la trayectoria:

$$
\lambda_2\approx 0
$$

cuando $D=3$ y el sistema tiene un atractor caótico típico. En mapas no existe necesariamente esta misma interpretación.

La dimensión de Kaplan--Yorke se define como

$$
D_{KY}=j+\frac{\sum_{i=1}^{j}\lambda_i}{|\lambda_{j+1}|},
$$

donde $j$ es el mayor entero tal que

$$
\sum_{i=1}^{j}\lambda_i\geq 0,
\qquad
\sum_{i=1}^{j+1}\lambda_i<0.
$$

Esta dimensión es útil para comparar atractores, pero depende de la calidad de la estimación de Lyapunov.

---

## 11. Conexión con atractores ocultos y multistabilidad

La literatura moderna distingue entre atractores autoexcitados y atractores ocultos.

Un atractor autoexcitado tiene una cuenca de atracción que intersecta una vecindad de algún equilibrio inestable. En términos computacionales, suele localizarse iniciando trayectorias cerca de un equilibrio inestable.

Un atractor oculto tiene una cuenca de atracción que no intersecta vecindades suficientemente pequeñas de los equilibrios. Por esa razón, no suele aparecer al usar el procedimiento estándar de iniciar cerca de equilibrios inestables.

Una definición operativa útil para la toolbox es:

$$
A\text{ es oculto}\quad\Longleftrightarrow\quad
\mathcal{B}(A)\cap U_\varepsilon(E_i)=\varnothing
\quad\text{para todo equilibrio }E_i
\text{ y }\varepsilon\text{ suficientemente pequeño}.
$$

Aquí $\mathcal{B}(A)$ es la cuenca del atractor $A$ y $U_\varepsilon(E_i)$ es una vecindad pequeña del equilibrio $E_i$.

Casos importantes:

1. Sistemas sin equilibrios: no hay equilibrios desde los cuales iniciar el procedimiento autoexcitado estándar; por ello sus atractores se tratan como ocultos desde el punto de vista de la clasificación moderna.
2. Sistemas con un único equilibrio estable: una trayectoria iniciada cerca del equilibrio estable cae al punto, no al atractor caótico; un atractor caótico coexistente debe buscarse lejos del equilibrio.
3. Sistemas con líneas, curvas o superficies de equilibrios: la clasificación requiere analizar qué segmentos de la variedad de equilibrios intersectan o no la cuenca del atractor.
4. Sistemas multistables: diferentes condiciones iniciales pueden converger a punto fijo, ciclo, toro o atractor extraño.

La toolbox debe evitar afirmar “oculto” solo porque una figura se ve caótica. Para certificar ocultedad se necesita comparar cuencas de atracción alrededor de todos los equilibrios y demostrar numéricamente que las vecindades pequeñas no caen al atractor candidato.

---

## 12. Sistemas Sprott A--S como referencia canónica

En *Some simple chaotic flows* (1994), Sprott presentó diecinueve flujos caóticos 3D algebraicamente simples. El libro editado por Wang, Kuznetsov y Chen los usa como referencia de sistemas simples para discutir caos, equilibrios, atractores ocultos y multistabilidad.

La forma general es

$$
\dot{x}=f_1(x,y,z),\qquad
\dot{y}=f_2(x,y,z),\qquad
\dot{z}=f_3(x,y,z),
$$

con pocos términos lineales, constantes y cuadráticos. La tabla siguiente resume los casos que deben incluirse como referencia teórica, no como copia de diccionarios originales.

| Caso | Sistema | Equilibrios reportados | Espectro de Lyapunov reportado | $D_{KY}$ |
|---|---|---|---|---:|
| A | $\dot{x}=y$, $\dot{y}=-x+yz$, $\dot{z}=1-y^2$ | ninguno | $(0.014,0,-0.014)$ | 3.000 |
| B | $\dot{x}=yz$, $\dot{y}=x-y$, $\dot{z}=1-xy$ | $(1,1,0)$, $(-1,-1,0)$ | $(0.210,0,-1.210)$ | 2.174 |
| C | $\dot{x}=yz$, $\dot{y}=x-y$, $\dot{z}=1-x^2$ | $(1,1,0)$, $(-1,-1,0)$ | $(0.163,0,-0.163)$ | 2.140 |
| D | $\dot{x}=-y$, $\dot{y}=x+z$, $\dot{z}=xz+3y^2$ | $(0,0,0)$ | $(0.103,0,-1.320)$ | 2.078 |
| E | $\dot{x}=yz$, $\dot{y}=x^2-y$, $\dot{z}=1-4x$ | $(0.25,0.063,0)$ | $(0.078,0,-1.078)$ | 2.072 |
| F | $\dot{x}=y+z$, $\dot{y}=-x+0.5y$, $\dot{z}=x^2-z$ | $(0,0,0)$, $(-2,-4,4)$ | $(0.117,0,-0.617)$ | 2.190 |
| G | $\dot{x}=0.4x+z$, $\dot{y}=xz-y$, $\dot{z}=-x+y$ | $(0,0,0)$, $(-2.5,-2.5,1)$ | $(0.034,0,-0.634)$ | 2.054 |
| H | $\dot{x}=-y+z^2$, $\dot{y}=x+0.5y$, $\dot{z}=x-z$ | $(0,0,0)$, $(-2,4,-2)$ | $(0.117,0,-0.617)$ | 2.190 |
| I | $\dot{x}=0.2y$, $\dot{y}=x+z$, $\dot{z}=x+y^2-z$ | $(0,0,0)$ | $(0.012,0,-1.012)$ | 2.012 aprox. |
| J | $\dot{x}=2z$, $\dot{y}=-2y+z$, $\dot{z}=-x+y+y^2$ | $(0,0,0)$ | $(0.076,0,-2.076)$ | 2.037 |
| K | $\dot{x}=xy-z$, $\dot{y}=x-y$, $\dot{z}=x+0.3z$ | $(0,0,0)$, $(-3.333,-3.333,11.111)$ | $(0.038,0,-0.890)$ | 2.042 |
| L | $\dot{x}=y+3.9z$, $\dot{y}=0.9x^2-y$, $\dot{z}=1-x$ | $(1,1.111,-0.231)$ | $(0.061,0,-1.061)$ | 2.057 |
| M | $\dot{x}=-z$, $\dot{y}=-x^2-y$, $\dot{z}=1.7+1.7x+y$ | $(2.406,-5.791,0)$, $(-0.706,-0.499,0)$ | $(0.044,0,-1.044)$ | 2.042 |
| N | $\dot{x}=-2y$, $\dot{y}=x+z^2$, $\dot{z}=1+y-2z$ | $(-0.25,0,0.5)$ | $(0.076,0,-2.076)$ | 2.037 |
| O | $\dot{x}=y$, $\dot{y}=x-z$, $\dot{z}=x+xz+2.7y$ | $(0,0,0)$, $(-1,0,-1)$ | $(0.049,0,-0.319)$ | 2.154 |
| P | $\dot{x}=2.7y+z$, $\dot{y}=-x+y^2$, $\dot{z}=x+y$ | $(0,0,0)$, $(1,-1,2.7)$ | $(0.087,0,-0.481)$ | 2.181 |
| Q | $\dot{x}=-z$, $\dot{y}=x-y$, $\dot{z}=3.1x+y^2+0.5z$ | $(0,0,0)$, $(-3.1,-3.1,0)$ | $(0.109,0,-0.609)$ | 2.179 |
| R | $\dot{x}=0.9-y$, $\dot{y}=0.4+z$, $\dot{z}=xy-z$ | $(-0.444,1.111,-0.4)$ | $(0.062,0,-1.062)$ | 2.058 |
| S | $\dot{x}=x-4y$, $\dot{y}=x+z^2$, $\dot{z}=1+x$ | $(-1,0.25,1)$, $(-1,0.25,-1)$ | $(0.188,0,-1.188)$ | 2.151 |

Esta tabla puede usarse para una página “Sistemas Sprott clásicos” o como bloque dentro de la teoría. La implementación de códigos compactos `A-X` no equivale necesariamente a estos casos A--S del artículo de 1994: conviene aclarar que aquí “familias A-X” son familias de codificación de la toolbox, mientras que “Sprott A--S” son sistemas 3D clásicos reportados en la literatura.

---

## 13. Sistemas sin equilibrios, equilibrios estables y búsqueda no estándar

El caso Sprott A no tiene equilibrios:

$$
\dot{x}=y,\qquad \dot{y}=-x+yz,\qquad \dot{z}=1-y^2.
$$

Al imponer $\dot{x}=0$, se obtiene $y=0$. Entonces $\dot{z}=1-y^2=1$, lo cual no puede anularse. Por tanto no existe punto $(x,y,z)$ que satisfaga simultáneamente

$$
\dot{x}=\dot{y}=\dot{z}=0.
$$

Este ejemplo debe usarse para explicar por qué la búsqueda de atractores no puede depender siempre de vecindades de equilibrios. En sistemas sin equilibrios, la exploración debe basarse en barridos de condiciones iniciales, continuidad de parámetros, búsqueda global o métodos heurísticos.

El caso Sprott E se usa históricamente como punto de partida para construir sistemas con un único equilibrio estable mediante perturbaciones constantes. La forma original es

$$
\dot{x}=yz,\qquad \dot{y}=x^2-y,
\qquad \dot{z}=1-4x.
$$

Una modificación tipo Wang--Chen agrega un parámetro $a$:

$$
\dot{x}=yz+a,
\qquad
\dot{y}=x^2-y,
\qquad
\dot{z}=1-4x.
$$

El equilibrio queda en

$$
E=\left(\frac14,\frac1{16},-16a\right),
$$

y su estabilidad cambia con $a$. Este ejemplo es adecuado para explicar que un atractor caótico puede coexistir con un equilibrio estable y por tanto no aparecer si se inicia cerca de ese equilibrio.

---

## 14. Lenguaje visual: proyección, densidad y color

La visualización debe explicarse como una lectura parcial del espacio de fases. Para una trayectoria $D$-dimensional, la figura 2D muestra una proyección

$$
\pi_{ij}(x)=(x_i,x_j).
$$

En 3D, las proyecciones más comunes son

$$
(x,y),\qquad (x,z),\qquad (y,z).
$$

En 4D, una representación útil combina proyección 2D con color o bandas:

$$
(x,y)\quad\text{con color por }z\text{ o }w.
$$

La densidad de puntos también tiene significado: regiones con muchos puntos indican mayor tiempo de residencia de la trayectoria, no necesariamente mayor dimensión. Por eso la toolbox debe conservar metadatos de visualización:

$$
\text{proyección},\quad \text{variable de color},\quad \text{paleta},\quad \text{fondo},\quad \alpha,
\quad \text{tamaño de punto},\quad N_{\max}.
$$

Una imagen exportada sin código, parámetros, transitorio y método numérico pierde reproducibilidad.

---

## 15. Cuencas de atracción y multistabilidad

Para un atractor $A$, la cuenca de atracción es

$$
\mathcal{B}(A)=\{x_0\in\mathbb{R}^D:\operatorname{dist}(\varphi_t(x_0),A)\to 0\text{ cuando }t\to\infty\}.
$$

Para mapas se reemplaza $\varphi_t(x_0)$ por $F^n(x_0)$.

Un sistema es multistable si existen atractores $A_1,A_2,\ldots,A_m$ con cuencas distintas:

$$
\mathcal{B}(A_i)\cap \mathcal{B}(A_j)=\varnothing\quad (i\neq j),
$$

en el sentido de convergencia asintótica, aunque sus fronteras puedan ser fractales o entrelazadas.

La toolbox puede explicar la clasificación práctica de trayectorias para cuencas:

1. elegir una malla de condiciones iniciales en un plano, por ejemplo $(x_0,y_0)$ con $z_0$ fijo;
2. integrar cada punto hasta $T$ o $N$;
3. extraer rasgos de la cola: media, desviación, energía, rango, frecuencia dominante, signo de Lyapunov estimado;
4. agrupar colas por cercanía de rasgos;
5. colorear cada punto inicial según el atractor final estimado;
6. repetir con varios tiempos, tolerancias y planos para comprobar robustez.

La clasificación de cuencas no debe basarse solo en una proyección visual del atractor.

---

## 16. Qué debe afirmar la interfaz y qué no

La interfaz puede afirmar:

- “Trayectoria acotada y no colapsada bajo filtros rápidos”.
- “Candidato para análisis adicional”.
- “Familia especial implementada”.
- “Familia especial reconocida, pendiente de validar semántica”.
- “Ejemplo local leído desde disco del usuario; no copiado al repositorio”.
- “Imagen generada por reimplementación educativa propia”.

La interfaz no debe afirmar automáticamente:

- “Este sistema es caótico” sin Lyapunov/diagnósticos suficientes.
- “Este atractor es oculto” sin análisis de equilibrios y cuencas locales.
- “Este resultado reproduce exactamente una figura del libro” si la imagen fue generada por el motor propio.
- “Código original incluido” o “diccionario original distribuido” en builds públicos.

---

## 17. Propuesta de estructura final para los archivos Markdown

### `assets/sprott/theory_intro.md`

Debe ser la página principal de teoría. Estructura recomendada:

1. ¿Qué explora el módulo Sprott?
2. Sistemas dinámicos discretos y continuos.
3. Mapas polinomiales y flujos polinomiales.
4. Códigos compactos.
5. Familias especiales.
6. Simulación, transitorio y visualización.
7. Candidatos, Lyapunov y límites de la evidencia.
8. Atractores ocultos y multistabilidad.
9. Referencias.

### `assets/sprott/code_grammar.md`

Debe contener:

1. tabla de familias `A-X`;
2. tabla de familias especiales;
3. regla de coeficientes;
4. conteo de monomios;
5. diferencia entre familias de codificación `A-X` y sistemas clásicos Sprott `A-S`;
6. advertencia sobre `Z` pendiente.

### `assets/sprott/theory/01_overview.md`

Debe resumir la motivación matemática y el flujo de trabajo:

$$
\text{código}\to \text{ecuaciones}\to \text{simulación}\to \text{transitorio}\to \text{figura}\to \text{diagnóstico}.
$$

### `assets/sprott/theory/02_iterated_maps.md`

Debe desarrollar mapas, base monomial, transitorio, punto fijo, ciclos y caos discreto.

### Nuevos archivos sugeridos

- `assets/sprott/theory/03_polynomial_flows.md`
- `assets/sprott/theory/04_special_families.md`
- `assets/sprott/theory/05_diagnostics.md`
- `assets/sprott/theory/07_hidden_attractors_multistability.md`
- `assets/sprott/theory/08_sprott_classic_flows.md`
- `assets/sprott/theory/09_reproducibility_and_attribution.md`

---

## 18. Referencias bibliográficas sugeridas

Sprott, J. C. (1993). *Strange Attractors: Creating Patterns in Chaos*. M&T Books.

Sprott, J. C. (1994). Some simple chaotic flows. *Physical Review E, 50*(2), R647--R650. https://doi.org/10.1103/PhysRevE.50.R647

Wang, X., Kuznetsov, N. V., & Chen, G. (Eds.). (2021). *Chaotic Systems with Multistability and Hidden Attractors*. Springer. https://doi.org/10.1007/978-3-030-75821-9

Leonov, G. A., & Kuznetsov, N. V. (2013). Hidden attractors in dynamical systems. From hidden oscillations in Hilbert--Kolmogorov, Aizerman, and Kalman problems to hidden chaotic attractor in Chua circuits. *International Journal of Bifurcation and Chaos, 23*(1), 1330002.

Dudkowski, D., Jafari, S., Kapitaniak, T., Kuznetsov, N. V., Leonov, G. A., & Prasad, A. (2016). Hidden attractors in dynamical systems. *Physics Reports, 637*, 1--50.

Jafari, S., & Sprott, J. C. (2013). Simple chaotic flows with a line equilibrium. *Chaos, Solitons & Fractals, 57*, 79--84.

Molaie, M., Jafari, S., Sprott, J. C., & Golpayegani, S. M. R. H. (2013). Simple chaotic flows with one stable equilibrium. *International Journal of Bifurcation and Chaos, 23*(11), 1350188.

---

## 19. Prompt para Codex

```text
Trabaja en el repositorio Xerkkun/Toolbox-chaos.

Objetivo general:
Actualizar y ampliar la documentación teórica del módulo Explorador Sprott para que sea matemáticamente clara, consistente con el código actual y respetuosa de la política de distribución. No modifiques resultados científicos, no agregues archivos originales de Sprott, no copies texto extenso del libro ni incluyas diccionarios .DIC, ejecutables, imágenes históricas o código fuente original.

Contexto del repositorio:
- La teoría actual está principalmente en:
  - assets/sprott/theory_intro.md
  - assets/sprott/code_grammar.md
  - assets/sprott/theory/01_overview.md
  - assets/sprott/theory/02_iterated_maps.md
  - assets/sprott/theory/06_visual_language.md
  - assets/sprott/theory/10_legal_attribution.md
- La gramática real de códigos está en:
  - core/sprott/codes.py
  - core/sprott/families.py
  - core/sprott/special_families.py
  - core/sprott/search.py
  - core/sprott/metrics.py
- La UI usa pestañas Inicio, Tutorial, Teoría, Códigos, Exploración, Ejemplos, Galería, Inventario local y Backend explicado en ui/sprott_explorer_tab.py.
- La política de distribución está en docs/distribution_policy.md y debe respetarse estrictamente.

Tareas de escritura:
1. Reescribe assets/sprott/theory_intro.md como página teórica principal, en español, con estas secciones:
   - Qué explora el módulo Sprott.
   - Sistemas dinámicos discretos y continuos.
   - Mapas polinomiales.
   - Flujos polinomiales.
   - Códigos compactos.
   - Familias especiales.
   - Simulación, transitorio y visualización.
   - Clasificación de candidatos.
   - Lyapunov, dimensión de Kaplan--Yorke y límites de la evidencia.
   - Atractores ocultos y multistabilidad.
   - Reproducibilidad y atribución.
   - Referencias.

2. Actualiza assets/sprott/code_grammar.md para que coincida exactamente con core/sprott/codes.py:
   - A-D: mapas 1D, órdenes 2--5.
   - E-H: mapas 2D, órdenes 2--5.
   - I-L: mapas 3D, órdenes 2--5.
   - M-P: mapas 4D, órdenes 2--5.
   - Q-T: flujos 3D, órdenes 2--5.
   - U-X: flujos 4D, órdenes 2--5.
   - Y: familia especial de valores absolutos, 10 coeficientes, implementada.
   - Z: familia especial AND/OR, 10 coeficientes, pendiente de validar semántica.
   - [: familia especial de potencias de valores absolutos, 14 coeficientes, implementada.
   - \: familia especial de senos, 18 coeficientes, implementada.
   - ]: familia especial de seno rotacional, 6 coeficientes, implementada.
   - ^: familia especial de oscilador forzado, 9 coeficientes, implementada.
   - Incluye la regla c=(ord(character)-77)/10.
   - Incluye N_m=binom(D+O,O) y N_c=D*binom(D+O,O).
   - Aclara que “familias A-X” son familias de codificación de la toolbox y no deben confundirse con los sistemas clásicos Sprott A-S del paper de 1994.

3. Crea o amplía los archivos modulares en assets/sprott/theory/:
   - 03_polynomial_flows.md
   - 04_special_families.md
   - 05_diagnostics.md
   - 07_hidden_attractors_multistability.md
   - 08_sprott_classic_flows.md
   - 09_reproducibility_and_attribution.md

4. En 04_special_families.md, documenta con ecuaciones las familias implementadas exactamente como aparecen en core/sprott/special_families.py:
   - Y:
     x' = a0+a1*x+a2*y+a3*|x|+a4*|y|
     y' = a5+a6*x+a7*y+a8*|x|+a9*|y|
     z' = x'^2+y'^2
     w' = (n-1000)/(nmax-1000)
   - [:
     x' = a0+a1*x+a2*y+a3*|x|^a4+a5*|y|^a6
     y' = a7+a8*x+a9*y+a10*|x|^a11+a12*|y|^a13
     z' = x'^2+y'^2
     w' = (n-1000)/(nmax-1000)
   - \:
     x' = a0+a1*x+a2*y+a3*sin(a4*x+a5)+a6*sin(a7*y+a8)
     y' = a9+a10*x+a11*y+a12*sin(a13*x+a14)+a15*sin(a16*y+a17)
     z' = x'^2+y'^2
     w' = (n-1000)/(nmax-1000)
   - ]:
     theta = 2*pi/(13+10*a5)
     u = x+a1*sin(a2*y+a3)
     x' = 10*a0+u*cos(theta)+y*sin(theta)
     y' = 10*a4-u*sin(theta)+y*cos(theta)
     z' = x'^2+y'^2
     w' = (n-1000)/(nmax-1000)
   - ^:
     x' = x+0.1*a0*y
     y' = y+0.1*(a1*x+a2*x^3+a3*x^2*y+a4*x*y^2+a5*y+a6*y^3+a7*sin(z))
     z' = (z+0.1*(a8+1.3)) mod 2*pi
     w' = (n-1000)/(nmax-1000)
   - Z debe quedar documentada como reconocida pero no simulable hasta validar semántica AND/OR.

5. En 05_diagnostics.md, documenta los filtros reales de core/sprott/search.py y core/sprott/metrics.py:
   - divergent: valores no finitos o norma mayor al umbral.
   - fixed_point: cola colapsada a un punto fijo.
   - periodic_or_low_complexity: baja dispersión o muchos estados repetidos redondeados.
   - candidate_chaotic: acotada y no colapsada; requiere diagnósticos fuertes.
   - Explica que quick_lyapunov_estimate es evidencia rápida, no certificación.

6. En 07_hidden_attractors_multistability.md, agrega una explicación moderna de atractores autoexcitados y ocultos:
   - Autoexcitado: la cuenca intersecta una vecindad de un equilibrio inestable.
   - Oculto: la cuenca no intersecta vecindades suficientemente pequeñas de los equilibrios.
   - Sistemas sin equilibrios y sistemas con solo equilibrios estables requieren búsqueda no estándar.
   - No afirmar ocultedad desde una sola simulación.

7. En 08_sprott_classic_flows.md, incluye una tabla educativa de los sistemas Sprott A-S del paper de 1994 usando ecuaciones, equilibrios y Lyapunov/Kaplan--Yorke como referencia bibliográfica. No copiar tablas escaneadas ni imágenes originales. Redacta la tabla de forma propia.

8. En 09_reproducibility_and_attribution.md, refuerza:
   - La app pública no empaqueta BOOKFIGS.DIC, SELECTED.DIC, SPECIAL.DIC, SA.EXE, SAWIN.EXE, PROG28.BAS, PROG28QC.C, PROG28TC.CPP, imágenes históricas ni HTML original.
   - Los .DIC locales se leen desde disco del usuario y no se copian al repositorio.
   - Las imágenes exportadas deben llevar metadata: código, fuente, ruta local si aplica, línea, simulación, transitorio, h, método, backend, proyección, color, alpha, dpi, clasificación.

9. Revisa que ui/sprott_explorer_tab.py pueda seguir renderizando los markdown. Si la pestaña Teoría solo lee theory_intro.md, conserva ese archivo como versión completa. Los archivos modulares pueden quedar enlazados o citados desde la página principal.

10. Agrega o actualiza referencias bibliográficas en formato breve:
   - Sprott (1993), Strange Attractors: Creating Patterns in Chaos.
   - Sprott (1994), Some simple chaotic flows, Physical Review E, DOI 10.1103/PhysRevE.50.R647.
   - Wang, Kuznetsov & Chen (eds.) (2021), Chaotic Systems with Multistability and Hidden Attractors.
   - Leonov & Kuznetsov (2013), Hidden attractors in dynamical systems.
   - Dudkowski et al. (2016), Hidden attractors in dynamical systems.

Criterios de aceptación:
- La documentación debe ser consistente con el código actual, especialmente con core/sprott/codes.py y core/sprott/special_families.py.
- No debe decir que candidate_chaotic prueba caos.
- No debe decir que una simulación prueba atractor oculto.
- Debe explicar claramente que los caracteres especiales no son errores: son familias especiales.
- Debe explicar que Z está pendiente por semántica, no por parsing.
- Debe preservar la política de no redistribución de material original de Sprott.
- Debe usar ecuaciones Markdown/LaTeX compatibles con el render actual.
- Debe mantener español claro, académico y útil para estudiantes.

Validación mínima:
- Ejecuta las pruebas existentes relacionadas con Sprott si están disponibles.
- Ejecuta cualquier script de verificación de distribución, especialmente tools/check_no_sprott_originals_in_release.py si aplica.
- Abre o inspecciona la pestaña Teoría para confirmar que el Markdown renderiza sin romper la UI.
- Verifica que las rutas de imágenes referidas existan o elimina referencias a imágenes inexistentes.
```

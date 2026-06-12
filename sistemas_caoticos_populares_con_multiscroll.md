# Sistemas caóticos populares e interesantes

**Fecha de elaboración:** 2026-06-11  
**Formato:** Markdown  
**Criterio de selección:** sistemas clásicos o ampliamente usados, con dinámica cualitativamente interesante y publicación original o de referencia identificable.

> Nota: las ecuaciones se dan en formas canónicas usadas en la literatura. Algunos sistemas tienen variantes por reescalamiento, cambio de parámetros, normalización o forma física original. Cuando hay ambigüedad histórica, se indica el trabajo de referencia más usado para el comportamiento caótico.

---

## Índice rápido

| # | Sistema | Tipo | Autores principales | Publicación de referencia | Año |
|---:|---|---|---|---|---:|
| 1 | Lorenz | ODE autónomo 3D | Edward N. Lorenz | *Deterministic Nonperiodic Flow* | 1963 |
| 2 | Rössler | ODE autónomo 3D | Otto E. Rössler | *An Equation for Continuous Chaos* | 1976 |
| 3 | Chua / doble scroll | Circuito no lineal, ODE 3D por tramos | Leon O. Chua; T. Matsumoto; L. O. Chua, M. Komuro, T. Matsumoto | *A Chaotic Attractor from Chua's Circuit*; *The Double Scroll Family* | 1984 / 1986 |
| 4 | Chen | ODE autónomo 3D | Guanrong Chen, Tetsushi Ueta | *Yet Another Chaotic Attractor* | 1999 |
| 5 | Lü | ODE autónomo 3D | Jinhu Lü, Guanrong Chen | *A New Chaotic Attractor Coined* | 2002 |
| 6 | Hénon | Mapa discreto 2D | Michel Hénon | *A Two-Dimensional Mapping with a Strange Attractor* | 1976 |
| 7 | Logístico | Mapa discreto 1D | Robert M. May, como referencia moderna de caos poblacional | *Simple Mathematical Models with Very Complicated Dynamics* | 1976 |
| 8 | Ikeda | Mapa discreto óptico 2D | Kensuke Ikeda | *Multiple-Valued Stationary State and Its Instability of the Transmitted Light by a Ring Cavity System* | 1979 |
| 9 | Mackey–Glass | Ecuación diferencial con retardo | Michael C. Mackey, Leon Glass | *Oscillation and Chaos in Physiological Control Systems* | 1977 |
| 10 | Duffing–Ueda | Oscilador forzado no lineal | Georg Duffing; Yoshisuke Ueda para dinámica caótica | *Randomly Transitional Phenomena in the System Governed by Duffing's Equation* | 1979 |
| 11 | Rabinovich–Fabrikant | ODE autónomo 3D | M. I. Rabinovich, A. L. Fabrikant | *Stochastic Self-Modulation of Waves in Nonequilibrium Media* | 1979 |
| 12 | Rikitake | Dinamo de discos, ODE 3D | Tsuneji Rikitake | *Oscillations of a System of Disk Dynamos* | 1958 |
| 13 | Sprott A | Flujo cuadrático simple 3D | J. C. Sprott | *Some Simple Chaotic Flows* | 1994 |
| 14 | Thomas / labyrinth chaos | Flujo cíclico con senos | René Thomas | *Deterministic Chaos Seen in Terms of Feedback Circuits: Analysis, Synthesis, "Labyrinth Chaos"* | 1999 |
| 15 | Hindmarsh–Rose | Modelo neuronal 3D | J. L. Hindmarsh, R. M. Rose | *A Model of Neuronal Bursting Using Three Coupled First Order Differential Equations* | 1984 |
| 16 | Lorenz-96 | ODE de dimensión alta, anillo atmosférico | Edward N. Lorenz | *Predictability — A Problem Partly Solved* | 1996 |

---

# 1. Sistema de Lorenz

**Tipo:** flujo autónomo tridimensional disipativo.  
**Autores:** Edward N. Lorenz.  
**Trabajo original:** *Deterministic Nonperiodic Flow*, *Journal of the Atmospheric Sciences*.  
**Año:** 1963.

## Ecuaciones canónicas

```math
\begin{aligned}
\dot{x} &= \sigma (y-x),\\
\dot{y} &= x(\rho-z)-y,\\
\dot{z} &= xy-\beta z.
\end{aligned}
```

Parámetros clásicos:

```math
\sigma = 10,\qquad \rho = 28,\qquad \beta = \frac{8}{3}.
```

## Dinámica curiosa

Es el sistema paradigmático del efecto mariposa. Tiene dos lóbulos asociados a la convección idealizada, sensibilidad extrema a condiciones iniciales, estructura tipo mariposa y un atractor extraño que se volvió emblema de la teoría del caos.

## Referencia base

Lorenz, E. N. (1963). *Deterministic Nonperiodic Flow*. *Journal of the Atmospheric Sciences*, 20(2), 130–141. DOI: `10.1175/1520-0469(1963)020<0130:DNF>2.0.CO;2`.

---

# 2. Sistema de Rössler

**Tipo:** flujo autónomo tridimensional.  
**Autor:** Otto E. Rössler.  
**Trabajo original:** *An Equation for Continuous Chaos*, *Physics Letters A*.  
**Año:** 1976.

## Ecuaciones canónicas

```math
\begin{aligned}
\dot{x} &= -y-z,\\
\dot{y} &= x+a y,\\
\dot{z} &= b+z(x-c).
\end{aligned}
```

Parámetros clásicos:

```math
a=0.2,\qquad b=0.2,\qquad c=5.7.
```

## Dinámica curiosa

Tiene una geometría espiral más simple que Lorenz. Su atractor parece una banda que se enrolla, se estira y se pliega. Es muy usado para estudiar secciones de Poincaré, bifurcaciones, sincronización y rutas al caos.

## Referencia base

Rössler, O. E. (1976). *An Equation for Continuous Chaos*. *Physics Letters A*, 57(5), 397–398. DOI: `10.1016/0375-9601(76)90101-8`.

---

# 3. Circuito de Chua y atractor doble scroll

**Tipo:** circuito electrónico no lineal; sistema autónomo 3D con no linealidad por tramos.  
**Autores principales:** Leon O. Chua; Takashi Matsumoto; Leon O. Chua, Motomasa Komuro y Takashi Matsumoto.  
**Trabajos de referencia:** *A Chaotic Attractor from Chua's Circuit* y *The Double Scroll Family*.  
**Años:** 1984 y 1986.

## Ecuaciones canónicas adimensionales

```math
\begin{aligned}
\dot{x} &= \alpha \left(y-x-f(x)\right),\\
\dot{y} &= x-y+z,\\
\dot{z} &= -\beta y,
\end{aligned}
```

con no linealidad tipo diodo de Chua:

```math
f(x)=m_1x+\frac{1}{2}(m_0-m_1)\left(|x+1|-|x-1|\right).
```

## Dinámica curiosa

Es uno de los sistemas caóticos más importantes en electrónica no lineal porque se implementa físicamente con componentes de circuito. El doble scroll tiene dos lóbulos y una no linealidad por tramos, por lo que es especialmente útil para estudiar circuitos, sincronización, cifrado caótico, atractores ocultos y validación experimental.

## Referencia base

Matsumoto, T. (1984). *A Chaotic Attractor from Chua's Circuit*. *IEEE Transactions on Circuits and Systems*, CAS-31, 1055–1058.  
Chua, L. O., Komuro, M., & Matsumoto, T. (1986). *The Double Scroll Family*. *IEEE Transactions on Circuits and Systems*, 33(11), 1072–1118.

---

# 4. Sistema de Chen

**Tipo:** flujo autónomo tridimensional.  
**Autores:** Guanrong Chen y Tetsushi Ueta.  
**Trabajo original:** *Yet Another Chaotic Attractor*, *International Journal of Bifurcation and Chaos*.  
**Año:** 1999.

## Ecuaciones canónicas

```math
\begin{aligned}
\dot{x} &= a(y-x),\\
\dot{y} &= (c-a)x -xz + c y,\\
\dot{z} &= xy-bz.
\end{aligned}
```

Parámetros típicos:

```math
a=35,\qquad b=3,\qquad c=28.
```

## Dinámica curiosa

Se parece a Lorenz en estructura general, pero no es una simple reparametrización. El término lineal de la segunda ecuación cambia la geometría de los equilibrios y la estructura de bifurcaciones. Se usa mucho en sincronización, control y cifrado.

## Referencia base

Chen, G., & Ueta, T. (1999). *Yet Another Chaotic Attractor*. *International Journal of Bifurcation and Chaos*, 9(7), 1465–1466. DOI: `10.1142/S0218127499001024`.

---

# 5. Sistema de Lü

**Tipo:** flujo autónomo tridimensional.  
**Autores:** Jinhu Lü y Guanrong Chen.  
**Trabajo original:** *A New Chaotic Attractor Coined*, *International Journal of Bifurcation and Chaos*.  
**Año:** 2002.

## Ecuaciones canónicas

```math
\begin{aligned}
\dot{x} &= a(y-x),\\
\dot{y} &= -xz + c y,\\
\dot{z} &= xy-bz.
\end{aligned}
```

Parámetros típicos:

```math
a=36,\qquad b=3,\qquad c=20.
```

## Dinámica curiosa

Fue propuesto como un puente entre Lorenz y Chen. Es interesante porque pequeñas modificaciones estructurales en la segunda ecuación cambian de manera importante la geometría del atractor y la ruta de bifurcación.

## Referencia base

Lü, J., & Chen, G. (2002). *A New Chaotic Attractor Coined*. *International Journal of Bifurcation and Chaos*, 12(3), 659–661. DOI: `10.1142/S0218127402004620`.

---

# 6. Mapa de Hénon

**Tipo:** mapa discreto bidimensional.  
**Autor:** Michel Hénon.  
**Trabajo original:** *A Two-Dimensional Mapping with a Strange Attractor*, *Communications in Mathematical Physics*.  
**Año:** 1976.

## Ecuaciones canónicas

```math
\begin{aligned}
x_{n+1} &= 1-a x_n^2+y_n,\\
y_{n+1} &= b x_n.
\end{aligned}
```

Parámetros clásicos:

```math
a=1.4,\qquad b=0.3.
```

## Dinámica curiosa

Es uno de los mapas discretos caóticos más famosos. Genera un atractor extraño con estructura fractal en el plano. Es excelente para estudiar iteración, sensibilidad, dimensión fractal, medidas invariantes y mapas de retorno.

## Referencia base

Hénon, M. (1976). *A Two-Dimensional Mapping with a Strange Attractor*. *Communications in Mathematical Physics*, 50(1), 69–77. DOI: `10.1007/BF01608556`.

---

# 7. Mapa logístico

**Tipo:** mapa discreto unidimensional.  
**Autor de referencia para caos poblacional:** Robert M. May.  
**Trabajo de referencia:** *Simple Mathematical Models with Very Complicated Dynamics*, *Nature*.  
**Año:** 1976.

## Ecuación canónica

```math
x_{n+1}=r x_n(1-x_n), \qquad 0\leq x_n \leq 1.
```

## Dinámica curiosa

Es posiblemente el ejemplo más compacto de cómo una ecuación determinista sencilla puede producir dinámica compleja. Exhibe bifurcaciones por duplicación de periodo, cascada de Feigenbaum, ventanas periódicas dentro del caos e intermitencia.

## Referencia base

May, R. M. (1976). *Simple Mathematical Models with Very Complicated Dynamics*. *Nature*, 261, 459–467. DOI: `10.1038/261459a0`.

---

# 8. Mapa de Ikeda

**Tipo:** mapa discreto asociado a óptica no lineal.  
**Autor:** Kensuke Ikeda.  
**Trabajo original:** *Multiple-Valued Stationary State and Its Instability of the Transmitted Light by a Ring Cavity System*, *Optics Communications*.  
**Año:** 1979.

## Forma compleja compacta

```math
z_{n+1}=A+Bz_n\exp\left(i\left(|z_n|^2+C\right)\right).
```

## Forma real común

```math
\begin{aligned}
x_{n+1} &= 1+u(x_n\cos t_n-y_n\sin t_n),\\
y_{n+1} &= u(x_n\sin t_n+y_n\cos t_n),\\
t_n &= 0.4-\frac{6}{1+x_n^2+y_n^2}.
\end{aligned}
```

## Dinámica curiosa

Surge en cavidades ópticas no lineales. Tiene una interpretación física clara: el campo óptico recircula y acumula una fase no lineal. Produce atractores con torsiones, multivaluación e inestabilidad óptica.

## Referencia base

Ikeda, K. (1979). *Multiple-Valued Stationary State and Its Instability of the Transmitted Light by a Ring Cavity System*. *Optics Communications*, 30(2), 257–261. DOI: `10.1016/0030-4018(79)90090-7`.

---

# 9. Ecuación de Mackey–Glass

**Tipo:** ecuación diferencial con retardo.  
**Autores:** Michael C. Mackey y Leon Glass.  
**Trabajo original:** *Oscillation and Chaos in Physiological Control Systems*, *Science*.  
**Año:** 1977.

## Ecuación canónica

```math
\frac{dx(t)}{dt}=
\frac{\beta x(t-\tau)}{1+x(t-\tau)^n}
-\gamma x(t).
```

Parámetros típicos para dinámica caótica:

```math
\beta=0.2,\qquad \gamma=0.1,\qquad n=10,\qquad \tau \gtrsim 17.
```

## Dinámica curiosa

Aunque tiene una sola variable observable, el retardo convierte al sistema en infinito-dimensional. Es un ejemplo clásico de caos en sistemas fisiológicos, especialmente en modelos de regulación hematológica y respiratoria.

## Referencia base

Mackey, M. C., & Glass, L. (1977). *Oscillation and Chaos in Physiological Control Systems*. *Science*, 197(4300), 287–289. DOI: `10.1126/science.267326`.

---

# 10. Oscilador de Duffing–Ueda

**Tipo:** oscilador no lineal forzado; sistema no autónomo de segundo orden.  
**Autores:** Georg Duffing para el oscilador; Yoshisuke Ueda para el estudio caótico computacional.  
**Trabajo de referencia para caos:** *Randomly Transitional Phenomena in the System Governed by Duffing's Equation*, *Journal of Statistical Physics*.  
**Año:** 1979.

## Ecuación canónica

```math
\ddot{x}+\delta\dot{x}+\alpha x+\beta x^3=\gamma\cos(\omega t).
```

Como sistema autónomo extendido:

```math
\begin{aligned}
\dot{x} &= y,\\
\dot{y} &= -\delta y-\alpha x-\beta x^3+\gamma\cos(\theta),\\
\dot{\theta} &= \omega.
\end{aligned}
```

## Dinámica curiosa

Puede mostrar saltos entre pozos, histeresis, atractores coexistentes, caos por forzamiento periódico y secciones de Poincaré con geometría fractal. Es uno de los modelos más importantes de vibraciones no lineales.

## Referencia base

Ueda, Y. (1979). *Randomly Transitional Phenomena in the System Governed by Duffing's Equation*. *Journal of Statistical Physics*, 20, 181–196. DOI: `10.1007/BF01011512`.

---

# 11. Sistema de Rabinovich–Fabrikant

**Tipo:** flujo autónomo tridimensional.  
**Autores:** M. I. Rabinovich y A. L. Fabrikant.  
**Trabajo original:** *Stochastic Self-Modulation of Waves in Nonequilibrium Media*.  
**Año:** 1979.

## Ecuaciones canónicas

```math
\begin{aligned}
\dot{x} &= y(z-1+x^2)+\gamma x,\\
\dot{y} &= x(3z+1-x^2)+\gamma y,\\
\dot{z} &= -2z(\alpha+xy).
\end{aligned}
```

Parámetros usados frecuentemente:

```math
\alpha=1.1,\qquad \gamma=0.87.
```

## Dinámica curiosa

Se originó como modelo de ondas en medios disipativos fuera del equilibrio. Es conocido por tener dinámica muy rica, regiones caóticas complicadas y coexistencia de comportamientos que lo vuelven difícil de analizar numéricamente.

## Referencia base

Rabinovich, M. I., & Fabrikant, A. L. (1979). *Stochastic Self-Modulation of Waves in Nonequilibrium Media*. *Soviet Physics JETP*, 50, 311–317. Original ruso: *Zh. Eksp. Teor. Fiz.*, 77, 617–629.

---

# 12. Sistema de Rikitake

**Tipo:** modelo de dinamo de dos discos; flujo autónomo 3D.  
**Autor:** Tsuneji Rikitake.  
**Trabajo original:** *Oscillations of a System of Disk Dynamos*, *Proceedings of the Cambridge Philosophical Society*.  
**Año:** 1958.

## Forma normalizada común

```math
\begin{aligned}
\dot{x} &= -\mu x+yz,\\
\dot{y} &= -\mu y+x(z-a),\\
\dot{z} &= 1-xy.
\end{aligned}
```

> Hay variantes equivalentes por cambio de escala y por la elección de parámetros físicos de los discos.

## Dinámica curiosa

Fue motivado por inversiones del campo magnético terrestre. Puede producir cambios irregulares de signo en las variables asociadas a corrientes o campo magnético, por lo que es un ejemplo histórico de caos con interpretación geofísica.

## Referencia base

Rikitake, T. (1958). *Oscillations of a System of Disk Dynamos*. *Proceedings of the Cambridge Philosophical Society*, 54, 89–105. DOI: `10.1017/S0305004100033223`.

---

# 13. Sistema Sprott A

**Tipo:** flujo autónomo tridimensional cuadrático simple.  
**Autor:** J. C. Sprott.  
**Trabajo original:** *Some Simple Chaotic Flows*, *Physical Review E*.  
**Año:** 1994.

## Ecuaciones canónicas

```math
\begin{aligned}
\dot{x} &= y,\\
\dot{y} &= -x+yz,\\
\dot{z} &= 1-y^2.
\end{aligned}
```

## Dinámica curiosa

Forma parte de una familia de sistemas caóticos extremadamente simples encontrados mediante búsqueda computacional. Es útil para estudiar qué tan poca estructura algebraica se necesita para obtener caos en flujos tridimensionales.

## Referencia base

Sprott, J. C. (1994). *Some Simple Chaotic Flows*. *Physical Review E*, 50, R647–R650. DOI: `10.1103/PhysRevE.50.R647`.

---

# 14. Sistema de Thomas / labyrinth chaos

**Tipo:** flujo autónomo tridimensional con simetría cíclica.  
**Autor:** René Thomas.  
**Trabajo original:** *Deterministic Chaos Seen in Terms of Feedback Circuits: Analysis, Synthesis, "Labyrinth Chaos"*, *International Journal of Bifurcation and Chaos*.  
**Año:** 1999.

## Ecuaciones canónicas

```math
\begin{aligned}
\dot{x} &= \sin(y)-b x,\\
\dot{y} &= \sin(z)-b y,\\
\dot{z} &= \sin(x)-b z.
\end{aligned}
```

## Dinámica curiosa

Tiene simetría cíclica y trayectorias que pueden recorrer una red espacial tipo laberinto. Es interesante porque conecta caos, circuitos de retroalimentación y estructuras de flujo con simetría.

## Referencia base

Thomas, R. (1999). *Deterministic Chaos Seen in Terms of Feedback Circuits: Analysis, Synthesis, "Labyrinth Chaos"*. *International Journal of Bifurcation and Chaos*, 9, 1889–1905. DOI: `10.1142/S0218127499001383`.

---

# 15. Modelo Hindmarsh–Rose

**Tipo:** modelo neuronal de tres variables; sistema lento-rápido.  
**Autores:** J. L. Hindmarsh y R. M. Rose.  
**Trabajo original:** *A Model of Neuronal Bursting Using Three Coupled First Order Differential Equations*, *Proceedings of the Royal Society of London. Series B*.  
**Año:** 1984.

## Ecuaciones canónicas

```math
\begin{aligned}
\dot{x} &= y-a x^3+b x^2-z+I,\\
\dot{y} &= c-d x^2-y,\\
\dot{z} &= r\left(s(x-x_R)-z\right).
\end{aligned}
```

## Dinámica curiosa

Modela disparos neuronales y ráfagas. La separación de escalas entre las variables rápidas y lentas permite obtener oscilaciones, bursting periódico, bursting irregular y regímenes caóticos.

## Referencia base

Hindmarsh, J. L., & Rose, R. M. (1984). *A Model of Neuronal Bursting Using Three Coupled First Order Differential Equations*. *Proceedings of the Royal Society of London. Series B*, 221(1222), 87–102. DOI: `10.1098/rspb.1984.0024`.

---

# 16. Modelo Lorenz-96

**Tipo:** sistema de ODEs de dimensión alta en una red cíclica.  
**Autor:** Edward N. Lorenz.  
**Trabajo original:** *Predictability — A Problem Partly Solved*.  
**Año:** 1996.

## Ecuaciones canónicas

Para \(j=1,\ldots,J\), con índices cíclicos:

```math
\frac{dX_j}{dt}=
(X_{j+1}-X_{j-2})X_{j-1}-X_j+F.
```

Condiciones cíclicas:

```math
X_{-1}=X_{J-1},\qquad X_0=X_J,\qquad X_{J+1}=X_1.
```

Parámetros típicos:

```math
J=40,\qquad F=8.
```

## Dinámica curiosa

Es un modelo atmosférico conceptual usado para predictibilidad, asimilación de datos y métodos de pronóstico por ensamble. Tiene dimensión alta, acoplamiento local en anillo, advección no lineal, disipación y forzamiento constante.

## Referencia base

Lorenz, E. N. (1996). *Predictability — A Problem Partly Solved*. En *Seminar on Predictability*, European Centre for Medium-Range Weather Forecasts, Reading, UK, 1–18.

---

# Recomendaciones de uso para investigación

Para una librería de atractores ocultos, caos fraccionario, cifrado y validación numérica, estos sistemas pueden organizarse así:

| Propósito | Sistemas útiles |
|---|---|
| Validación básica de integradores ODE | Lorenz, Rössler, Chen, Lü, Sprott A |
| No linealidad por tramos y circuitos | Chua |
| Mapas discretos y PRNG | Logístico, Hénon, Ikeda |
| Retardo e infinita dimensión efectiva | Mackey–Glass |
| Coexistencia, forzamiento y Poincaré | Duffing–Ueda |
| Dinámica física/geofísica | Rikitake, Lorenz-96 |
| Dinámica neuronal lenta-rápida | Hindmarsh–Rose |
| Sistemas con geometría poco usual | Thomas, Rabinovich–Fabrikant |

---

# Referencias bibliográficas base

1. Lorenz, E. N. (1963). *Deterministic Nonperiodic Flow*. *Journal of the Atmospheric Sciences*, 20(2), 130–141. DOI: `10.1175/1520-0469(1963)020<0130:DNF>2.0.CO;2`.
2. Rössler, O. E. (1976). *An Equation for Continuous Chaos*. *Physics Letters A*, 57(5), 397–398. DOI: `10.1016/0375-9601(76)90101-8`.
3. Matsumoto, T. (1984). *A Chaotic Attractor from Chua's Circuit*. *IEEE Transactions on Circuits and Systems*, CAS-31, 1055–1058.
4. Chua, L. O., Komuro, M., & Matsumoto, T. (1986). *The Double Scroll Family*. *IEEE Transactions on Circuits and Systems*, 33(11), 1072–1118.
5. Chen, G., & Ueta, T. (1999). *Yet Another Chaotic Attractor*. *International Journal of Bifurcation and Chaos*, 9(7), 1465–1466. DOI: `10.1142/S0218127499001024`.
6. Lü, J., & Chen, G. (2002). *A New Chaotic Attractor Coined*. *International Journal of Bifurcation and Chaos*, 12(3), 659–661. DOI: `10.1142/S0218127402004620`.
7. Hénon, M. (1976). *A Two-Dimensional Mapping with a Strange Attractor*. *Communications in Mathematical Physics*, 50(1), 69–77. DOI: `10.1007/BF01608556`.
8. May, R. M. (1976). *Simple Mathematical Models with Very Complicated Dynamics*. *Nature*, 261, 459–467. DOI: `10.1038/261459a0`.
9. Ikeda, K. (1979). *Multiple-Valued Stationary State and Its Instability of the Transmitted Light by a Ring Cavity System*. *Optics Communications*, 30(2), 257–261. DOI: `10.1016/0030-4018(79)90090-7`.
10. Mackey, M. C., & Glass, L. (1977). *Oscillation and Chaos in Physiological Control Systems*. *Science*, 197(4300), 287–289. DOI: `10.1126/science.267326`.
11. Ueda, Y. (1979). *Randomly Transitional Phenomena in the System Governed by Duffing's Equation*. *Journal of Statistical Physics*, 20, 181–196. DOI: `10.1007/BF01011512`.
12. Rabinovich, M. I., & Fabrikant, A. L. (1979). *Stochastic Self-Modulation of Waves in Nonequilibrium Media*. *Soviet Physics JETP*, 50, 311–317.
13. Rikitake, T. (1958). *Oscillations of a System of Disk Dynamos*. *Proceedings of the Cambridge Philosophical Society*, 54, 89–105. DOI: `10.1017/S0305004100033223`.
14. Sprott, J. C. (1994). *Some Simple Chaotic Flows*. *Physical Review E*, 50, R647–R650. DOI: `10.1103/PhysRevE.50.R647`.
15. Thomas, R. (1999). *Deterministic Chaos Seen in Terms of Feedback Circuits: Analysis, Synthesis, "Labyrinth Chaos"*. *International Journal of Bifurcation and Chaos*, 9, 1889–1905. DOI: `10.1142/S0218127499001383`.
16. Hindmarsh, J. L., & Rose, R. M. (1984). *A Model of Neuronal Bursting Using Three Coupled First Order Differential Equations*. *Proceedings of the Royal Society of London. Series B*, 221(1222), 87–102. DOI: `10.1098/rspb.1984.0024`.
17. Lorenz, E. N. (1996). *Predictability — A Problem Partly Solved*. En *Seminar on Predictability*, European Centre for Medium-Range Weather Forecasts, Reading, UK, 1–18.
---

# Apéndice A. Sistemas multiscroll / n-scroll que faltaban en la versión inicial

> Nota: los atractores multiscroll no suelen corresponder a un único “sistema canónico” universal. En la literatura aparecen como familias parametrizadas, normalmente construidas al añadir no linealidades por tramos, funciones saturadas, funciones signo, histéresis, senoidales o controladores de realimentación a un sistema base. Por eso, en esta sección se dan las formas matemáticas representativas y la referencia primaria más útil para cada familia.

## A1. Circuito de Chua generalizado con 3-scroll y 5-scroll

**Tipo:** sistema autónomo 3D por tramos; extensión multiscroll del circuito de Chua.  
**Autores del trabajo experimental:** M. E. Yalçın, J. A. K. Suykens y J. Vandewalle.  
**Trabajo:** *Experimental Confirmation of 3- and 5-Scroll Attractors from a Generalized Chua's Circuit*.  
**Revista:** *IEEE Transactions on Circuits and Systems I: Fundamental Theory and Applications*.  
**Año:** 2000.  
**Antecedente:** circuito de Chua generalizado propuesto por Suykens, Huang y Chua.

### Ecuaciones representativas

```math
\begin{aligned}
\dot{x} &= \alpha\,[y-h(x)],\\
\dot{y} &= x-y+z,\\
\dot{z} &= -\beta y,
\end{aligned}
```

con una característica lineal por tramos con múltiples puntos de quiebre:

```math
h(x)=m_{2q-1}x+\frac{1}{2}\sum_{i=1}^{2q-1}(m_{i-1}-m_i)
\left(|x+c_i|-|x-c_i|\right).
```

La elección de los vectores de pendientes `m` y puntos de quiebre `c` permite obtener 3-scroll, 5-scroll y variantes `n-scroll`.

### Dinámica curiosa

Es una extensión directa del doble scroll de Chua. Mantiene una estructura tipo Lur'e, pero aumenta el número de lóbulos mediante una no linealidad PWL con más segmentos. Es relevante para circuitos, sincronización y comunicaciones seguras basadas en caos.

### Referencia base

Yalçın, M. E., Suykens, J. A. K., & Vandewalle, J. (2000). *Experimental Confirmation of 3- and 5-Scroll Attractors from a Generalized Chua's Circuit*. *IEEE Transactions on Circuits and Systems I: Fundamental Theory and Applications*, 47(3), 425–429. DOI: `10.1109/81.841918`.

---

## A2. Familias de atractores scroll-grid: 1D, 2D y 3D

**Tipo:** familia Lur'e de sistemas autónomos 3D con no linealidades escalón.  
**Autores:** M. E. Yalçın, J. A. K. Suykens, J. Vandewalle y S. Özoğuz.  
**Trabajo:** *Families of Scroll Grid Attractors*.  
**Revista:** *International Journal of Bifurcation and Chaos*.  
**Año:** 2002.

### Ecuaciones representativas

La familia se formula como:

```math
\dot{\mathbf{x}}=A\mathbf{x}+B\Phi(\mathbf{x}), \qquad \mathbf{x}=(x,y,z)^T,
```

con, para el generador 1D básico,

```math
A=\begin{pmatrix}
0&1&0\\
0&0&1\\
-a&-a&-a
\end{pmatrix},
\qquad
B=\begin{pmatrix}
0&0&0\\
0&0&0\\
0&0&a
\end{pmatrix},
\qquad
\Phi(\mathbf{x})=\begin{pmatrix}0\\0\\f_1(x)\end{pmatrix}.
```

La no linealidad se construye con funciones núcleo de tipo escalón:

```math
f_1(x)=\sum_{i=1}^{M_x}g_{(-2i+1)/2}(x)+\sum_{i=1}^{N_x}g_{(2i-1)/2}(x),
```

```math
g_\theta(\zeta)=
\begin{cases}
1, & \zeta\geq \theta,\ \theta>0,\\
0, & \zeta<\theta,\ \theta>0,\\
0, & \zeta\geq \theta,\ \theta<0,\\
-1, & \zeta<\theta,\ \theta<0.
\end{cases}
```

La cantidad de scrolls 1D es `M_x+N_x+1`. Al introducir no linealidades adicionales en las direcciones `y` y `z`, se obtienen rejillas `n \times m` y `n \times m \times l`.

### Dinámica curiosa

A diferencia de un doble scroll aislado, aquí los lóbulos se distribuyen como una red de equilibrios. La misma arquitectura puede generar 3-scroll, 5-scroll, 10-scroll, rejillas 2D y rejillas 3D como `2×2×2` o `4×3×2`.

### Referencia base

Yalçın, M. E., Suykens, J. A. K., Vandewalle, J., & Özoğuz, S. (2002). *Families of Scroll Grid Attractors*. *International Journal of Bifurcation and Chaos*, 12(1), 23–41. DOI: `10.1142/S0218127402004218`.

---

## A3. Atractores multiscroll mediante series de funciones saturadas

**Tipo:** familia de sistemas autónomos 3D lineales controlados por funciones saturadas.  
**Autores:** J. Lü, G. Chen, X. Yu y H. Leung.  
**Trabajo:** *Design and Analysis of Multiscroll Chaotic Attractors From Saturated Function Series*.  
**Revista:** *IEEE Transactions on Circuits and Systems I: Regular Papers*.  
**Año:** 2004.

### Forma matemática representativa

La idea central es partir de un sistema lineal 3D y cerrarlo con una función saturada o una serie de funciones saturadas:

```math
\dot{\mathbf{x}}=A\mathbf{x}+B\,u,\qquad u=f(C\mathbf{x}),
```

con `f` construida como una serie de funciones saturadas por tramos. La estructura permite generar familias 1D `n-scroll`, 2D `n\times m` y 3D `n\times m\times l`.

Una función saturada elemental puede escribirse genéricamente como una función PWL con mesetas:

```math
s(u)=
\begin{cases}
-k, & u<-E,\\
\lambda u, & |u|\leq E,\\
k, & u>E,
\end{cases}
```

mientras que la serie saturada se obtiene desplazando y sumando varias copias de `s(u)` para crear múltiples mesetas y puntos de conmutación.

### Dinámica curiosa

Esta familia es importante porque da una metodología sistemática de diseño: no sólo reproduce un número dado de scrolls, sino que permite organizar scrolls en una, dos o tres direcciones. Es más una técnica constructiva general que un sistema aislado.

### Referencia base

Lü, J., Chen, G., Yu, X., & Leung, H. (2004). *Design and Analysis of Multiscroll Chaotic Attractors From Saturated Function Series*. *IEEE Transactions on Circuits and Systems I: Regular Papers*, 51(12), 2476–2490. DOI: `10.1109/TCSI.2004.838151`.

---

## A4. Sistema de Chen controlado con atractores multiscroll e hiperchaóticos

**Tipo:** extensión controlada del sistema de Chen; ODE 3D y variante con retardo.  
**Autores:** Xinzhi Liu, Xuemin Shen y Hongtao Zhang.  
**Trabajo:** *Multi-Scroll Chaotic and Hyperchaotic Attractors Generated from Chen System*.  
**Revista:** *International Journal of Bifurcation and Chaos*.  
**Año:** 2012.

### Ecuaciones base

El sistema de Chen clásico se escribe como:

```math
\begin{aligned}
\dot{x} &= a(y-x),\\
\dot{y} &= (c-a)x-xz+cy,\\
\dot{z} &= xy-bz.
\end{aligned}
```

La versión controlada sustituye el término `xz` por `xu`, con control no lineal:

```math
\begin{aligned}
\dot{x} &= a(y-x),\\
\dot{y} &= (c-a)x-xu+cy,\\
\dot{z} &= xy-bz,
\end{aligned}
```

```math
u(t)=d_1z(t)-d_2\sin(z(t)).
```

Parámetros usados para el ejemplo de 6-scroll:

```math
a=35,\qquad b=3,\qquad c=28,\qquad d_1=1,\qquad d_2=8.
```

### Dinámica curiosa

Al variar los parámetros de control se incrementa el número de puntos de equilibrio y se obtienen atractores con más scrolls. Al introducir retardo en la realimentación, la familia se extiende a atractores hiperchaóticos.

### Referencia base

Liu, X., Shen, X., & Zhang, H. (2012). *Multi-Scroll Chaotic and Hyperchaotic Attractors Generated from Chen System*. *International Journal of Bifurcation and Chaos*, 22(2), 1250033. DOI: `10.1142/S0218127412500332`.

---

## A5. Circuito jerk general para atractores n-scroll

**Tipo:** sistema jerk/circuito analógico con función moduladora no lineal.  
**Autores:** S. Yu, J. Lü, H. Leung y G. Chen.  
**Trabajo:** *Design and Implementation of n-Scroll Chaotic Attractors From a General Jerk Circuit*.  
**Revista:** *IEEE Transactions on Circuits and Systems I: Regular Papers*.  
**Año:** 2005.

### Forma matemática representativa

El sistema se formula como una ecuación jerk de tercer orden, equivalente a un sistema de primer orden:

```math
\dddot{x}=J(x,\dot{x},\ddot{x};f),
```

```math
\begin{aligned}
\dot{x} &= y,\\
\dot{y} &= z,\\
\dot{z} &= J(x,y,z;f),
\end{aligned}
```

con `f` una función moduladora ajustable, por ejemplo de tipo diente de sierra, triangular o transconductora. La función `f` controla anchuras, pendientes, puntos de quiebre, puntos de equilibrio y número de scrolls.

### Dinámica curiosa

La metodología permite diseñar atractores `n-scroll` con gran control geométrico. El artículo reporta implementaciones de 3 a 12 scrolls y verificación experimental de un atractor de 12 scrolls en circuito analógico.

### Referencia base

Yu, S., Lü, J., Leung, H., & Chen, G. (2005). *Design and Implementation of n-Scroll Chaotic Attractors From a General Jerk Circuit*. *IEEE Transactions on Circuits and Systems I: Regular Papers*, 52(7), 1459–1476. DOI: `10.1109/TCSI.2005.851717`.


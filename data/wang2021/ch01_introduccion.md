# Capítulo 1. Introducción: Catálogo de Sistemas caóticos

Este documento recopila la información teórica y numérica de los sistemas dinámicos caóticos presentados en el Capítulo 1 del libro *Chaotic Systems with Multistability and Hidden Attractors* (2021).

## 1. Sistema de Lorenz (`lorenz`)
- **Ecuaciones**:
  $$ \dot{x} = \sigma (y - x) $$
  $$ \dot{y} = \rho x - y - xz $$
  $$ \dot{z} = xy - \beta z $$
- **Parámetros Canónicos**: $\sigma = 10$, $\rho = 28$, $\beta = 8/3$.
- **Dinámica**: Atractor autocitado clásico con estructura en forma de mariposa.
- **Equilibrios**:
  - $O = (0, 0, 0)$ (Silla)
  - $E_+ = (6\sqrt{2}, 6\sqrt{2}, 27)$ (Silla-foco inestable)
  - $E_- = (-6\sqrt{2}, -6\sqrt{2}, 27)$ (Silla-foco inestable)

---

## 2. Sistema de Rössler (`rossler`)
- **Ecuaciones**:
  $$ \dot{x} = -y - z $$
  $$ \dot{y} = x + ay $$
  $$ \dot{z} = b + z(x - c) $$
- **Parámetros Canónicos**: $a = 0.2$, $b = 0.2$, $c = 5.7$.
- **Dinámica**: Atractor espiral con una sola banda.
- **Equilibrios**:
  - $E_1 \approx (0.007, -0.035, 0.035)$
  - $E_2 \approx (5.693, -28.465, 28.465)$

---

## 3. Circuito de Chua (`chua`)
- **Ecuaciones**:
  $$ \dot{x} = \alpha (y - x - h(x)) $$
  $$ \dot{y} = x - y + z $$
  $$ \dot{z} = -\beta y $$
  $$ h(x) = m_1 x + \frac{1}{2}(m_0 - m_1)(|x+1| - |x-1|) $$
- **Parámetros Canónicos**: $\alpha = 15.6$, $\beta = 28.0$, $m_0 = -1.143$, $m_1 = -0.714$.
- **Dinámica**: Atractor de doble scroll en circuito no suave.
- **Equilibrios**:
  - $O = (0, 0, 0)$ (Silla-foco inestable)
  - $P_+ = (1.5, 0, -1.5)$ (Silla-foco inestable)
  - $P_- = (-1.5, 0, 1.5)$ (Silla-foco inestable)

---

## 4. Sistema de Chen (`chen`)
- **Ecuaciones**:
  $$ \dot{x} = a(y - x) $$
  $$ \dot{y} = (c - a)x - xz + cy $$
  $$ \dot{z} = xy - bz $$
- **Parámetros Canónicos**: $a = 35$, $b = 3$, $c = 28$.
- **Dinámica**: Atractor similar a Lorenz pero con topología diferente.
- **Equilibrios**:
  - $O = (0, 0, 0)$ (Silla inestable)
  - $E_1 = (\sqrt{63}, \sqrt{63}, 21) \approx (7.937, 7.937, 21)$ (Silla-foco inestable)
  - $E_2 = (-\sqrt{63}, -\sqrt{63}, 21) \approx (-7.937, -7.937, 21)$ (Silla-foco inestable)

---

## 5. Sistema Unificado Lorenz-Chen (`unified_lorenz_chen`)
- **Ecuaciones**:
  $$ \dot{x} = (25\alpha + 10)(y - x) $$
  $$ \dot{y} = (28 - 35\alpha)x + (29\alpha - 1)y - xz $$
  $$ \dot{z} = -\frac{\alpha + 8}{3}z + xy $$
- **Parámetros**: $\alpha \in [0, 1]$. Interpolación continua entre Lorenz ($\alpha = 0$) y Chen ($\alpha = 1$).
- **Equilibrios**:
  - $O = (0, 0, 0)$
  - $E_{\pm} = (\pm \sqrt{\beta(27 - 6\alpha)}, \pm \sqrt{\beta(27 - 6\alpha)}, 27 - 6\alpha)$ donde $\beta = (\alpha + 8)/3$.

---

## 6. Sistemas de Sprott A-S (`sprott_a` a `sprott_s`)

A continuación se comparan los equilibrios reportados en el libro (Tabla de Cap. 1) con los calculados numéricamente mediante el resolvedor algebraico y numérico implementado.

| ID | Ecuaciones Canónicas | Equilibrios Reportados | Equilibrios Calculados | Notas de Discrepancia |
|---|---|---|---|---|
| **sprott_a** | $\dot{x}=y$, $\dot{y}=-x+yz$, $\dot{z}=1-y^2$ | Ninguno | Ninguno | Coincide. |
| **sprott_b** | $\dot{x}=yz$, $\dot{y}=x-y$, $\dot{z}=1-xy$ | $(1,1,0)$, $(-1,-1,0)$ | $(1,1,0)$, $(-1,-1,0)$ | Coincide. |
| **sprott_c** | $\dot{x}=yz$, $\dot{y}=x-y$, $\dot{z}=1-x^2$ | $(1,1,0)$, $(-1,-1,0)$ | $(1,1,0)$, $(-1,-1,0)$ | Coincide. |
| **sprott_d** | $\dot{x}=-y$, $\dot{y}=x+z$, $\dot{z}=xz+3y^2$ | $(0,0,0)$ | $(0,0,0)$ | Coincide. |
| **sprott_e** | $\dot{x}=yz$, $\dot{y}=x^2-y$, $\dot{z}=1-4x$ | $(0.25, 0.063, 0)$ | $(0.25, 0.0625, 0)$ | Coincide (redondeo en el libro). |
| **sprott_f** | $\dot{x}=y+z$, $\dot{y}=-x+0.5y$, $\dot{z}=x^2-z$ | $(0,0,0)$, $(-2,-4,4)$ | $(0,0,0)$, $(-2,-4,4)$ | Coincide. |
| **sprott_g** | $\dot{x}=0.4x+z$, $\dot{y}=xz-y$, $\dot{z}=-x+y$ | $(0,0,0)$, $(-2.5,-2.5,1)$ | $(0,0,0)$, $(-2.5,-2.5,1)$ | Coincide. |
| **sprott_h** | $\dot{x}=-y+z^2$, $\dot{y}=x+0.5y$, $\dot{z}=x-z$ | $(0,0,0)$, $(-2,4,-2)$ | $(0,0,0)$, $(-2,4,-2)$ | Coincide. |
| **sprott_i** | $\dot{x}=0.2y$, $\dot{y}=x+z$, $\dot{z}=x+y^2-z$ | $(0,0,0)$ | $(0,0,0)$ | Coincide. |
| **sprott_j** | $\dot{x}=2z$, $\dot{y}=-2y+z$, $\dot{z}=-x+y+y^2$ | $(0,0,0)$ | $(0,0,0)$ | Coincide. |
| **sprott_k** | $\dot{x}=xy-z$, $\dot{y}=x-y$, $\dot{z}=x+0.3z$ | $(0,0,0)$, $(-3.333,-3.333,11.111)$ | $(0,0,0)$, $(-3.333,-3.333,11.111)$ | Coincide (redondeo). |
| **sprott_l** | $\dot{x}=y+3.9z$, $\dot{y}=0.9x^2-y$, $\dot{z}=1-x$ | $(1, 1.111, -0.231)$ | $(1, 0.9, -0.2308)$ | **Discrepancia detectada**: Si $x=1$ y $\dot{y}=0$, entonces $y = 0.9 x^2 = 0.9$. El libro muestra $1.111$ (que es $1/0.9$). Posible error de tipografía en el texto original. |
| **sprott_m** | $\dot{x}=-z$, $\dot{y}=-x^2-y$, $\dot{z}=1.7+1.7x+y$ | $(2.406,-5.791,0)$, $(-0.706,-0.499,0)$ | $(2.406,-5.791,0)$, $(-0.706,-0.499,0)$ | Coincide. |
| **sprott_n** | $\dot{x}=-2y$, $\dot{y}=x+z^2$, $\dot{z}=1+y-2z$ | $(-0.25,0,0.5)$ | $(-0.25,0,0.5)$ | Coincide. |
| **sprott_o** | $\dot{x}=y$, $\dot{y}=x-z$, $\dot{z}=x+xz+2.7y$ | $(0,0,0)$, $(-1,0,-1)$ | $(0,0,0)$, $(-1,0,-1)$ | Coincide. |
| **sprott_p** | $\dot{x}=2.7y+z$, $\dot{y}=-x+y^2$, $\dot{z}=x+y$ | $(0,0,0)$, $(1,-1,2.7)$ | $(0,0,0)$, $(1,-1,2.7)$ | Coincide. |
| **sprott_q** | $\dot{x}=-z$, $\dot{y}=x-y$, $\dot{z}=3.1x+y^2+0.5z$ | $(0,0,0)$, $(-3.1,-3.1,0)$ | $(0,0,0)$, $(-3.1,-3.1,0)$ | Coincide. |
| **sprott_r** | $\dot{x}=0.9-y$, $\dot{y}=0.4+z$, $\dot{z}=xy-z$ | $(-0.444, 1.111, -0.4)$ | $(-0.4444, 0.9, -0.4)$ | **Discrepancia detectada**: Si $\dot{x}=0$, entonces $y=0.9$. El libro muestra $1.111$ (que es $1/0.9$). Posible error de tipografía. |
| **sprott_s** | $\dot{x}=x-4y$, $\dot{y}=x+z^2$, $\dot{z}=1+x$ | $(-1, 0.25, 1)$, $(-1, 0.25, -1)$ | $(-1, -0.25, 1)$, $(-1, -0.25, -1)$ | **Discrepancia detectada**: Si $x=-1$ y $\dot{x}=0$, entonces $x-4y = 0 \implies y = -0.25$. El libro reporta $0.25$. |

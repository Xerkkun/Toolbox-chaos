# Catálogo de Sistemas Caóticos de Wang, Kuznetsov y Chen (2021)

Este catálogo estructurado describe los sistemas caóticos del libro *Chaotic Systems with Multistability and Hidden Attractors* (Springer, 2021) que han sido integrados, calculados y verificados en Chaos Toolbox.

## Lorenz system (`lorenz`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Lorenz, E. N. (1963). Deterministic nonperiodic flow. Journal of the Atmospheric Sciences.
- **Ecuaciones (LaTeX)**: $$\dot{x}=\sigma(y-x), \; \dot{y}=\rho x-y-xz, \; \dot{z}=xy-\beta z$$
- **Parámetros**: `{'sigma': 10.0, 'rho': 28.0, 'beta': 2.6666666666666665}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.9056, 0.0, -14.5723]
kaplan_yorke_dimension: 2.06
```
- **Equilibrios reportados por el libro**: `O(0,0,0) (saddle), $E_+(6\sqrt{2}, 6\sqrt{2}, 27)$, $E_-(-6\sqrt{2}, -6\sqrt{2}, 27)$`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[11.8277, -2.6667, -22.8277]`
    - *Clasificación*: `saddle`
  - **E2**: `(8.4853, 8.4853, 27.0000)`
    - *Autovalores*: `[0.0940 + 10.1945i, 0.0940 + -10.1945i, -13.8546]`
    - *Clasificación*: `saddle_focus`
  - **E3**: `(-8.4853, -8.4853, 27.0000)`
    - *Autovalores*: `[0.0940 + 10.1945i, 0.0940 + -10.1945i, -13.8546]`
    - *Clasificación*: `saddle_focus`

---

## Rössler system (`rossler`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Rössler, O. E. (1976). An Equation for Continuous Chaos. Physics Letters A.
- **Ecuaciones (LaTeX)**: $$\dot{x}=-y-z, \; \dot{y}=x+ay, \; \dot{z}=b+z(x-c)$$
- **Parámetros**: `{'a': 0.2, 'b': 0.2, 'c': 5.7}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.0714, 0.0, -5.3943]
kaplan_yorke_dimension: 2.013
```
- **Equilibrios reportados por el libro**: `E1(0.007, -0.035, 0.035), E2(5.693, -28.465, 28.465)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0070, -0.0351, 0.0351)`
    - *Autovalores*: `[0.0970 + 0.9952i, 0.0970 + -0.9952i, -5.6870]`
    - *Clasificación*: `saddle_focus`
  - **E2**: `(5.6930, -28.4649, 28.4649)`
    - *Autovalores*: `[0.1930, -0.0000 + 5.4280i, -0.0000 + -5.4280i]`
    - *Clasificación*: `saddle_focus`

---

## Chua circuit, piecewise-linear form (`chua`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Chua, L. O. (1984). A Chaotic Attractor from Chua's Circuit. IEEE Transactions on Circuits and Systems.
- **Ecuaciones (LaTeX)**: $$\dot{x}=\alpha(y-x-h(x)), \; \dot{y}=x-y+z, \; \dot{z}=-\beta y$$
- **Parámetros**: `{'alpha': 15.6, 'beta': 28.0, 'm0': -1.143, 'm1': -0.714}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
```
- **Equilibrios reportados por el libro**: `O(0,0,0) (saddle-focus), P+(1.5, 0, -1.5), P-(-1.5, 0, 1.5)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[3.4756, -1.1224 + 4.0880i, -1.1224 + -4.0880i]`
    - *Clasificación*: `saddle_focus`
  - **E2**: `(1.5000, 0.0000, -1.5000)`
    - *Autovalores*: `[0.3055 + 4.5253i, 0.3055 + -4.5253i, -6.0726]`
    - *Clasificación*: `saddle_focus`
  - **E3**: `(-1.5000, 0.0000, 1.5000)`
    - *Autovalores*: `[0.3055 + 4.5253i, 0.3055 + -4.5253i, -6.0726]`
    - *Clasificación*: `saddle_focus`

---

## Chen system (`chen`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Chen, G., Ueta, T. (1999). Yet another chaotic attractor. International Journal of Bifurcation and Chaos.
- **Ecuaciones (LaTeX)**: $$\dot{x}=a(y-x), \; \dot{y}=(c-a)x-xz+cy, \; \dot{z}=xy-bz$$
- **Parámetros**: `{'a': 35.0, 'b': 3.0, 'c': 28.0}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
```
- **Equilibrios reportados por el libro**: `O(0,0,0), E1(7.937, 7.937, 21), E2(-7.937, -7.937, 21)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[23.8359, -3.0000, -30.8359]`
    - *Clasificación*: `saddle`
  - **E2**: `(7.9373, 7.9373, 21.0000)`
    - *Autovalores*: `[4.2140 + 14.8846i, 4.2140 + -14.8846i, -18.4280]`
    - *Clasificación*: `saddle_focus`
  - **E3**: `(-7.9373, -7.9373, 21.0000)`
    - *Autovalores*: `[4.2140 + 14.8846i, 4.2140 + -14.8846i, -18.4280]`
    - *Clasificación*: `saddle_focus`

---

## Unified Lorenz-Chen system (`unified_lorenz_chen`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Lü, J., Chen, G., Zhang, S. (2002). The compound structure of a new chaotic attractor. Chaos, Solitons & Fractals.
- **Ecuaciones (LaTeX)**: $$\dot{x}=(25\alpha+10)(y-x), \; \dot{y}=(28-35\alpha)x+(29\alpha-1)y-xz, \; \dot{z}=-\frac{\alpha+8}{3}z+xy$$
- **Parámetros**: `{'alpha': 0.0}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited (alpha=0: Lorenz, alpha=1: Chen)
```
- **Equilibrios reportados por el libro**: `O(0,0,0), E1, E2 dependent on alpha`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[11.8277, -2.6667, -22.8277]`
    - *Clasificación*: `saddle`
  - **E2**: `(8.4853, 8.4853, 27.0000)`
    - *Autovalores*: `[0.0940 + 10.1945i, 0.0940 + -10.1945i, -13.8546]`
    - *Clasificación*: `saddle_focus`
  - **E3**: `(-8.4853, -8.4853, 27.0000)`
    - *Autovalores*: `[0.0940 + 10.1945i, 0.0940 + -10.1945i, -13.8546]`
    - *Clasificación*: `saddle_focus`

---

## Sprott A system (`sprott_a`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y, \; \dot{y}=-x+yz, \; \dot{z}=1.0-y2$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: conservative_chaotic_sea
lyapunov_exponents: [0.014, 0.0, -0.014]
kaplan_yorke_dimension: 3.000
```
- **Equilibrios reportados por el libro**: `Ninguno`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---

## Sprott B system (`sprott_b`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=yz, \; \dot{y}=x-y, \; \dot{z}=1.0-xy$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.21, 0.0, -1.21]
kaplan_yorke_dimension: 2.174
```
- **Equilibrios reportados por el libro**: `(1,1,0), (-1,-1,0)`
- **Equilibrios calculados por el código**:
  - **E1**: `(1.0000, 1.0000, -0.0000)`
    - *Autovalores*: `[0.1766 + 1.2028i, 0.1766 + -1.2028i, -1.3532]`
    - *Clasificación*: `saddle_focus`
  - **E2**: `(-1.0000, -1.0000, 0.0000)`
    - *Autovalores*: `[0.1766 + 1.2028i, 0.1766 + -1.2028i, -1.3532]`
    - *Clasificación*: `saddle_focus`

---

## Sprott C system (`sprott_c`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=yz, \; \dot{y}=x-y, \; \dot{z}=1.0-x2$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.163, 0.0, -0.163]
kaplan_yorke_dimension: 2.140
```
- **Equilibrios reportados por el libro**: `(1,1,0), (-1,-1,0)`
- **Equilibrios calculados por el código**:
  - **E1**: `(1.0000, 1.0000, -0.0000)`
    - *Autovalores*: `[-0.0000 + 1.4142i, -0.0000 + -1.4142i, -1.0000]`
    - *Clasificación*: `nonhyperbolic`
  - **E2**: `(-1.0000, -1.0000, 0.0000)`
    - *Autovalores*: `[0.0000 + 1.4142i, 0.0000 + -1.4142i, -1.0000]`
    - *Clasificación*: `nonhyperbolic`

---

## Sprott D system (`sprott_d`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=-y, \; \dot{y}=x+z, \; \dot{z}=xz+3.0y2$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.103, 0.0, -1.32]
kaplan_yorke_dimension: 2.078
```
- **Equilibrios reportados por el libro**: `(0,0,0)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[0.0000 + 1.0000i, 0.0000 + -1.0000i, 0.0000]`
    - *Clasificación*: `nonhyperbolic`

---

## Sprott E system (`sprott_e`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=yz, \; \dot{y}=x2-y, \; \dot{z}=1.0-4.0x$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.078, 0.0, -1.078]
kaplan_yorke_dimension: 2.072
```
- **Equilibrios reportados por el libro**: `(0.25, 0.063, 0)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.2500, 0.0625, 0.0000)`
    - *Autovalores*: `[0.0000 + 0.5000i, 0.0000 + -0.5000i, -1.0000]`
    - *Clasificación*: `nonhyperbolic`

---

## Sprott F system (`sprott_f`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y+z, \; \dot{y}=-x+0.5y, \; \dot{z}=x2-z$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.117, 0.0, -0.617]
kaplan_yorke_dimension: 2.190
```
- **Equilibrios reportados por el libro**: `(0,0,0), (-2,-4,4)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[0.2500 + 0.9682i, 0.2500 + -0.9682i, -1.0000]`
    - *Clasificación*: `saddle_focus`

---

## Sprott G system (`sprott_g`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=0.4x+z, \; \dot{y}=xz-y, \; \dot{z}=-x+y$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.034, 0.0, -0.634]
kaplan_yorke_dimension: 2.054
```
- **Equilibrios reportados por el libro**: `(0,0,0), (-2.5,-2.5,1)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[0.2000 + 0.9798i, 0.2000 + -0.9798i, -1.0000]`
    - *Clasificación*: `saddle_focus`
  - **E2**: `(-2.5000, -2.5000, 1.0000)`
    - *Autovalores*: `[0.2970, -0.4485 + 1.7791i, -0.4485 + -1.7791i]`
    - *Clasificación*: `saddle_focus`

---

## Sprott H system (`sprott_h`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=-y+z2, \; \dot{y}=x+0.5y, \; \dot{z}=x-z$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.117, 0.0, -0.617]
kaplan_yorke_dimension: 2.190
```
- **Equilibrios reportados por el libro**: `(0,0,0), (-2,4,-2)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[0.2500 + 0.9682i, 0.2500 + -0.9682i, -1.0000]`
    - *Clasificación*: `saddle_focus`

---

## Sprott I system (`sprott_i`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=0.2y, \; \dot{y}=x+z, \; \dot{z}=x+y2-z$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.012, 0.0, -1.012]
kaplan_yorke_dimension: 2.012
```
- **Equilibrios reportados por el libro**: `(0,0,0)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[0.5720, -0.7860 + 0.2854i, -0.7860 + -0.2854i]`
    - *Clasificación*: `saddle_focus`

---

## Sprott J system (`sprott_j`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=2.0z, \; \dot{y}=-2.0y+z, \; \dot{z}=-x+y+y2$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.076, 0.0, -2.076]
kaplan_yorke_dimension: 2.037
```
- **Equilibrios reportados por el libro**: `(0,0,0)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[0.1573 + 1.3052i, 0.1573 + -1.3052i, -2.3146]`
    - *Clasificación*: `saddle_focus`

---

## Sprott K system (`sprott_k`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=xy-z, \; \dot{y}=x-y, \; \dot{z}=x+0.3z$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.038, 0.0, -0.89]
kaplan_yorke_dimension: 2.042
```
- **Equilibrios reportados por el libro**: `(0,0,0), (-3.333,-3.333,11.111)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[0.1500 + 0.9887i, 0.1500 + -0.9887i, -1.0000]`
    - *Clasificación*: `saddle_focus`

---

## Sprott L system (`sprott_l`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y+3.9z, \; \dot{y}=0.9x2-y, \; \dot{z}=1.0-x$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.061, 0.0, -1.061]
kaplan_yorke_dimension: 2.057
```
- **Equilibrios reportados por el libro**: `(1, 1.111, -0.231)`
- **Equilibrios calculados por el código**:
  - **E1**: `(1.0000, 0.9000, -0.2308)`
    - *Autovalores*: `[0.2166 + 1.6353i, 0.2166 + -1.6353i, -1.4333]`
    - *Clasificación*: `saddle_focus`

---

## Sprott M system (`sprott_m`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=-z, \; \dot{y}=-x2-y, \; \dot{z}=1.7+1.7x+y$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.044, 0.0, -1.044]
kaplan_yorke_dimension: 2.042
```
- **Equilibrios reportados por el libro**: `(2.406,-5.791,0), (-0.706,-0.499,0)`
- **Equilibrios calculados por el código**:
  - **E1**: `(-0.7064, -0.4991, 0.0000)`
    - *Autovalores*: `[0.1946 + 1.4842i, 0.1946 + -1.4842i, -1.3892]`
    - *Clasificación*: `saddle_focus`
  - **E2**: `(2.4064, -5.7909, 0.0000)`
    - *Autovalores*: `[0.9074, -0.9537 + 1.5878i, -0.9537 + -1.5878i]`
    - *Clasificación*: `saddle_focus`

---

## Sprott N system (`sprott_n`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=-2.0y, \; \dot{y}=x+z2, \; \dot{z}=1.0+y-2.0z$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.076, 0.0, -2.076]
kaplan_yorke_dimension: 2.037
```
- **Equilibrios reportados por el libro**: `(-0.25,0,0.5)`
- **Equilibrios calculados por el código**:
  - **E1**: `(-0.2500, 0.0000, 0.5000)`
    - *Autovalores*: `[0.1573 + 1.3052i, 0.1573 + -1.3052i, -2.3146]`
    - *Clasificación*: `saddle_focus`

---

## Sprott O system (`sprott_o`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y, \; \dot{y}=x-z, \; \dot{z}=x+xz+2.7y$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.049, 0.0, -0.319]
kaplan_yorke_dimension: 2.154
```
- **Equilibrios reportados por el libro**: `(0,0,0), (-1,0,-1)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[0.2551 + 1.3767i, 0.2551 + -1.3767i, -0.5101]`
    - *Clasificación*: `saddle_focus`
  - **E2**: `(-1.0000, 0.0000, -1.0000)`
    - *Autovalores*: `[0.4315, -0.7157 + 1.3436i, -0.7157 + -1.3436i]`
    - *Clasificación*: `saddle_focus`

---

## Sprott P system (`sprott_p`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=2.7y+z, \; \dot{y}=-x+y2, \; \dot{z}=x+y$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.087, 0.0, -0.481]
kaplan_yorke_dimension: 2.181
```
- **Equilibrios reportados por el libro**: `(0,0,0), (1,-1,2.7)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[0.2551 + 1.3767i, 0.2551 + -1.3767i, -0.5101]`
    - *Clasificación*: `saddle_focus`
  - **E2**: `(1.0000, -1.0000, 2.7000)`
    - *Autovalores*: `[0.3828, -1.1914 + 1.0921i, -1.1914 + -1.0921i]`
    - *Clasificación*: `saddle_focus`

---

## Sprott Q system (`sprott_q`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=-z, \; \dot{y}=x-y, \; \dot{z}=3.1x+y2+0.5z$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.109, 0.0, -0.609]
kaplan_yorke_dimension: 2.179
```
- **Equilibrios reportados por el libro**: `(0,0,0), (-3.1,-3.1,0)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[0.2500 + 1.7428i, 0.2500 + -1.7428i, -1.0000]`
    - *Clasificación*: `saddle_focus`

---

## Sprott R system (`sprott_r`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=0.9-y, \; \dot{y}=0.4+z, \; \dot{z}=xy-z$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.062, 0.0, -1.062]
kaplan_yorke_dimension: 2.058
```
- **Equilibrios reportados por el libro**: `(-0.444, 1.111, -0.4)`
- **Equilibrios calculados por el código**:
  - **E1**: `(-0.4444, 0.9000, -0.4000)`
    - *Autovalores*: `[0.1161 + 0.8467i, 0.1161 + -0.8467i, -1.2321]`
    - *Clasificación*: `saddle_focus`

---

## Sprott S system (`sprott_s`)
- **Capítulo**: 1 | **Tipo**: clásico
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=x-4.0y, \; \dot{y}=x+z2, \; \dot{z}=1.0+x$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
lyapunov_exponents: [0.188, 0.0, -1.188]
kaplan_yorke_dimension: 2.151
```
- **Equilibrios reportados por el libro**: `(-1, 0.25, 1), (-1, 0.25,-1)`
- **Equilibrios calculados por el código**:
  - **E1**: `(-1.0000, -0.2500, 1.0000)`
    - *Autovalores*: `[1.1015 + 2.3317i, 1.1015 + -2.3317i, -1.2030]`
    - *Clasificación*: `saddle_focus`
  - **E2**: `(-1.0000, -0.2500, -1.0000)`
    - *Autovalores*: `[1.6075, -0.3038 + 2.2101i, -0.3038 + -2.2101i]`
    - *Clasificación*: `saddle_focus`

---

## Wang-Chen system with one stable equilibrium (`wang_chen_stable_equilibrium`)
- **Capítulo**: 3 | **Tipo**: con equilibrio estable
- **Referencia**: Wang, X., Chen, G. (2012). A chaotic system with only one stable equilibrium. Communications in Nonlinear Science and Numerical Simulation.
- **Ecuaciones (LaTeX)**: $$\dot{x}=yz+a, \; \dot{y}=x^2-y, \; \dot{z}=1-4x$$
- **Parámetros**: `{'a': 0.006}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
lyapunov_exponents: [0.0489, 0.0, -1.0485]
```
- **Equilibrios reportados por el libro**: `E(0.25, 0.0625, -16a) = (0.25, 0.0625, -0.096)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.2500, 0.0625, -0.0960)`
    - *Autovalores*: `[-0.0197 + 0.5097i, -0.0197 + -0.5097i, -0.9607]`
    - *Clasificación*: `stable_focus`

---

## Wei extended Sprott E system (`wei_extended_sprott_e`)
- **Capítulo**: 3 | **Tipo**: con equilibrio estable
- **Referencia**: Wei, Z. (2013). Chaotic behavior of a simple system with one stable equilibrium. Kybernetika.
- **Ecuaciones (LaTeX)**: $$\dot{x}=yz+ex^2+fx+g, \; \dot{y}=x^2-y, \; \dot{z}=1-4x$$
- **Parámetros**: `{'e': 0.0, 'f': -0.1, 'g': 0.02}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
```
- **Equilibrios reportados por el libro**: `E(0.25, 0.0625, -e-4f-16g) = (0.25, 0.0625, 0.08)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.2500, 0.0625, 0.0800)`
    - *Autovalores*: `[-0.0330 + 0.4906i, -0.0330 + -0.4906i, -1.0340]`
    - *Clasificación*: `stable_focus`

---

## Lao system (`lao`)
- **Capítulo**: 3 | **Tipo**: con equilibrio estable
- **Referencia**: Lao, S.-K., Shekofteh, Y., Jafari, S., Sprott, J. C. (2014). GMM parameter estimation of a chaotic circuit. International Journal of Bifurcation and Chaos.
- **Ecuaciones (LaTeX)**: $$\dot{x}=-z, \; \dot{y}=-x-z, \; \dot{z}=2x-1.3y-2z+x^2+z^2-xz$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
lyapunov_exponents: [0.018, 0.0, -2.018]
```
- **Equilibrios reportados por el libro**: `E(0, 0, 0)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[-0.0108 + 0.8106i, -0.0108 + -0.8106i, -1.9783]`
    - *Clasificación*: `stable_focus`

---

## Kingni system (`kingni`)
- **Capítulo**: 3 | **Tipo**: con equilibrio estable
- **Referencia**: Kingni, S., Jafari, S., Simo, H., Woafo, P. (2014). Three-dimensional chaotic autonomous system with only one stable equilibrium. European Physical Journal Plus.
- **Ecuaciones (LaTeX)**: $$\dot{x}=-z, \; \dot{y}=-x-z, \; \dot{z}=3x-ay+x^2-z^2-yz+b$$
- **Parámetros**: `{'a': 1.3, 'b': 1.01}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
```
- **Equilibrios reportados por el libro**: `E(0, b/a, 0) = (0, 0.7769, 0)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.7769, 0.0000)`
    - *Autovalores*: `[-0.0045 + 1.3012i, -0.0045 + -1.3012i, -0.7679]`
    - *Clasificación*: `stable_focus`

---

## Controlled LE1 system (`line_equilibrium_to_one_stable`)
- **Capítulo**: 3 | **Tipo**: con equilibrio estable
- **Referencia**: Pham, V.-T., et al. (2013). Line equilibrium system controlled to one stable equilibrium.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y, \; \dot{y}=-x+yz+c, \; \dot{z}=-x-axy-bxz$$
- **Parámetros**: `{'a': 15.0, 'b': 1.0, 'c': 0.001}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
```
- **Equilibrios reportados por el libro**: `E(c, 0, -1/b) = (0.001, 0, -1.0)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0010, 0.0000, -1.0000)`
    - *Autovalores*: `[-0.0010, -0.5000 + 0.8660i, -0.5000 + -0.8660i]`
    - *Clasificación*: `stable_focus`

---

## Yang-Chen system (`yang_chen`)
- **Capítulo**: 3 | **Tipo**: con equilibrio estable
- **Referencia**: Yang, Q., Chen, G. (2008). A chaotic system with one saddle and two stable node-foci. International Journal of Bifurcation and Chaos.
- **Ecuaciones (LaTeX)**: $$\dot{x}=a(y-x), \; \dot{y}=cx-xz, \; \dot{z}=-bz+xy$$
- **Parámetros**: `{'a': 35.0, 'b': 3.0, 'c': 35.0}`
- **Dinámica reportada**: 
```yaml
attractor_type: self_excited
```
- **Equilibrios reportados por el libro**: `O(0,0,0), E+(sqrt(105), sqrt(105), 35), E-( -sqrt(105), -sqrt(105), 35)`
- **Equilibrios calculados por el código**:
  - **E1**: `(0.0000, 0.0000, 0.0000)`
    - *Autovalores*: `[21.6312, -3.0000, -56.6312]`
    - *Clasificación*: `saddle`
  - **E2**: `(10.2470, 10.2470, 35.0000)`
    - *Autovalores*: `[-0.1939 + 13.9778i, -0.1939 + -13.9778i, -37.6122]`
    - *Clasificación*: `stable_focus`
  - **E3**: `(-10.2470, -10.2470, 35.0000)`
    - *Autovalores*: `[-0.1939 + 13.9778i, -0.1939 + -13.9778i, -37.6122]`
    - *Clasificación*: `stable_focus`

---

## Yang-Wei system (`yang_wei`)
- **Capítulo**: 3 | **Tipo**: con equilibrio estable
- **Referencia**: Yang, Q., Wei, Z., Chen, G. (2010). An unusual 3D autonomous quadratic chaotic system with two stable node-foci. International Journal of Bifurcation and Chaos.
- **Ecuaciones (LaTeX)**: $$\dot{x}=a(y-x), \; \dot{y}=-cy-xz, \; \dot{z}=-b+xy$$
- **Parámetros**: `{'a': 10.0, 'b': 100.0, 'c': 11.2}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
```
- **Equilibrios reportados por el libro**: `E1(10, 10, -11.2), E2(-10, -10, -11.2)`
- **Equilibrios calculados por el código**:
  - **E1**: `(10.0000, 10.0000, -11.2000)`
    - *Autovalores*: `[-0.1111 + 9.7635i, -0.1111 + -9.7635i, -20.9778]`
    - *Clasificación*: `stable_focus`
  - **E2**: `(-10.0000, -10.0000, -11.2000)`
    - *Autovalores*: `[-0.1111 + 9.7635i, -0.1111 + -9.7635i, -20.9778]`
    - *Clasificación*: `stable_focus`

---

## Sprott A no-equilibrium system (`sprott_a_no_equilibrium`)
- **Capítulo**: 4 | **Tipo**: sin equilibrio
- **Referencia**: Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y, \; \dot{y}=-x+yz, \; \dot{z}=1-y^2$$
- **Parámetros**: `{}`
- **Dinámica reportada**: 
```yaml
attractor_type: conservative_chaotic_sea
lyapunov_exponents: [0.0139, 0.0, -0.0139]
kaplan_yorke_dimension: 3.0
```
- **Equilibrios reportados por el libro**: `Ninguno`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---

## Wei no-equilibrium system (`wei_no_equilibrium`)
- **Capítulo**: 4 | **Tipo**: sin equilibrio
- **Referencia**: Wei, Z. (2011). Dynamical behaviors of a chaotic system with no equilibria. Physics Letters A.
- **Ecuaciones (LaTeX)**: $$\dot{x}=-y, \; \dot{y}=cx+z, \; \dot{z}=ay^2+xz-d$$
- **Parámetros**: `{'a': 2.0, 'b': 1.0, 'c': 0.35}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
lyapunov_exponents: [0.0793, 0.0, -1.5034]
kaplan_yorke_dimension: 2.0528
```
- **Equilibrios reportados por el libro**: `Ninguno para d > 0`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---

## Wang-Chen no-equilibrium system (`wang_chen_no_equilibrium`)
- **Capítulo**: 4 | **Tipo**: sin equilibrio
- **Referencia**: Wang, X., Chen, G. (2013). Constructing a chaotic system with any number of equilibria. Nonlinear Dynamics.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y, \; \dot{y}=z, \; \dot{z}=-y+3y^2-x^2-xz+a$$
- **Parámetros**: `{'a': -0.05}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
```
- **Equilibrios reportados por el libro**: `Ninguno para a < 0`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---

## Maaita cubic no-equilibrium system (`maaita`)
- **Capítulo**: 4 | **Tipo**: sin equilibrio
- **Referencia**: Maaita, J., Volos, C. K., Kyprianidis, I., Stouboulos, I. (2015). The dynamics of a cubic nonlinear system with no equilibrium point. Nonlinear Dynamics.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y, \; \dot{y}=-x^3-zy, \; \dot{z}=y^2-a$$
- **Parámetros**: `{'a': 5.16}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
```
- **Equilibrios reportados por el libro**: `Ninguno para a > 0`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---

## Akgul no-equilibrium system (`akgul`)
- **Capítulo**: 4 | **Tipo**: sin equilibrio
- **Referencia**: Akgul, A., et al. (2016). Chaos-based engineering applications with a 3D chaotic system without equilibrium points. Nonlinear Dynamics.
- **Ecuaciones (LaTeX)**: $$\dot{x}=ay-x+zy, \; \dot{y}=-bxz-cx+zy+d, \; \dot{z}=e-fxy-x^2$$
- **Parámetros**: `{'a': 2.8, 'b': 0.2, 'c': 1.4, 'd': 1.0, 'e': 10.0, 'f': 2.0}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
```
- **Equilibrios reportados por el libro**: `Complejos solamente`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---

## Pham modified Jafari LE5 system (`pham_modified_le5`)
- **Capítulo**: 4 | **Tipo**: sin equilibrio
- **Referencia**: Pham, V.-T., Volos, C., Kapitaniak, T. (2017). Systems with stable equilibria. Springer.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y, \; \dot{y}=-1.5x+zy, \; \dot{z}=-x^2+y^2-5xy+a$$
- **Parámetros**: `{'a': 0.001}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
```
- **Equilibrios reportados por el libro**: `Ninguno para a != 0`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---

## Pham modified Jafari LE6 system (`pham_modified_le6`)
- **Capítulo**: 4 | **Tipo**: sin equilibrio
- **Referencia**: Pham, V.-T., Volos, C., Kapitaniak, T. (2017). Systems with stable equilibria. Springer.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y, \; \dot{y}=-x+zy, \; \dot{z}=0.04y^2-xy-0.1xz+a$$
- **Parámetros**: `{'a': 0.001}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
```
- **Equilibrios reportados por el libro**: `Ninguno para a != 0`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---

## Pham special hidden-attractor system (`pham_special_hidden`)
- **Capítulo**: 4 | **Tipo**: sin equilibrio
- **Referencia**: Pham, V.-T., et al. (2017). A novel hidden chaotic system.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y, \; \dot{y}=0.4xz-a, \; \dot{z}=0.3y-0.1z-1.4y^2-bxy-c$$
- **Parámetros**: `{'a': 0.005, 'b': 0.2, 'c': 0.0}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
```
- **Equilibrios reportados por el libro**: `Ninguno para a != 0 y c = 0`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---

## Pham-Akgul no-equilibrium system with boostable variable (`pham_akgul_boostable`)
- **Capítulo**: 4 | **Tipo**: sin equilibrio
- **Referencia**: Pham, V.-T., Akgul, A., Volos, C., Jafari, S., Kapitaniak, T. (2017). Dynamics and circuit realization of a no-equilibrium chaotic system. AEU.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y+a, \; \dot{y}=-x+z, \; \dot{z}=-bx^2+z^2+c$$
- **Parámetros**: `{'a': 1.0, 'b': 0.8, 'c': 2.0}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
lyapunov_exponents: [0.026, 0.0, -6.8624]
kaplan_yorke_dimension: 2.0038
```
- **Equilibrios reportados por el libro**: `Ninguno real para b < 1`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---

## Jafari multiscroll chaotic sea without equilibrium (`jafari_multiscroll_no_equilibrium`)
- **Capítulo**: 4 | **Tipo**: sin equilibrio
- **Referencia**: Jafari, S., Pham, V.-T., Kapitaniak, T. (2016). Multiscroll chaotic sea obtained from a simple 3D system. IJBC.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y, \; \dot{y}=-x+ayz+by\sin(z), \; \dot{z}=1-y^2$$
- **Parámetros**: `{'a': 0.1, 'b': 2.9}`
- **Dinámica reportada**: 
```yaml
attractor_type: conservative_chaotic_sea
```
- **Equilibrios reportados por el libro**: `Ninguno`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---

## Hu System I, sine improved Sprott A (`hu_multiscroll_i`)
- **Capítulo**: 4 | **Tipo**: sin equilibrio
- **Referencia**: Hu, X., Liu, C., Liu, L., Ni, J., Li, S. (2016). Multi-scroll hidden attractors in improved Sprott A system. Nonlinear Dynamics.
- **Ecuaciones (LaTeX)**: $$\dot{x}=y, \; \dot{y}=-x+yz-a\sin(2\pi bx), \; \dot{z}=1-y^2$$
- **Parámetros**: `{'a': 25.0, 'b': 1.0}`
- **Dinámica reportada**: 
```yaml
attractor_type: hidden_candidate
```
- **Equilibrios reportados por el libro**: `Ninguno`
- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).

---


# 05 - Diagnóstico y Clasificación Computacional

Para filtrar dinámicas triviales en búsquedas automatizadas, Chaos Toolbox implementa filtros rápidos aplicados a la trayectoria post-transitorio:

## Criterios de Clasificación

1. **Divergente (`divergent`):** La simulación se detiene e identifica como divergente si alguna coordenada del estado es infinita (`NaN` o `Inf`) o si la norma del estado $\|x_n\|$ supera el límite tolerable (por defecto $R_{\max} = 10^6$).
2. **Punto Fijo (`fixed_point`):** Se detecta si la cola de la trayectoria colapsa a un único punto estacionario.
3. **Baja Complejidad / Periódico (`periodic_or_low_complexity`):** Ocurre si la trayectoria muestra muy baja dispersión numérica o si redondeando los valores de su cola de estados, se revela un ciclo repetitivo de periodo corto (ciclos de límite de periodo 2, 3, etc.).
4. **Candidato Caótico (`candidate_chaotic`):** Se aplica a órbitas que permanecen acotadas, finitas, y no colapsan ni a puntos fijos ni a ciclos cortos evidentes.

## El Exponente de Lyapunov Rápido

La toolbox utiliza la métrica `quick_lyapunov_estimate` para dar una indicación preliminar de caos. Calcula la tasa de separación de dos trayectorias vecinas separadas a una distancia infinitesimal inicial $d_0$, aplicando un paso de integración y midiendo la distancia resultante $d_1$.

> [!WARNING]
> La estimación rápida de Lyapunov es una herramienta heurística de cribado. Un exponente rápido positivo no constituye una demostración formal de caos matemático. Para confirmar caos, se requiere un análisis dinámico exhaustivo que involucre el cálculo del espectro completo de Lyapunov mediante renormalización de Gram-Schmidt, análisis de sensibilidad a condiciones iniciales con pasos finos, y secciones de Poincaré.

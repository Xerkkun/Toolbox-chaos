# 07 - Atractores Ocultos y Multistabilidad

La teoría moderna de sistemas dinámicos establece una distinción fundamental sobre cómo se localizan los atractores en el espacio de fases:

## Clasificación de Atractores

- **Atractor Autoexcitado:** Su cuenca de atracción intersecta una vecindad pequeña de algún punto de equilibrio inestable del sistema. Computacionalmente, estos atractores son fáciles de hallar: basta con inicializar trayectorias cerca de los equilibrios inestables.
- **Atractor Oculto:** Su cuenca de atracción no intersecta vecindades de los equilibrios. Es decir, para toda vecindad pequeña $U_\varepsilon(E_i)$ alrededor de cualquier equilibrio $E_i$, se cumple:
  $$\mathcal{B}(A) \cap U_\varepsilon(E_i) = \varnothing$$
  Donde $\mathcal{B}(A)$ es la cuenca del atractor $A$.

## Casos Dinámicos Críticos

1. **Sistemas sin Equilibrios:** Al no existir puntos de equilibrio, el método estándar de iniciación en equilibrio inestable falla por definición. Todos los atractores caóticos en estos sistemas son, por tanto, atractores ocultos.
2. **Sistemas con un único Equilibrio Estable:** Si el único punto de equilibrio es un sumidero estable, cualquier trayectoria inicializada cerca de él colapsará al punto fijo. Para hallar un atractor caótico coexistente (multistabilidad), es necesario buscar condiciones iniciales alejadas del equilibrio.
3. **Variedades de Equilibrio:** Sistemas que presentan líneas, curvas o superficies completas de puntos de equilibrio.

## Búsqueda de Atractores Ocultos

La detección de atractores ocultos y el análisis de **multistabilidad** (coexistencia de varios atractores estables para los mismos parámetros) requiere realizar barridos globales de condiciones iniciales en malla, análisis de cuencas de atracción, o búsquedas heurísticas. Una sola simulación iniciada desde una condición estándar no es suficiente para clasificar un atractor como oculto.

# 06 - Lenguaje Visual y Representación

La visualización de atractores extraños es una lectura selectiva del espacio de fases. Cuando un sistema dinámico tiene dimensión $D > 2$, se deben proyectar y colorear los datos para poder interpretarlos visualmente.

## Elementos del Lenguaje Visual

1. **Proyecciones Bidimensionales:** Las proyecciones más comunes son los planos coordenados $(x, y)$, $(x, z)$ y $(y, z)$.
2. **Variable de Color:** Se puede colorear cada punto según variables adicionales del estado (como $z$ o $w$), la distancia radial al origen, el tiempo transcurrido en la simulación, o la densidad local de puntos.
3. **Fondo e Iluminación:** Los fondos negros proporcionan un contraste vibrante y acentúan paletas incandescentes (como `turbo` o `plasma`), mientras que los fondos claros son óptimos para impresión.
4. **Opacidad (Alpha) y Tamaño de Punto:** Para atractores densos con decenas de miles de puntos, se recomienda usar un tamaño de punto pequeño ($0.1$ a $0.3$) y una opacidad baja ($\alpha = 0.2$ a $0.4$). Esto revela la estructura tridimensional y las densidades del atractor.
5. **Representación 4D:** Para sistemas de cuatro dimensiones, se elige un par de coordenadas para la proyección plana. El selector de color utiliza una sola variable, que puede ser $z$ o $w$; el preajuste `Mapa 4D` usa $w$. Si se activan bandas, estas cuantizan esa misma variable de color. No se aplican simultáneamente $z$ al color y $w$ al brillo o al grosor.
6. **Esfera unitaria:** Para estados con al menos tres componentes y $(x,y,z)\neq(0,0,0)$, la proyección radial usa
   $$\widehat{\mathbf{x}}=\frac{(x,y,z)}{\sqrt{x^2+y^2+z^2}}.$$
   El color se calcula con el estado original antes de normalizar; por ejemplo, `radio` conserva la amplitud descartada por la geometría esférica. Los estados nulos se omiten porque su dirección no está definida. Esta vista compara direcciones y pierde deliberadamente la amplitud, por lo que no demuestra caos, atracción ni ocultamiento.

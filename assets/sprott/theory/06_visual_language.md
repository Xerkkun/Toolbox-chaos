# 06 - Lenguaje Visual y Representación

La visualización de atractores extraños es una lectura selectiva del espacio de fases. Cuando un sistema dinámico tiene dimensión $D > 2$, se deben proyectar y colorear los datos para poder interpretarlos visualmente.

## Elementos del Lenguaje Visual

1. **Proyecciones Bidimensionales:** Las proyecciones más comunes son los planos coordenados $(x, y)$, $(x, z)$ y $(y, z)$.
2. **Variable de Color:** Se puede colorear cada punto según variables adicionales del estado (como $z$ o $w$), la distancia radial al origen, el tiempo transcurrido en la simulación, o la densidad local de puntos.
3. **Fondo e Iluminación:** Los fondos negros proporcionan un contraste vibrante y acentúan paletas incandescentes (como `turbo` o `plasma`), mientras que los fondos claros son óptimos para impresión.
4. **Opacidad (Alpha) y Tamaño de Punto:** Para atractores densos con decenas de miles de puntos, se recomienda usar un tamaño de punto pequeño ($0.1$ a $0.3$) y una opacidad baja ($\alpha = 0.2$ a $0.4$). Esto revela la estructura tridimensional y las densidades del atractor.
5. **Representación 4D:** Para sistemas de cuatro dimensiones, se proyectan las coordenadas $(x, y)$ en el lienzo plano, se mapea la coordenada $z$ a la paleta de colores del trazo, y se mapea la coordenada $w$ para modular el brillo o el grosor de las bandas.

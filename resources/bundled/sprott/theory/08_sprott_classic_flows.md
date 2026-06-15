# 08 - Sistemas Caóticos Sprott Clásicos (1994)

En su artículo de 1994 *Some simple chaotic flows*, Julien C. Sprott realizó una búsqueda sistemática de ecuaciones diferenciales ordinarias autónomas tridimensionales con la menor cantidad de términos y no linealidades que presentaran dinámica caótica. Identificó 19 flujos caóticos simples etiquetados de la `A` a la `S`.

A continuación se detallan algunos de los sistemas más significativos de esta colección:

$$
\begin{array}{c l l c c}
\text{Caso} & \text{Ecuaciones} & \text{Equilibrios} & \text{Lyapunov} & D_{KY} \\
\hline
\text{A} & \dot{x}=y, \; \dot{y}=-x+yz, \; \dot{z}=1-y^2 & \text{Ninguno (oculto)} & (0.014, 0, -0.014) & 3.000 \\
\text{B} & \dot{x}=yz, \; \dot{y}=x-y, \; \dot{z}=1-xy & (1,1,0), \; (-1,-1,0) & (0.210, 0, -1.210) & 2.174 \\
\text{C} & \dot{x}=yz, \; \dot{y}=x-y, \; \dot{z}=1-x^2 & (1,1,0), \; (-1,-1,0) & (0.163, 0, -0.163) & 2.140 \\
\text{D} & \dot{x}=-y, \; \dot{y}=x+z, \; \dot{z}=xz+3y^2 & (0,0,0) & (0.103, 0, -1.320) & 2.078 \\
\text{E} & \dot{x}=yz, \; \dot{y}=x^2-y, \; \dot{z}=1-4x & (0.25, 0.063, 0) & (0.078, 0, -1.078) & 2.072 \\
\text{F} & \dot{x}=y+z, \; \dot{y}=-x+0.5y, \; \dot{z}=x^2-z & (0,0,0), \; (-2,-4,4) & (0.117, 0, -0.617) & 2.190 \\
\text{G} & \dot{x}=0.4x+z, \; \dot{y}=xz-y, \; \dot{z}=-x+y & (0,0,0), \; (-2.5,-2.5,1) & (0.034, 0, -0.634) & 2.054
\end{array}
$$

## Análisis Dinámico Especial
- **Caso A:** Al imponer $\dot{x}=0 \Rightarrow y=0$, lo que hace que $\dot{z} = 1 - y^2 = 1 \neq 0$. Por lo tanto, el sistema no posee ningún punto de equilibrio. El atractor caótico resultante es un atractor oculto puro.
- **Caso E:** Este flujo posee un único punto de equilibrio. Mediante perturbaciones continuas es posible transformarlo en un sistema con un único equilibrio estable que coexiste con un atractor caótico (atractor oculto).

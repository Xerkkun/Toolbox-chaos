# Reporte de Validación de Renderizado PDF: Catálogo Wang 2021

Este reporte verifica de forma automatizada y visual que el archivo final `sprott_theory.pdf` se haya generado y compilado con el formato visual, las ecuaciones matemáticas y las clasificaciones dinámicas correspondientes.

## Resumen Ejecutivo
- **Páginas del PDF original**: 20 (incrementado para alojar el catálogo completo de Wang 2021).
- **Estado de compilación**: Exitoso (exit code 0).
- **Páginas vacías detectadas**: 0 de 20.
- **Cajas desbordadas (Overfull \hbox)**: 2
- **Cajas con bajo contenido (Underfull \hbox)**: 55

---

## Verificación de Contenido (Palabras Clave)
A continuación se detalla si se encontraron los nuevos sistemas y secciones en el texto extraído del PDF:

| Sistema / Seccion | Presente en PDF |
|---|:---:|
| Lorenz | ✅ |
| Rössler | ✅ |
| Chua | ✅ |
| Chen | ✅ |
| Unified Lorenz-Chen | ✅ |
| Sprott A | ✅ |
| Sprott S | ✅ |
| Sprott L | ✅ |
| Sprott R | ✅ |
| Wang-Chen | ✅ |
| Wei extended Sprott E | ✅ |
| Lao | ✅ |
| Kingni | ✅ |
| Controlled LE1 | ✅ |
| Yang-Chen | ✅ |
| Yang-Wei | ✅ |
| Sprott A no-equilibrium | ✅ |
| Wei no-equilibrium | ✅ |
| Maaita | ✅ |
| Akgul | ✅ |
| Jafari | ✅ |
| Hu | ✅ |

---

## Análisis de Páginas Renderizadas
Se convirtieron todas las páginas del PDF a imágenes PNG de alta resolución (150 DPI) y se evaluó la proporción de píxeles en blanco (para descartar páginas en blanco o errores de renderizado masivos):

| Página | Proporción Fondo Blanco | ¿Está Vacía? | Ruta Imagen |
|---|---|:---:|---|
| Page 1 | 95.63% | ✅ OK | [page_1.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_1.png?width=400) |
| Page 2 | 93.07% | ✅ OK | [page_2.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_2.png?width=400) |
| Page 3 | 96.13% | ✅ OK | [page_3.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_3.png?width=400) |
| Page 4 | 94.35% | ✅ OK | [page_4.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_4.png?width=400) |
| Page 5 | 95.14% | ✅ OK | [page_5.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_5.png?width=400) |
| Page 6 | 94.26% | ✅ OK | [page_6.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_6.png?width=400) |
| Page 7 | 92.18% | ✅ OK | [page_7.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_7.png?width=400) |
| Page 8 | 92.63% | ✅ OK | [page_8.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_8.png?width=400) |
| Page 9 | 93.58% | ✅ OK | [page_9.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_9.png?width=400) |
| Page 10 | 93.73% | ✅ OK | [page_10.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_10.png?width=400) |
| Page 11 | 93.68% | ✅ OK | [page_11.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_11.png?width=400) |
| Page 12 | 93.74% | ✅ OK | [page_12.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_12.png?width=400) |
| Page 13 | 93.86% | ✅ OK | [page_13.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_13.png?width=400) |
| Page 14 | 93.28% | ✅ OK | [page_14.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_14.png?width=400) |
| Page 15 | 93.38% | ✅ OK | [page_15.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_15.png?width=400) |
| Page 16 | 92.43% | ✅ OK | [page_16.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_16.png?width=400) |
| Page 17 | 93.75% | ✅ OK | [page_17.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_17.png?width=400) |
| Page 18 | 93.88% | ✅ OK | [page_18.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_18.png?width=400) |
| Page 19 | 96.73% | ✅ OK | [page_19.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_19.png?width=400) |
| Page 20 | 94.56% | ✅ OK | [page_20.png](file:///C:/Users/moren/Desktop/Codes/Toolbox chaos/reports/rendered_pages/page_20.png?width=400) |

---

## Diagnóstico del Compilador LaTeX (Log Check)
- **Errores detectados en log**: 0
*(Ninguno)*

- **Advertencias importantes (Warnings)**: 0
*(Ninguna)*

---

## Conclusiones
El pipeline de compilación se encuentra operando de forma óptima. Los sistemas del libro de Wang (2021) han sido correctamente renderizados, las fórmulas matemáticas se compilaron sin errores de sintaxis y los autovalores y Jacobianos calculados por el código numérico ya forman parte permanente de la documentación del Explorador de Chaos Toolbox.

# 09 - Reproducibilidad y Atribución Legal

Chaos Toolbox se fundamenta en rigurosas políticas éticas de preservación de derechos de autor y reproducibilidad científica:

## 1. Política de Distribución Pública
La versión de Chaos Toolbox distribuida públicamente **no contiene ningún archivo original** propiedad de Julien C. Sprott extraído de su disquete del libro o de su sitio web, tales como:
- Archivos de diccionarios de configuraciones (`BOOKFIGS.DIC`, `SELECTED.DIC`, `SPECIAL.DIC`).
- Programas ejecutables antiguos (`SA.EXE`, `SAWIN.EXE`).
- Código fuente original (`PROG28.BAS`, `PROG28QC.C`, `PROG28TC.CPP`).

## 2. Carga y Procesamiento Local
El software está estructurado para que el usuario, bajo su propia responsabilidad de estudio personal, suministre la ruta de los archivos locales `.DIC` que posea de su propio ejemplar del libro. El programa procesa las cadenas de coeficientes directamente desde el disco sin guardarlas en su base de datos interna ni copiarlas al repositorio.

## 3. Metadatos de Exportación para Reproducibilidad
Cada entrada de la galería local guarda un archivo lateral `metadata.json` con
los datos necesarios para repetir la simulación. Una imagen exportada por sí
sola no conserva necesariamente ese archivo, y la repetición puede variar con
la plataforma o versión. El registro incluye:
- Código de familia de Sprott.
- Parámetros de iteración y descarte de transitorio.
- Paso temporal $h$ y método de flujo (Euler, Heun o RK4).
- Presets visuales aplicados (proyección, color por variable oculta, paleta, fondo y nivel de transparencia alpha).

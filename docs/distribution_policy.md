# Política de Distribución Pública y Archivos Locales

Este documento detalla las reglas de distribución de **Chaos Toolbox** y explica la separación entre el contenido distribuido públicamente y el material de estudio personal de Julien C. Sprott.

## 1. Qué se incluye en la Release Pública

La versión pública oficial de Chaos Toolbox (incluyendo el código fuente en GitHub, los archivos ejecutables construidos con PyInstaller y el instalador generado con Inno Setup) contiene exclusivamente:
- **Código Fuente Propio:** Toda la lógica de la interfaz gráfica en PyQt6 y el cargador de configuraciones.
- **Backend Numérico Propio:** Los archivos de simulación en C y la interfaz de biblioteca nativa (`chaos_core`).
- **Ejemplos Sintéticos Propios:** Una colección de ecuaciones caóticas de dominio público y ejemplos de prueba diseñados específicamente para validar el funcionamiento del programa de forma autónoma.
- **Teoría Propia y Guías de Uso:** Explicaciones educativas originales, manuales de uso técnico de la herramienta, y referencias bibliográficas formateadas.

## 2. Qué NO se incluye en la Release Pública

Por razones de derechos de autor y políticas de distribución respetuosas, **no se incluye ni se redistribuye** ningún material original extraído del disquete histórico o del sitio oficial de Julien C. Sprott, incluyendo:
- Diccionarios de datos originales: `BOOKFIGS.DIC`, `SELECTED.DIC`, `SPECIAL.DIC`.
- Archivos ejecutables históricos: `SA.EXE`, `SAWIN.EXE`.
- Código fuente original de Sprott: `PROG28.BAS`, `PROG28QC.C`, `PROG28TC.CPP`.
- Archivos de soporte y DLLs históricas: `SADISK.ZIP`, `VBRUN200.DLL`.
- Imágenes o páginas HTML extraídas directamente del sitio web de Sprott.

Estos archivos **no están empaquetados ni comprimidos** dentro del ejecutable final, ni se distribuyen como assets en el repositorio.

## 3. Uso de Archivos Locales para Estudio Personal

La herramienta permite y fomenta el uso de los archivos originales del libro de Sprott para fines estrictamente educativos y de estudio personal en tu computadora local:
- **Lectura en tiempo de ejecución:** El programa lee los archivos `.DIC` directamente desde la ruta de tu disco local que configures en la interfaz (por defecto busca en `external/`).
- **Sin copia ni persistencia:** Los archivos leídos permanecen en tu disco local y en ningún momento se copian dentro del programa ni se suben al repositorio.
- **Resultados locales:** Las imágenes generadas a partir de estos códigos se guardan en tu galería de usuario local (en la carpeta `APPDATA`) con metadatos claros de atribución y aclaración de que son recreaciones locales, no imágenes originales redistribuidas.

## 4. Backend Numérico en C y Autorización

Chaos Toolbox utiliza un backend numérico de simulación rápido desarrollado en C (`core/csrc/chaos_core.c`). Este backend es una reimplementación independiente y optimizada de los métodos de integración numérica. 

Dado que el backend de simulación es de autoría propia y fue desarrollado de forma independiente para sistemas modernos de 64 bits, **no cuenta con autorización ni tiene como fin** redistribuir los códigos, algoritmos o archivos de datos con copyright del disquete original del libro de Sprott. Por lo tanto, cualquier intento de distribución de los datos originales requiere una licencia y permiso específico del autor original.

## 5. Cómo solicitar permiso para Distribuciones Históricas

Si eres una institución educativa, investigador o entusiasta y deseas crear una distribución empaquetada con fines de preservación histórica o de uso offline que incluya los diccionarios originales de Sprott:
1. Debes contactar directamente al **Prof. Julien C. Sprott** (a través de los medios oficiales listados en su sitio web de la Universidad de Wisconsin-Madison) para solicitar una autorización o verificar los términos de distribución de su obra *Strange Attractors: Creating Patterns in Chaos*.
2. Una vez obtenido dicho consentimiento, puedes colocar los archivos `.DIC` y otros recursos en la carpeta `external/sprott_site_bookdisk/...` en tu copia local antes de realizar el build.
3. El script de verificación de liberación (`tools/check_no_sprott_originals_in_release.py`) fallará intencionadamente si intentas compilar la versión oficial. Para realizar un build personalizado histórico con archivos embebidos, deberás modificar el archivo `.spec` y desactivar localmente la comprobación de seguridad bajo tu propia responsabilidad.

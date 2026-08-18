# Política de Distribución Pública y Archivos Locales

Este documento detalla las reglas de distribución de **Chaos Toolbox** y explica la separación entre el contenido distribuido públicamente y el material de estudio personal de Julien C. Sprott.

## 1. Qué se incluye en la Release Pública

La versión pública oficial de Chaos Toolbox (incluyendo el código fuente en GitHub, los archivos ejecutables construidos con PyInstaller y el instalador generado con Inno Setup) contiene exclusivamente:
- **Código Fuente Propio:** Toda la lógica de la interfaz gráfica en PySide6 y el cargador de configuraciones.
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

## 4. Licencias del programa y de sus dependencias

El código propio de Chaos Toolbox se distribuye bajo MIT. Esa licencia no
relicencia PySide6, Shiboken6, Qt, Python ni las bibliotecas científicas que se
empaquetan con la aplicación. Las compilaciones comunitarias oficiales usan
la vía LGPLv3 para los componentes Qt/PySide que la ofrecen.

Cada wheel, sdist, bundle PyInstaller e instalador debe conservar
`THIRD_PARTY_NOTICES.md`, LGPLv3/GPLv3, los avisos Chromium/WebEngine y los
metadatos de licencia de las dependencias incluidas. Los bundles nativos
incluyen además la licencia exacta del runtime Python. La publicación conserva
un SBOM del entorno Python y otro con hashes de cada archivo del bundle de cada
plataforma; rechaza deriva de versiones o cualquier resto de la vinculación
Qt anterior. El responsable de una release binaria conserva el código fuente
correspondiente a la versión exacta de Qt/PySide distribuida o una oferta
escrita válida bajo su control. Esta es una política técnica de distribución,
no un dictamen legal.

## 5. Backend Numérico en C y Autorización

Chaos Toolbox utiliza un backend numérico compilado desarrollado en C
(`core/csrc/chaos_core.c`). Es una implementación independiente de los métodos
de integración documentados; este texto no atribuye una ventaja de rendimiento
sin una medición reproducible para el equipo y caso concretos.

Dado que el backend de simulación es de autoría propia y fue desarrollado de forma independiente para sistemas modernos de 64 bits, **no cuenta con autorización ni tiene como fin** redistribuir los códigos, algoritmos o archivos de datos con copyright del disquete original del libro de Sprott. Por lo tanto, cualquier intento de distribución de los datos originales requiere una licencia y permiso específico del autor original.

## 6. Material histórico con permiso separado

Una institución que quiera preservar o redistribuir material histórico debe
obtener y documentar por separado los permisos aplicables con el titular de
los derechos. Esos archivos se mantienen fuera del repositorio, del árbol de
recursos y del proceso oficial de release de Chaos Toolbox. Incluso con un
permiso particular, los verificadores de la distribución oficial no se
desactivan ni se modifica el archivo `.spec` para incluir ese material; una
colección de preservación autorizada constituye un archivo separado.

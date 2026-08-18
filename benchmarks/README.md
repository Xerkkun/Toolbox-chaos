# Protocolo multiplataforma de compilación y rendimiento

Este directorio contiene un flujo por computadora que:

1. prepara un entorno Python aislado;
2. compila el backend numérico C y la aplicación nativa;
3. crea el paquete instalable de la plataforma;
4. mide el arranque y las cargas numéricas fijas;
5. guarda observaciones crudas, resumen y procedencia en JSON.

Los scripts de macOS y Pop!_OS deben ejecutarse en esos sistemas. Prepararlos o
revisar su sintaxis desde Windows no constituye una prueba de compatibilidad.

## Contrato de medición

- El arranque se mide externamente, desde la creación del proceso empaquetado
  hasta el primer pintado de la ventana principal. Se realiza un arranque de
  calentamiento no medido y después 10 repeticiones en caliente.
- Cada cálculo se ejecuta en un proceso Python independiente desde el mismo
  árbol fuente con el que se construyó el paquete. Hay un calentamiento no
  medido y 5 repeticiones medidas.
- Se fijan un trabajador y un hilo para evitar que una computadora reciba más
  trabajo paralelo que otra.
- Las cargas son: trayectoria de 100 000 muestras, FFT de 100 000 muestras,
  espectro de Lyapunov, bifurcación y cuencas de 60 x 60 y 200 x 200.
- Cada manifiesto registra versión del software, versiones de dependencias,
  inventario de hardware no identificador, consumo de memoria, hashes del
  código numérico, perfil de energía, compilador/flags y hash/tamaño del
  paquete. No se registra un commit.
- Antes de medir, el ejecutable congelado realiza una trayectoria Lorenz corta
  y comprueba finitud y dimensiones. Esta autoprueba obliga a cargar la
  biblioteca C incluida en el bundle.

El arranque caracteriza el artefacto empaquetado; los tiempos numéricos
caracterizan el backend del mismo árbol fuente. El JSON declara explícitamente
esta frontera y no mezcla ambos tipos de evidencia.

Los lanzadores también rechazan una arquitectura Python incompatible con el
host (por ejemplo, Python Intel bajo Rosetta en una Mac Apple Silicon o Python
de 32 bits en Windows x64).

## Preparación común

Copie la misma versión de `Toolbox chaos` y este directorio de protocolo en cada
equipo. Conecte el equipo a la corriente, mantenga fijo el modo de energía,
cierre aplicaciones pesadas y no use la computadora durante el lote.

Los scripts descubren el repositorio si existe una carpeta ascendente que
contenga `Toolbox chaos`. En cualquier otra disposición, indique su ruta.

## Windows: ThinkPad actual

Comprobación sin compilar ni medir:

```powershell
.\run_windows_thinkpad_t14s_gen3.ps1 `
  -ToolboxRoot 'C:\ruta\Toolbox chaos' `
  -CheckOnly
```

Compilación del ejecutable y del instalador Inno Setup, seguida de las pruebas:

```powershell
.\run_windows_thinkpad_t14s_gen3.ps1 `
  -ToolboxRoot 'C:\ruta\Toolbox chaos'
```

Requiere Python 3.11 o posterior, GCC/Clang e Inno Setup 6. El resultado incluye
`Chaos Toolbox.exe` y
`installer\chaos-toolbox-v<version>-windows-x64-setup.exe`. Solo use
`-AllowAppOnly` si desea aceptar explícitamente que no se cree el instalador.

El nombre editorial confirmado por la autora es `ThinkPad T14s Gen 3`.
Windows informa además el código `21CF003TUS` y la cadena de familia
`ThinkPad T14 Gen 3`; ambos se conservan como valores crudos de procedencia.

## Windows: ASUS TUF

En la ASUS ejecute:

```powershell
.\run_windows_asus_tuf.ps1 `
  -ToolboxRoot 'C:\ruta\Toolbox chaos' `
  -CheckOnly

.\run_windows_asus_tuf.ps1 `
  -ToolboxRoot 'C:\ruta\Toolbox chaos'
```

El perfil base no inventa modelo, CPU ni memoria. El manifiesto de la ejecución
nativa los obtiene mediante CIM. El lanzador rechaza una computadora que no
sea ASUS TUF para evitar resultados mal etiquetados.

## macOS: equipo de 16 GiB

Instale Python 3 y las herramientas de línea de comandos de Xcode. Desde una
terminal gráfica:

```bash
bash ./run_macos_16gb.sh \
  --toolbox-root "/ruta/Toolbox chaos" \
  --check-only

bash ./run_macos_16gb.sh \
  --toolbox-root "/ruta/Toolbox chaos"
```

Se construyen `dist/Chaos Toolbox.app` y
`dist/chaos-toolbox-v<version>-macos.dmg`. La aplicación recibe una firma
ad hoc para la prueba local. El DMG no tiene firma Developer ID ni notarización
de Apple; esas credenciales son necesarias antes de distribuirlo públicamente.

## Pop!_OS: ThinkPad T14 Gen 2

Ejecute desde la sesión gráfica normal:

```bash
bash ./run_popos_thinkpad_t14_gen2.sh \
  --toolbox-root "/ruta/Toolbox chaos" \
  --check-only

bash ./run_popos_thinkpad_t14_gen2.sh \
  --toolbox-root "/ruta/Toolbox chaos"
```

El flujo instala, con confirmación de `sudo` cuando sea necesaria, las
dependencias de compilación de Pop!_OS; construye el directorio PyInstaller y el
paquete `dist/chaos-toolbox_<version>_<arquitectura>.deb`. No afirma producir
un AppImage.

## Alcance del instalador

Los scripts construyen y verifican la estructura del `.exe`, `.dmg` o `.deb`;
además ejecutan un cálculo corto desde el binario situado en `dist`. Por tanto,
el JSON registra que esa autoprueba finita del bundle terminó y registra el
instalador generado; no sustituye una prueba de instalación y desinstalación en
el sistema.

Antes de distribuir, instale manualmente cada paquete, abra la aplicación
instalada y ejecute al menos una trayectoria y una cuenca. Para comprobaciones
estructurales adicionales:

```bash
# macOS
hdiutil verify "/ruta/Toolbox chaos/dist/chaos-toolbox-v0.1.0-macos.dmg"

# Pop!_OS
dpkg-deb --info "/ruta/Toolbox chaos/dist/chaos-toolbox_0.1.0_amd64.deb"
dpkg-deb --contents "/ruta/Toolbox chaos/dist/chaos-toolbox_0.1.0_amd64.deb"
```

## Resultados

Por omisión, cada ejecución crea una de estas rutas, según la copia usada:

```text
supplementary/benchmark_results/<perfil>/<fecha-UTC>/
benchmarks/results/<perfil>/<fecha-UTC>/
```

El archivo principal es `benchmark_result.json`. También se conservan:

- `run_manifest.json`;
- `startup_raw.json` y `startup_raw.csv`;
- `calculations_raw.json` y `calculations_raw.csv`;
- `summary.json` y `summary.csv`.

El resultado de una plataforma solo se acepta si el script termina sin error,
existen los cinco JSON requeridos y `benchmark_result.json` tiene
`"status": "ok"`. `benchmark_result.schema.json` describe el resultado completo
aceptable; el combinador comprueba además los conteos exactos por caso.

## Combinar las cuatro computadoras

Cuando existan los cuatro resultados:

```bash
python merge_benchmark_results.py \
  /ruta/thinkpad/benchmark_result.json \
  /ruta/asus/benchmark_result.json \
  /ruta/macos/benchmark_result.json \
  /ruta/popos/benchmark_result.json \
  --output benchmark_comparison.json
```

El combinador no altera los resultados. Incluye la huella SHA-256 de cada
archivo y advierte si cambió el contrato de pruebas o el código fuente entre
computadoras. Por omisión rechaza resultados parciales, identidades no
verificadas y cualquier diferencia de contrato o código. Las opciones
`--allow-partial` y `--allow-mismatch` existen solo para diagnóstico.

Una comparación con hardware diferente describe configuraciones completas; no
permite atribuir por sí sola las diferencias exclusivamente al sistema
operativo.

## Perfil focal del diagnóstico de Lyapunov

`profile_lyapunov.py` conserva una línea base reproducible del contrato actual
de `integer_qr_benettin_lyapunov`: un calentamiento, cinco mediciones, mediana,
configuración numérica, versiones, hashes de fuentes, estado del commit y los
hotspots de una ejecución con `cProfile`. Ejecútelo con:

```bash
python benchmarks/profile_lyapunov.py
```

El resultado `benchmarks/results/lyapunov_profile_current.json` caracteriza la
implementación Python vigente. No demuestra una aceleración ni autoriza por sí
solo una migración a C; cualquier kernel nuevo debe compararse con la misma
configuración y validar primero equivalencia numérica.

# Entorno y build

## Entorno soportado

El proyecto soporta Python 3.12. Python 3.14 no tiene soporte formal. En macOS o Linux, cree el entorno con:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

En Windows (PowerShell o Git Bash, adaptando la activación al shell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

Los perfiles son intencionadamente independientes:

```bash
# Runtime API y navegador
python -m pip install -r requirements.txt

# Pruebas (incluye runtime)
python -m pip install -r requirements-dev.txt

# Escritorio, además de runtime
python -m pip install -r requirements-webview.txt

# Build, además de runtime y escritorio
python -m pip install -r requirements-build.txt

# Herramientas auxiliares opcionales (actualmente ReportLab)
python -m pip install -r requirements-tools.txt
```

## Ejecución

La suite canónica se ejecuta con `bash run_all_tests.sh`. Los modos de aplicación son:

```bash
python -m app.web_main --browser
python -m app.web_main --desktop
python -m app.web_main --smoke-test
```

Sin argumento, la aplicación intenta abrir el modo escritorio y usa el navegador como fallback si pywebview no está disponible. `--smoke-test` levanta el servidor local, comprueba `/health` y el shell web, y lo detiene sin abrir interfaz gráfica.

## Datos y puertos

`ANALISIS_SACYL_DATA_DIR` define el directorio escribible de datos. Por compatibilidad, `SALUD_V1_DATA_DIR` se usa cuando la variable nueva no está definida. Si ninguna existe, el valor predeterminado es `~/.analisis-sacyl/`. `ANALISIS_SACYL_PORT` permite fijar el puerto local; sin valor se selecciona uno libre.

La separación de directorios es:

- código y recursos web de solo lectura en la raíz del proyecto o del bundle;
- base y configuración persistente bajo el directorio de datos;
- importaciones en `uploads/` bajo ese directorio;
- temporales de ejecución en `tmp/` bajo ese directorio.

Al migrar una base existente, el proceso necesita permisos de escritura tanto sobre la base como en su directorio contenedor para poder crear el backup junto a ella.

## Recursos offline

El dashboard carga Apache ECharts 5.6.0 desde `web/assets/vendor/echarts-5.6.0.min.js`; no depende de una CDN. El README del vendor registra el origen oficial exacto, la licencia Apache 2.0 y el SHA-256.

## Build portable de Windows

En Windows con Git Bash y un entorno Python 3.12 que ya tenga instalados los perfiles runtime, desktop y build:

```bash
bash scripts/build_windows.sh
```

El script valida el entorno antes de limpiar `build/` y `dist/`, ejecuta el spec versionado en formato onedir y valida `dist/AnalisisSACYL/AnalisisSACYL.exe --smoke-test` con timeout. No instala dependencias ni descarga recursos.

PyInstaller genera binarios nativos para el sistema anfitrión; en la práctica no se puede producir un ejecutable Windows nativo desde macOS. El workflow `Build Windows` de GitHub Actions usa `windows-latest`, Python 3.12, ejecuta las pruebas enfocadas, construye, inspecciona y publica la carpeta portable como artefacto.

El resultado no incluye firma, instalador ni formato onefile. Estas instrucciones tampoco prometen soporte formal para Python 3.14.

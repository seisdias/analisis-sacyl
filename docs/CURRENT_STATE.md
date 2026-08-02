# Estado técnico actual

Fotografía posterior a la integración de la PR #27 mediante **Squash and merge**.

## Estado canónico

- Repositorio: `seisdias/analisis-sacyl`.
- `main` es la fuente canónica estable; `dev` está sincronizada con ella.
- `6a8b2d5` es el commit squash de consolidación técnica generado por la PR #27 y el punto de partida del cierre documental.
- Antes de crear `docs/final-roadmap-closure`, `main` y `dev` estaban sincronizadas en `6a8b2d5`. Tras integrar el cierre, volverán a sincronizarse en el nuevo commit de `main`; el estado canónico es su sincronización, no un SHA permanente.
- `docs/final-roadmap-closure` es temporal, sirve únicamente para este cierre documental y se eliminará después de integrarse.

## Estructura local

- La ruta local canónica final será `/Volumes/SamsungEVO/ws/analisis-sacyl`.
- El worktree `/Volumes/SamsungEVO/ws/analisis-sacyl-import-safety` fue temporal para la consolidación y se eliminará después de integrar este cierre.
- `main` y `dev` se usarán normalmente en la carpeta original, alternando mediante `git switch`; no requieren carpetas permanentes separadas.
- Los worktrees adicionales se crearán solo temporalmente cuando haga falta trabajar simultáneamente en varias ramas.

## Componentes activos

| Ruta | Responsabilidad |
|---|---|
| `lab_pdf/` | Extracción y parsers de informes PDF. |
| `db/` | Esquema SQLite v4, preparación segura y persistencia. |
| `api/` | FastAPI, sesiones, importación y consultas. |
| `web/` | Shell, dashboard y ECharts 5.6.0 local. |
| `charts/` | Series e histogramas proxy. |
| `ranges/` | Rangos predeterminados y estado editable en memoria. |
| `app/` | Rutas de recursos y datos, launcher y bridge pywebview. |
| `tests/` | Contratos unitarios, integración, seguridad, runtime y build. |

## Operación confirmada

- Python soportado y probado: 3.12.
- Perfiles separados: runtime, dev, webview, build y tools.
- Modos: `--browser`, `--desktop` y `--smoke-test`.
- Servidor limitado a `127.0.0.1`, con puerto dinámico o `ANALISIS_SACYL_PORT`.
- Prioridad de datos: `ANALISIS_SACYL_DATA_DIR`, `SALUD_V1_DATA_DIR`, `~/.analisis-sacyl`.
- Recursos frozen de solo lectura y directorios separados para PDFs, SQLite y temporales.
- ECharts local, sin dependencia de CDN.
- Importación transaccional por PDF y uploads confinados.
- SQLite v4 con clasificación, backup y migración de esquemas reconocidos.

Comandos principales:

```bash
python -m app.web_main --browser
python -m app.web_main --desktop
python -m app.web_main --smoke-test
bash run_all_tests.sh
```

## Validación final

- Local: 226 pruebas recogidas, 224 aprobadas, 2 omitidas, 0 fallos y 92 % de cobertura.
- `git diff --check`: correcto.
- PR #27: head final previo al squash `68a6497`; checks de tests y build correctos; comentarios P1 y P2 corregidos y resueltos.
- Windows: workflow `Build Windows`, run `30759025520`, commit técnico validado `6bd0bad`.
- Build PyInstaller, pruebas, smoke test del ejecutable e inspección de contenido prohibido: correctos.
- Artefacto validado: `AnalisisSACYL-windows`.

## Privacidad confirmada

- Los PDFs temporales se crean con modo `0600` desde el primer instante en POSIX.
- Los backups SQLite se crean con `0600` y `backups/` queda protegido con `0700`.
- Las regresiones de permisos se prueban bajo `umask 022` y restauran el umask original.
- Windows mantiene compatibilidad funcional; las comprobaciones específicas de modos POSIX se omiten allí.
- Datos clínicos reales, PDFs reales y SQLite personales permanecen fuera del repositorio y de los artefactos.

## Ramas y flujo

Las ramas temporales de consolidación fueron eliminadas después de quedar absorbidas. Se conservan `main`, `dev`, `feature/export_analytics` y `feature/mac-os-tahoe`.

La rama actual `docs/final-roadmap-closure` es temporal y será eliminada tras la integración de este cierre documental.

`feature/export_analytics` sigue pendiente de auditoría e incorporación. `feature/mac-os-tahoe` contiene ajustes experimentales para Mac mini M1/macOS Tahoe, no está integrada y queda fuera del cierre actual.

El flujo acordado mantiene `main` estable y protegida; sincroniza `dev` con `main` cuando no hay integración pendiente; crea `feature/*` desde `dev`; integra PR mediante **Squash and merge**; avanza después `dev` hasta `main`; y elimina ramas temporales tras verificarlas.

## Limitaciones y riesgos residuales

- `MIGRATIONS` no contiene migraciones SQLite futuras.
- La identidad cuando falta o cambia el número de petición sigue pendiente de definición.
- Falta una política fuerte que impida mezclar identidades de paciente.
- Los rangos editables son globales y no persistentes.
- Las sesiones viven solo en memoria y no tienen expiración.
- Quedan validaciones de dominio y una revisión de usos de `innerHTML`.
- Persisten legado Tk y nomenclatura histórica.
- No existe distribución macOS validada, firma de código ni instalador Windows.

Los histogramas RBC, PLT y WBC son proxies visuales sin valor diagnóstico.

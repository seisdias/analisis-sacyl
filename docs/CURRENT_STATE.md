# Estado técnico actual

Fotografía documental de `chore/final-consolidation@183fab0`, construida sobre la base técnica consolidada `6bd0bad`. Hasta una integración autorizada, esta rama es la verdad técnica provisional.

## Componentes activos

| Ruta | Responsabilidad |
|---|---|
| `lab_pdf/` | Extracción y parsers de informes PDF. |
| `db/` | Esquema SQLite v4, preparación segura y persistencia. |
| `api/` | FastAPI, sesiones, importación y consultas. |
| `web/` | Shell, dashboard y ECharts 5.6.0 local. |
| `charts/` | Series e histogramas proxy. |
| `ranges/` | Rangos predeterminados y estado editable en memoria. |
| `app/` | Rutas de recursos/datos, launcher y bridge pywebview. |
| `tests/` | Contratos unitarios, integración, seguridad, runtime y build. |

## Operación confirmada

- Python soportado y probado: 3.12.
- Perfiles separados: runtime, dev, webview, build y tools.
- Modos: `--browser`, `--desktop` y `--smoke-test`.
- Servidor limitado a `127.0.0.1`, con puerto dinámico o `ANALISIS_SACYL_PORT`.
- Prioridad de datos: `ANALISIS_SACYL_DATA_DIR`, `SALUD_V1_DATA_DIR`, `~/.analisis-sacyl`.
- Recursos frozen de solo lectura y directorios separados para PDFs, SQLite y temporales.
- ECharts local, sin dependencia de CDN.
- Importación de cada PDF transaccional y uploads confinados.
- SQLite v4 con clasificación, backup y migración de esquemas reconocidos.

Comandos principales:

```bash
python -m app.web_main --browser
python -m app.web_main --desktop
python -m app.web_main --smoke-test
bash run_all_tests.sh
```

## Validación

- Local: 223 pruebas recogidas, 221 aprobadas, 2 omitidas, 0 fallos y 92 % de cobertura.
- Windows: workflow `Build Windows`, run `30759025520`, sobre `6bd0bad`, resultado correcto.
- PyInstaller, smoke test del ejecutable e inspección de contenido prohibido: correctos.
- Artefacto validado: `AnalisisSACYL-windows`.

## Limitaciones y riesgos residuales

- `MIGRATIONS` no contiene migraciones futuras.
- La identidad cuando falta o cambia el número de petición sigue pendiente de definición.
- Falta una política fuerte que impida mezclar identidades de paciente.
- Los rangos editables son globales y no persistentes.
- Las sesiones viven solo en memoria y no tienen expiración.
- Quedan validaciones de dominio y una revisión de usos de `innerHTML`.
- Persisten legado Tk, normalización no conectada y nomenclatura histórica.
- No existe distribución macOS validada, firma de código ni instalador Windows.

Los histogramas RBC, PLT y WBC son proxies visuales sin valor diagnóstico. Los datos clínicos reales, PDFs reales y SQLite personales permanecen fuera del repositorio.

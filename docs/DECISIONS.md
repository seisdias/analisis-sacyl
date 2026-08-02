# Registro de decisiones

Estas decisiones describen el estado consolidado. No inventan historia de producto o esquemas que Git y el código no acrediten.

## D-001 — Verdad técnica provisional

- **Estado:** aceptada.
- **Decisión:** `chore/final-consolidation` es la verdad técnica provisional; `main` solo será canónico después de una integración autorizada.

## D-002 — Datos separados

- **Estado:** aceptada.
- **Decisión:** datos clínicos reales, PDFs reales y SQLite personales permanecen fuera de Git y de artefactos públicos. Solo se usan fixtures autorizados o datos sintéticos.

## D-003 — Arquitectura activa

- **Estado:** aceptada.
- **Decisión:** PDF → parsers → SQLite → FastAPI → frontend web → ECharts es el flujo activo; web/pywebview es la interfaz vigente.

## D-004 — Python y perfiles

- **Estado:** aceptada.
- **Decisión:** Python 3.12 es la versión soportada y probada. Runtime, dev, webview, build y tools permanecen como perfiles separados.

## D-005 — Una base por paciente

- **Estado:** aceptada como modelo conceptual.
- **Decisión:** cada SQLite representa a un paciente y las bases distintas se aíslan mediante sesiones. La validación fuerte de identidad continúa pendiente.

## D-006 — SQLite v4 y migraciones

- **Estado:** aceptada.
- **Decisión:** el esquema canónico usa `PRAGMA user_version = 4`; solo se migran esquemas reconocidos después de clasificarlos y crear un backup verificable. No se inventan migraciones futuras: `MIGRATIONS` continúa vacío.

## D-007 — Rutas escribibles

- **Estado:** aceptada.
- **Decisión:** la prioridad es `ANALISIS_SACYL_DATA_DIR`, `SALUD_V1_DATA_DIR` y `~/.analisis-sacyl`. Recursos frozen son de solo lectura; PDFs, SQLite y temporales están separados.

## D-008 — Offline

- **Estado:** resuelta.
- **Decisión:** ECharts 5.6.0 se distribuye localmente con licencia y hash documentados; el frontend activo no depende de CDN.

## D-009 — Windows

- **Estado:** validada.
- **Decisión:** el build Windows usa `AnalisisSACYL.spec`, formato onedir y workflow dedicado. El artefacto `AnalisisSACYL-windows` fue construido, probado e inspeccionado correctamente.

## D-010 — Histogramas proxy

- **Estado:** aceptada.
- **Decisión:** RBC, PLT y WBC son proxies visuales, no datos directos del analizador ni información diagnóstica.

## D-011 — Rangos

- **Estado:** pendiente de producto.
- **Decisión:** se conserva el estado actual, global y en memoria, hasta definir propiedad, aislamiento y persistencia.

## D-012 — Nomenclatura y plataformas fuera de alcance

- **Estado:** aceptada.
- **Decisión:** el nombre visible es Análisis SACYL y el ejecutable `AnalisisSACYL`; `salud_v1` permanece como compatibilidad histórica. No se integran `feature/export_analytics` ni `feature/mac-os-tahoe`, y no se declara distribución macOS estable.

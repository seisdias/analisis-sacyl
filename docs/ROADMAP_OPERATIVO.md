# Roadmap operativo

## Propósito

Mantener una referencia breve y persistente del estado técnico, las decisiones vigentes y el siguiente punto de consolidación del proyecto.

## Contexto activo

- Repositorio: `seisdias/analisis-sacyl`
- Carpeta activa: `/Volumes/SamsungEVO/ws/analisis-sacyl-import-safety`
- Base técnica consolidada: `6bd0bad`
- Rama actual: `chore/final-consolidation`

## Fuente de verdad

La fuente de verdad es, por este orden práctico, el código versionado en Git, el grafo y los commits identificados, las pruebas automatizadas y la ejecución comprobada en cada plataforma. Este documento resume ese estado; no sustituye esas evidencias.

## Estado de los pasos

| Paso | Alcance | Estado | Avance |
|---:|---|---|---:|
| 1 | Workspace y repositorio | Completado | 100 % |
| 2 | Auditoría inicial | Completado | 100 % |
| 3 | Documentación base | Completado | 100 % |
| 4 | Pruebas reproducibles y CI | Completado | 100 % |
| 5 | Protección de importaciones | Completado | 100 % |
| 6 | Seguridad y migraciones SQLite | Completado | 100 % |
| 7 | API e integración | Completado | 100 % |
| 8 | Entorno, dependencias y build | Completado | 100 % |
| 9 | Consolidación final | En curso | 20 % |

## Paso 9 — Consolidación final

- **9.1 Ingesta de ramas y commits:** completado.
- **9.2 Roadmap operativo:** en curso.
- **9.3 Reconciliación documental:** pendiente.
- **9.4 Integración:** pendiente.
- **9.5 Adaptaciones mínimas:** pendiente.
- **9.6 Verificación completa:** pendiente.
- **9.7 Auditoría e informe de cierre:** pendiente.

## Cadena técnica integrada

1. `main`: `6b116d7`
2. `chore/test-baseline`: `5052be6`
3. `fix/import-safety`: `a70bf1e`
4. `fix/sqlite-safety`: `c426e38`
5. `test/api-integration`: `40cea02`
6. `chore/environment-build`: `82551c8` → `6bd0bad`

La documentación pendiente de reconciliar permanece separada en `docs/codex-baseline`, commit `25ac74e`.

## Validaciones cerradas

Pruebas locales:

- 223 recogidas, 221 aprobadas, 2 omitidas y 0 fallos.
- Cobertura total: 92 %.

Windows:

- Workflow: `Build Windows`.
- Run: `30759025520`, commit `6bd0bad`, resultado `success`.
- Instalación limpia, pruebas focalizadas, build PyInstaller, smoke test e inspección de contenido prohibido: correctos.
- Artefacto: `AnalisisSACYL-windows`.
- Tamaño: 24.191.505 bytes.
- SHA-256: `a9cef2f7307a9c356d1d2a28461b28ab315e22d7a61a9ef76e79fa6e5cbb6b7e`.

## Decisiones vigentes

- No integrar `feature/export_analytics`.
- No integrar `feature/mac-os-tahoe`.
- No crear PR ni fusionar sin autorización expresa.
- No acceder ni añadir datos clínicos reales.
- Mantener SQLite y PDFs reales fuera del repositorio.

## Punto actual y siguiente acción

Punto exacto actual: cadena técnica integrada y validada en `6bd0bad`; ingesta 9.1 completada y elaboración del roadmap 9.2 en curso sobre `chore/final-consolidation`.

Siguiente acción prevista: reconciliar `docs/codex-baseline` con el estado técnico final.

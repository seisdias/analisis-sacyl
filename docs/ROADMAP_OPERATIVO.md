# Roadmap operativo

## Propósito

Mantener una referencia persistente del cierre de la consolidación y del flujo de trabajo acordado para las siguientes etapas.

## Estado canónico

- Repositorio: `seisdias/analisis-sacyl`.
- PR #27 integrada mediante **Squash and merge**.
- `main` es la fuente canónica estable y `dev` está sincronizada con ella.
- `6a8b2d5` es el commit squash de consolidación técnica creado por la PR #27 y el punto de partida de este cierre documental.
- `main` y `dev` estaban sincronizadas en `6a8b2d5` antes de crear `docs/final-roadmap-closure`; después de integrar el cierre volverán a sincronizarse en el nuevo commit de `main`.
- `docs/final-roadmap-closure` es una rama temporal dedicada exclusivamente a este cierre y será eliminada tras integrarse.

## Estructura local final

- La ruta local canónica será `/Volumes/SamsungEVO/ws/analisis-sacyl`.
- `/Volumes/SamsungEVO/ws/analisis-sacyl-import-safety` fue un worktree temporal de consolidación y se eliminará después de integrar este cierre documental.
- `main` y `dev` no necesitan carpetas locales separadas: normalmente se alternará entre ellas en la carpeta original mediante `git switch`.
- Solo se crearán worktrees adicionales, de forma temporal, cuando sea necesario trabajar simultáneamente en varias ramas.

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
| 9 | Consolidación final | Completado | 100 % |

## Paso 9 — Consolidación final

- **9.1 Ingesta de ramas y commits:** completado.
- **9.2 Roadmap operativo:** completado.
- **9.3 Reconciliación documental:** completado.
- **9.4 Integración:** completado.
- **9.5 Adaptaciones mínimas:** completado.
- **9.6 Verificación completa:** completado.
- **9.7 Auditoría e informe de cierre:** completado.

## Validación final

Validación local:

- 226 pruebas recogidas, 224 aprobadas, 2 omitidas y 0 fallos.
- Cobertura total: 92 %.
- `git diff --check`: correcto.

PR #27:

- Head final anterior al squash: `68a6497`.
- Checks de tests y build: `success`.
- Comentarios P1 y P2 corregidos y resueltos.

Privacidad:

- PDFs temporales creados con `0600` desde el primer instante en POSIX.
- Backups SQLite creados con `0600` y directorio `backups/` protegido con `0700`.
- Pruebas de regresión ejecutadas bajo `umask 022`.
- Compatibilidad funcional mantenida en Windows.

Validación Windows previa:

- Workflow `Build Windows`, run `30759025520`, commit técnico `6bd0bad`.
- Build, pruebas, smoke test e inspección de contenido prohibido: correctos.
- Artefacto validado: `AnalisisSACYL-windows`.

## Ramas

Las ramas históricas y temporales de consolidación fueron eliminadas después de quedar absorbidas.

`docs/final-roadmap-closure` es la última rama temporal del proceso y se eliminará después de integrar este documento.

Ramas conservadas:

- `main`;
- `dev`;
- `feature/export_analytics`, pendiente de auditoría e incorporación;
- `feature/mac-os-tahoe`, con ajustes experimentales para Mac mini M1/macOS Tahoe, no integrada y fuera de este cierre.

## Flujo futuro

1. `main` permanece estable y protegida.
2. `dev` se mantiene sincronizada con `main` cuando no existe una integración pendiente.
3. Las nuevas ramas `feature/*` nacen desde `dev`.
4. Las PR se integran en `main` mediante **Squash and merge**.
5. Después de cada merge, `dev` avanza hasta `main`.
6. Las ramas temporales se eliminan una vez verificadas.

## Cierre

Los pasos 1–9 están completados al 100 %. El trabajo posterior comienza como alcance nuevo desde `dev`; no reabre esta consolidación.

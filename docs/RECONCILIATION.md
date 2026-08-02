# Reconciliación técnica y documental

Esta reconciliación compara la fotografía histórica `main@6b116d7`, documentada en `docs/codex-baseline@25ac74e`, con `chore/final-consolidation@183fab0`. La base técnica consolidada es `6bd0bad`.

| Área | Afirmación histórica | Estado reconciliado | Resultado |
|---|---|---|---|
| Fuente canónica | `main@6b116d7` | `chore/final-consolidation` es provisional hasta integración autorizada | Sustituida |
| Pruebas | Suite bloqueada; 49 aprobadas y 55 % | 223 recogidas, 221 aprobadas, 2 omitidas, 92 % | Sustituida |
| Python | CI 3.10 y build 3.12 sin política | Python 3.12 soportado y probado | Sustituida |
| Dependencias | `httpx` y PyInstaller no declarados | Cinco perfiles separados y rangos acotados | Sustituida |
| Ejecución | Uvicorn directo y fallback pywebview no confirmado | Browser, desktop y smoke test probados | Sustituida |
| Servidor | Puerto 8000 del launcher histórico | Loopback con puerto dinámico o variable explícita | Sustituida |
| Rutas | Escrituras y uploads parcialmente relativos | Raíz estable y directorios separados fuera del bundle | Sustituida |
| SQLite | Versión 3 no persistida y sin migraciones | Versión 4, clasificación, backup y migración reconocida | Sustituida con límite futuro |
| Importación | No atómica y uploads débiles | Transacción por PDF, confinamiento y limpieza | Sustituida |
| API | Deuda de pruebas | Contratos y flujos críticos cubiertos | Actualizada |
| Offline | ECharts desde CDN | ECharts 5.6.0 local con licencia y hash | Sustituida |
| Build Windows | Script no reproducible y sin validación CI | Spec versionado, workflow y artefacto validados | Sustituida |
| Privacidad | Política propuesta | Exclusiones, temporales, backups e inspección de artefacto documentados | Reforzada |
| Histogramas | Proxies | Continúan siendo proxies sin valor diagnóstico | Conservada |
| Rangos | Globales y en memoria | Sin cambio; decisión de producto pendiente | Conservada |
| Una base por paciente | Modelo conceptual vigente | Vigente; falta validación fuerte de identidad | Conservada con riesgo residual |

## Cadena integrada

`6b116d7` → `5052be6` → `a70bf1e` → `c426e38` → `40cea02` → `82551c8` → `6bd0bad` → `183fab0`

No se incorporan `feature/export_analytics` ni `feature/mac-os-tahoe`. La documentación histórica queda preservada por Git y no requiere un directorio duplicado.

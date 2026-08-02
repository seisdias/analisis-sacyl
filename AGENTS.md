# Reglas de trabajo del repositorio

## Fuente de verdad y alcance

- Mientras no exista una integración autorizada, `chore/final-consolidation` y el código ejecutable son la verdad técnica provisional. Después de integrarse, prevalecerá `main`.
- Compruebe código, Git y pruebas antes de conservar afirmaciones históricas.
- Mantenga cada tarea dentro de su alcance y no mezcle cambios ajenos.
- No cambie silenciosamente APIs, formatos de respuesta, rutas persistentes ni el esquema SQLite.

## Privacidad y SQLite

- No abra, copie, inspeccione ni versione datos clínicos reales, bases SQLite personales o PDFs sin anonimización comprobada.
- Use únicamente fixtures autorizados o datos sintéticos temporales.
- Todo cambio de esquema requiere versión explícita, clasificación compatible, backup verificable, migración probada y manejo seguro de fallos.
- No invente la historia de versiones antiguas ni migraciones futuras. `MIGRATIONS` vacío es un límite real del estado actual.
- Los histogramas RBC, PLT y WBC son proxies visuales sin valor diagnóstico.

## Pruebas y terminado

- Ejecute las pruebas proporcionales al cambio; la suite canónica es `bash run_all_tests.sh`.
- No declare compatibilidad de plataforma, build o migración sin evidencia ejecutada.
- Una tarea termina cuando el alcance está cubierto, las pruebas relevantes pasan o el bloqueo queda documentado, privacidad e integridad han sido revisadas, la documentación afectada está actualizada y `git status` contiene solo los archivos previstos.

# Datos y privacidad

## Principio

El repositorio contiene código, configuración, documentación y fixtures autorizados. Los datos clínicos reales pertenecen exclusivamente al entorno local de la persona usuaria y nunca deben incorporarse a Git, artefactos públicos, logs, capturas o canales de colaboración.

Cada base SQLite representa conceptualmente la historia longitudinal de un paciente y debe tratarse como información sanitaria sensible.

## Material permitido y prohibido

Se permiten fixtures previamente anonimizados, datos completamente sintéticos y bases temporales creadas durante pruebas que no se versionen. Todo fixture nuevo requiere revisión independiente.

Se prohíben bases personales, PDFs reales sin anonimización comprobada, identificadores reidentificables, logs con contenido clínico, capturas con datos o rutas sensibles, credenciales y volcados de API con información real.

## Almacenamiento local

La raíz de datos usa `ANALISIS_SACYL_DATA_DIR`, después `SALUD_V1_DATA_DIR` y finalmente `~/.analisis-sacyl`. Bajo ella se separan uploads PDF, uploads SQLite y temporales. Esa separación no convierte el contenido en público ni elimina la necesidad de permisos restrictivos.

Una migración reconocida crea un backup verificable en `backups/` junto a la base. Base y backup contienen la misma categoría de información sensible y requieren protección equivalente. Las bases seleccionadas explícitamente conservan su ubicación.

## Trabajo seguro

- No abra ni inspeccione una base personal para una tarea general.
- Reproduzca defectos con casos mínimos sintéticos o anonimizados.
- No imprima contenido clínico completo; sanitice errores, nombres y rutas.
- Elimine temporales y uploads de prueba al terminar.
- Recuerde que `.gitignore` no sustituye la revisión humana ni protege frente a `git add -f`.

## Antes de commit o release

1. Revisar `git status -sb` y el diff completo.
2. Confirmar que no se incluyen DB, SQLite, WAL/SHM, uploads, backups, PDFs no autorizados, logs o rutas personales.
3. Verificar por separado cualquier fixture nuevo.
4. Ejecutar las pruebas solo con datos seguros.
5. Inspeccionar el artefacto desempaquetado, no solo el árbol Git.
6. Confirmar que PyInstaller no incorpora tests, fixtures, PDFs, bases, uploads o backups.

El workflow Windows ya aplica una inspección de contenido prohibido, pero sigue siendo una defensa adicional y no una autorización para manejar datos reales.

# Backlog técnico

Este backlog separa trabajo cerrado, parcialmente resuelto y residual. Un elemento pendiente no autoriza por sí mismo cambios de producto, esquema o datos.

## Completado

- Suite reproducible y comando canónico con cobertura.
- Declaración de `httpx` y separación de perfiles runtime, dev, webview, build y tools.
- Aislamiento del test Tk heredado respecto a la suite activa.
- Contratos e integración de API para sesiones, importación y dashboard.
- Importación transaccional por PDF.
- Confinamiento, nombres internos, limpieza y validación básica de uploads.
- Sustitución atómica de bases sin destruir el original ante fallo.
- SQLite v4, clasificación de esquemas reconocidos y backup previo verificable.
- Python 3.12 unificado para desarrollo, CI y build.
- ECharts 5.6.0 local y funcionamiento sin CDN.
- Build Windows reproducible, smoke test e inspección del artefacto.
- `.gitignore`, cobertura e inventarios históricos normalizados.

## Parcialmente resuelto

### Evolución SQLite futura

La adopción y migración de esquemas reconocidos hasta v4 está probada. Falta definir cualquier migración posterior; `MIGRATIONS` está vacío.

### Seguridad de uploads

Traversal, colisiones, extensión, cabecera, limpieza y errores están cubiertos. Quedan políticas explícitas de tamaño y cuotas.

### Protección de overwrite

La sustitución es atómica y preserva el original si falla. Queda decidir si un overwrite exitoso requiere backup permanente o confirmación adicional de UX.

### Dependencias reproducibles

Los perfiles y rangos están separados y la instalación limpia fue validada. No existe un lock de resolución exacta ni una política formal de actualización.

### Cobertura API y frontend

Los contratos críticos tienen cobertura amplia y el total alcanza 92 %. No hay pruebas visuales end-to-end del frontend.

## Pendiente residual

### Identidad y duplicados

- Definir identidad de una analítica cuando falta o cambia el número de petición.
- Establecer una política fuerte para impedir mezcla accidental de pacientes.

### Rangos

- Decidir si pertenecen al proceso, a la base o al paciente.
- Definir persistencia, migración, API y aislamiento antes de implementar.

### Validación y frontend

- Completar reglas de dominio para fechas, intervalos, límites y campos clínicos.
- Inventariar y reducir usos de `innerHTML` con contenido externo.

### Consistencia y legado

- Unificar gradualmente `salud_v1` y Análisis SACYL sin romper compatibilidad.
- Retirar el legado Tk cuando las referencias estén probadamente inalcanzables.
- Decidir integración o retirada de `lab_pdf/text_norm.py` con fixtures suficientes.
- Revisar comentarios y formato mediante cambios mecánicos separados.

### Distribución

- Decidir firma, instalador y política de releases Windows.
- Definir soporte de otras plataformas solo con validación específica.

# Edición de vehículos — backend

## Proceso y trazabilidad

- Fecha: 2026-11-05.
- Tarea: TASK-EDIT-BE; criterios AC-01 a AC-04 acordados por el coordinador.
- Guías aplicadas: orquestador 1.3.0, Skills 1.0.0, Backend Django 1.0.1, Seguridad 1.1.0 y documentación backend 1.0.0.
- Antes: el sistema permitía registrar y consultar vehículos, pero no actualizar sus datos.
- Después: se admite PATCH parcial de los campos editables, conservando ID y VIN.
- Relaciona el proceso anterior: [Consulta de vehículos](consulta_vehiculos_backend.md).

## Contrato

`PATCH /api/vehicles/{id}/`

Sesión de Django, `Content-Type: application/json` y cabecera `X-CSRFToken` requeridos. `ADMIN` y `RECEPCION` tienen iguales permisos operativos; se conserva el control real del backend. La protección CSRF permanece activa y una solicitud sin token puede recibir 403 antes de la vista.

El cuerpo debe ser un objeto JSON no vacío con uno o varios campos de esta lista:

| Campo | Regla |
| --- | --- |
| `plate` | Texto, normalizado con trim y mayúsculas; formato ASCII `ABC-123-D`, único entre vehículos no eliminados. |
| `brand`, `model`, `version`, `color` | Texto no vacío tras trim, máximo 50 caracteres. |
| `year` | Entero JSON, de 1950 al año actual más uno. |
| `mileage` | `null` o entero JSON entre 0 y 4294967295, límite de `integer unsigned` de MySQL. |

Se rechazan números enviados como texto, booleanos, decimales, objetos y listas donde no corresponden. `mileage: null` elimina el kilometraje; omitirlo lo conserva. Todos los campos omitidos mantienen su valor. No se aceptan `id`, `vin`, `client`, `client_id`, `workshop`, `estatus`, `status`, fechas ni otros campos desconocidos, aunque el valor enviado coincida con el actual.

Ejemplo ficticio:

```json
{"color":"Gris","year":2025,"mileage":42000}
```

### Respuesta correcta

`200` con `detail: "Vehículo actualizado exitosamente."` y `vehicle` con los campos completos ya usados por la consulta: `id`, `plate`, `vin`, `brand`, `model`, `year`, `version`, `color`, `mileage`, `status`, `created_at`, `client: {id, full_name}` y `workshop: {id, name}`.

No se entregan teléfonos, correos o direcciones de otras entidades. El vehículo conserva su cliente, taller y estatus. Las respuestas de la vista usan `Cache-Control: private, no-store`.

### Respuestas de error

| HTTP | Situación |
| --- | --- |
| 401 | Falta sesión, una vez superada la comprobación CSRF aplicable. |
| 403 | Rol insuficiente o rechazo CSRF. |
| 404 | ID inexistente/fuera del rango permitido; vehículo, cliente o taller eliminado lógicamente. |
| 409 | Placa duplicada/conflicto de integridad de actualización; no se revela el otro vehículo. |
| 422 | JSON inválido, cuerpo vacío/no objeto, tipo de contenido incorrecto, campo prohibido o valor inválido. |
| 405 | Método diferente de PATCH en esta ruta. |

Ejemplo de validación: `{"detail":"Revisa los campos marcados.","fields":{"vin":"Este campo no se puede modificar."}}`.

Ejemplo de conflicto: `{"detail":"La placa ya está registrada en otro vehículo.","fields":{"plate":"Esta placa ya está registrada."}}`.

## Implementación e integridad

- `VehicleUpdateValidator`: lista explícita de campos y validación tipada; no hay asignación masiva desde el cuerpo sin validar.
- `VehicleRepository.get_for_update`: precarga cliente/taller/estatus y bloquea con `select_for_update` dentro de transacción; excluye relaciones eliminadas.
- `VehicleRepository.plate_in_use`: excluye el propio ID; permite conservar la misma placa.
- `VehicleRepository.update`: guarda solo campos enviados más `updated_at`; evita sobrescribir campos omitidos de un PATCH concurrente.
- `VehicleFacade.update`: coordina validación, transacción, duplicado y actualización. Captura `IntegrityError` después de salir de `atomic`, para no consultar una transacción rota.
- `vehicle_update`: permisos, contrato HTTP y serialización explícita.

La restricción única de placa ya existente sigue siendo la defensa frente a carreras. No se han modificado modelos, migraciones ni dependencias; el ID automático y VIN permanecen intactos. No se edita cliente/taller ni se añade reasignación o cambio de estatus.

## Pruebas y evidencia

Se añadieron diez métodos en `VehicleUpdateApiTests`:

1. Ambos roles modifican campos permitidos y conservan identificadores/asociaciones.
2. Campos omitidos conservados y kilometraje null/cero.
3. ID/VIN y campos desconocidos rechazados incluso iguales; sin cambios parciales.
4. Tipos/rangos/JSON/cuerpo inválidos rechazados.
5. Placa propia permitida y duplicada rechazada sin filtrar datos.
6. Colisión de índice MySQL tras simular un precheck sin conflicto; rollback y consulta posterior válidos.
7. Sesión y roles operativos obligatorios.
8. IDs inexistentes/fuera de rango y cadena eliminada devuelven 404.
9. CSRF ausente rechazado; token válido permite PATCH.
10. Consulta posterior conserva VIN e identifica por nueva placa.

La prueba de colisión simula la ventana de carrera; no mide concurrencia real. Validación integrada del coordinador: 29 pruebas de workshop aprobadas en MySQL 8.4 aislado (6.030 s), incluidas las diez pruebas nuevas. Se ejecutaron call_command('check') sin incidencias y call_command('makemigrations', check=True, dry_run=True) sin cambios detectados. El código se montó de solo lectura y MEDIA_ROOT apuntó a /tmp dentro del contenedor. No se usó la base principal para las pruebas; la base y red desechables se retiraron al terminar. No se accedió a producción.

## Archivos y límites

Archivos: `backend/config/urls.py`, `backend/workshop/validators.py`, `repositories.py`, `facades.py`, `views.py` y `tests.py`.

No incluye edición de fotografías, VIN/ID, cliente/taller, estatus ni actualizaciones masivas. No se introducen migraciones, herramientas ni políticas de producción. Las validaciones/build/despliegue pendientes deben informarse sin equiparar sintaxis válida con aceptación funcional.

## Cierre integrado

- Se construyó la imagen local con las dependencias ya disponibles y el código nuevo, mediante un Dockerfile temporal fuera del repositorio. El Dockerfile versionado no se modificó. Backend y frontend quedaron iniciados en localhost:8000 y localhost:5173.
- Se ejecutó desde la interfaz local una solicitud inválida (color vacío): devolvió 422 y error por campo; cancelar conservó la información anterior. No se realizó un guardado válido sobre los registros existentes para probar la funcionalidad.
- La revisión independiente TASK-EDIT-SEC no confirmó hallazgos de seguridad en el alcance del cambio. Se revisaron whitelist, permisos, CSRF, límites, transacción, cadena eliminada y ausencia de datos ajenos en conflictos.
- No se ejecutaron auditorías generales de dependencias ni check --deploy con configuración de producción: fuera del alcance de esta edición. No hay SEC abierto ni CR implementado en esta tarea.

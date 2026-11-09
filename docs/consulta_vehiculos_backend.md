# Consulta de vehículos por VIN, placa o ID

## Registro del proceso

- Identificador: VEH-CONSULTA-001 / TASK-BE-001 y TASK-BE-002.
- Fecha: 2026-11-03.
- Guías: orquestador 1.3.0, Skills 1.0.0, Backend Django 1.0.1 y Seguridad 1.1.0.
- Solicitud: consultar un vehículo por VIN, placa o ID, mostrando sus datos, cliente y taller; indicar cuando no existe.
- Antes: la API listaba vehículos de un cliente; no ofrecía una consulta global exacta por identificador.
- Después: se agrega una ruta GET de consulta exacta sin cambiar las rutas de registro/listado existentes.

## Identificación y persistencia

`Vehicle.id` ya es `BigAutoField`, generado automáticamente al registrar el vehículo por la migración existente y la configuración de Django. Se reutiliza este identificador: no se crean modelos, columnas, migraciones ni un segundo consecutivo. No se promete una secuencia sin huecos.

Relación utilizada: `Vehicle.client` → `Client.workshop`. Los vehículos o relaciones cliente/taller eliminados lógicamente no aparecen. Un cliente suspendido sigue siendo consultable; la consulta no cambia su estado ni el del vehículo.

## Contrato API

`GET /api/vehicles/lookup/?field=vin|plate|id&value=<identificador>`

- Sesión Django requerida; mismos permisos operativos para `ADMIN` y `RECEPCION`.
- GET de solo lectura; no necesita cabecera CSRF, sin desactivar middleware ni modificar escrituras.
- Solo admite `field` y `value`, una vez cada uno; no acepta filtros libres del ORM.
- Coincidencia exacta, sin búsquedas parciales ni comodines.
- Se quitan espacios exteriores y se normalizan letras a mayúsculas.
- VIN: 17 caracteres ASCII válidos, sin I, O ni Q. Placa: formato actual `ABC-123-D`.
- ID: entero ASCII positivo de hasta 9223372036854775807. Máximo 19 dígitos; no se asigna desde el cliente.
- Valor recibido limitado a 128 caracteres antes de normalizar.

Ejemplo ficticio: `/api/vehicles/lookup/?field=plate&value=ABC-123-D`.

### Respuesta 200

```json
{
  "vehicle": {
    "id": 123,
    "plate": "ABC-123-D",
    "vin": "1HGCM82633A004352",
    "brand": "Honda",
    "model": "Civic",
    "year": 2026,
    "version": "EX",
    "color": "Azul",
    "mileage": 12345,
    "status": "activo",
    "created_at": "2026-11-03T12:00:00+00:00",
    "client": {"id": 45, "full_name": "Cliente Ejemplo"},
    "workshop": {"id": 7, "name": "Taller Ejemplo"}
  }
}
```

La consulta devuelve solo ID y nombre del cliente y del taller; no sus teléfonos, correos, dirección ni fotografía. Las respuestas de la vista llevan `Cache-Control: private, no-store`.

### Errores

- `401`: falta sesión, según decorador existente.
- `403`: rol insuficiente, según decorador existente; no revela el vehículo.
- `404`: `{"detail":"Vehículo no encontrado."}` para consulta válida sin coincidencias visibles.
- `422`: `{"detail":"Revisa los campos marcados.","fields":{"value":"Mensaje de validación"}}`. `field` se usa para criterio desconocido o parámetros extra; `value` para identificador inválido.
- `405`: el endpoint solo admite GET.

## Responsabilidades y trazabilidad

- REQ-001 (VIN/placa/ID): `VehicleLookupValidator` valida y normaliza; `VehicleRepository.lookup` aplica una lista permitida de filtros.
- REQ-002 (información y asociaciones): `VehicleFacade.lookup` coordina; `views.vehicle_lookup` serializa vehículo y nombres. `select_related('client__workshop', 'estatus')` evita consultas repetidas por relación.
- REQ-003 (sin coincidencia): vista responde 404 con mensaje explícito.
- BR-001 (roles equivalentes): decorador existente `roles_required(ADMIN, RECEPTION)`.
- Seguridad: filtros explícitos para `client.deleted_at` y `client.workshop.deleted_at`; ORM parametrizado, sin SQL construido desde entradas.

Archivos afectados: `backend/config/urls.py`, `backend/workshop/validators.py`, `repositories.py`, `facades.py`, `views.py` y `tests.py`. Sin dependencias nuevas.

## Validación

Se añadieron nueve pruebas en `VehicleLookupApiTests` para ambos roles sin privilegios de superusuario, los tres identificadores, normalización, permisos anónimo/CONSULTA/TECNICO, inexistentes, registros eliminados, clientes suspendidos, parámetros inválidos/repetidos, lectura sin escritura e ID automático. Se comprueba una única consulta ORM al recuperar las relaciones.

Evidencia ejecutada y comunicada por el coordinador:

- `python manage.py check`: sin incidencias.
- `python manage.py makemigrations --check --dry-run`: `No changes detected`.
- `python manage.py test workshop --noinput`: 19 pruebas aprobadas en 6.086 segundos, incluidas las nueve nuevas de consulta.

Entorno: MySQL 8.4 desechable `motora-lookup-spec-test-db`, red aislada sin puerto publicado ni volumen de la base principal; código fuente montado en solo lectura y `MEDIA_ROOT=/tmp/lookup-test-media`. No se conectó a producción ni se ejecutó sobre la base principal. No se cambiaron modelos ni migraciones.

La construcción de la imagen backend seguía en curso por descarga de la imagen base al actualizar este registro. Las pruebas aprobadas no equivalen a despliegue ni a validación del servicio de ejecución; no se declara disponibilidad del endpoint en el contenedor principal todavía.

## Límites

No incluye búsqueda parcial, edición, fotografías, filtros por múltiples criterios ni cambios de permisos. No se añaden restricciones por taller del operador: el contrato actual autoriza a ambos roles a consultar globalmente. Todo cambio futuro de ese alcance requiere nueva SPEC.

## Validación integrada del coordinador - 2026-11-03

- Django check: sin incidencias. makemigrations --check --dry-run: No changes detected.
- Suite workshop: 19 pruebas aprobadas (9 nuevas) en MySQL 8.4 desechable, red aislada, sin puertos ni volumen de la aplicación. Fuente montada en solo lectura; archivos de prueba bajo /tmp.
- Frontend: build Vite y compilación explícita de la plantilla Vue correctos. Revisión del formulario en escritorio y a 390 px de ancho.
- Navegador con sesión ADMIN: VIN, placa en minúsculas e ID de un registro existente devolvieron la misma ficha y los nombres de cliente y taller; ID inexistente mostró Vehículo no encontrado. Cambiar criterio limpió la ficha anterior. No se crearon ni editaron registros para estas consultas.
- Permisos ADMIN/RECEPCION, roles denegados y registros eliminados se verificaron con tests en MySQL aislado; el recorrido de navegador se ejecutó con ADMIN. No se afirma recorrido visual con ambos roles ni todas las dimensiones posibles.
- Imagen backend construida sobre la imagen local ya instalada, copiando el código actualizado; se canceló el build estándar por demora de descarga de la base. Dockerfile y dependencias del repositorio no se modificaron. Backend y frontend reiniciados; base principal preservada.
- Revisión independiente de seguridad: sin hallazgos SEC confirmados en el cambio revisado. No se realizó auditoría global ni check --deploy contra producción.
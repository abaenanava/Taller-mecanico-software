# Progreso del proyecto Motora

## Fase 02 — clientes, talleres y códigos postales

| Área | Estado | Evidencia |
| --- | --- | --- |
| Clientes con roles | Completo | `roles_required` limita clientes a `ADMIN` y `RECEPCION`. |
| Talleres | Completo | Modelo `Workshop`, API `/api/talleres/` y formulario sólo visible para Administración. |
| Cliente por taller | Completo | `Client.workshop` es FK obligatoria; la migración asigna registros anteriores al taller predeterminado. |
| Catálogo SEPOMEX | Completo | `PostalCode`, importador idempotente y ruta `GET /api/codigos-postales/<cp>/`. |
| Validación postal | Completo | Si el CP existe, colonia/municipio/estado deben coincidir; si no existe, la captura queda no verificada. |
| Listado | Completo | Filtros por taller y estatus, orden `full_name`/`created_at`, y páginas de diez elementos. |
| Estatus de cliente | Completo | Sólo Administración puede suspender con `POST /api/clients/<id>/suspend/` o reactivar con `POST /api/clients/<id>/activate/`; no se borra el cliente. |
| Esquema de cliente | Completo | Migraciones `0005` y `0006` mantienen la FK del taller, estatus y longitudes de dirección alineadas con el modelo Django. |
| Verificación final local | Completo | 8 pruebas Django y compilación Vite superadas; una segunda importación añadió 0 filas. |
| Pendiente | Operativo | Carga inicial de credenciales autorizadas requiere variables `SEED_*` y el comando existente. |

## Documentación técnica actualizada

`fase_02.md` conserva la fase original y documenta la continuación con tablas de responsabilidades para modelos, migraciones, comando SEPOMEX, Repository, Facade, validadores, vistas REST, rutas y funciones Vue. También enumera de manera explícita los pendientes que no forman parte de la Fase 02.

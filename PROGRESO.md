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
| Suspensión | Completo | Sólo Administración usa `POST /api/clients/<id>/suspend/`; no borra el cliente. |
| Pendiente | Operativo | Carga inicial de credenciales autorizadas requiere variables `SEED_*` y el comando existente. |

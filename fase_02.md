# Fase 02 — módulo de clientes

| Elemento | Estado | Implementación verificable |
| --- | --- | --- |
| Modelo y tabla `clientes` | Completo | `Client` y migración `0003` incluyen todos los campos, foto y relación futura desacoplada. |
| Acceso por rol | Completo | Sólo `ADMIN` y `RECEPCION` pasan `roles_required`; 401 redirige la interfaz al login y 403 devuelve acceso no autorizado. |
| Seeder seguro | Completo | Comando `seed_authorized_users` usa `SEED_ADMIN_PASSWORD` y `SEED_RECEPTION_PASSWORD`, que Django convierte a hash. |
| Registro | Completo | `POST /api/clients/register/` valida datos y responde `Registro guardado exitosamente`. |
| Consulta y detalle | Completo | `GET /api/clients/` alimenta la cuadrícula y `GET /api/clients/<id>/` obtiene el detalle persistido. |
| Modificación | Completo | `PUT /api/clients/<id>/` acepta formulario multipart y conserva la foto si no se adjunta una nueva. |
| Validación | Completo | Obligatorios, edad, fecha, teléfonos, correo, CP, extensión, firma y límite de 15 MB devuelven mensajes por campo. |
| Duplicados | Completo | Fachada y tres índices únicos bloquean correo, teléfono y nombre+fecha; al chocar se devuelve el registro existente con 409. |
| Pruebas automatizadas | Completo | `ClientRegistrationApiTests` recorre alta, lista, edición y duplicado con Administrador y Recepcionista. |
| Relación sucursal/taller | Pendiente deliberadamente | `Client` no depende de un taller; una futura entidad intermedia puede asociarlo sin rehacer repositorio, fachada ni API. |
| Recuperación de contraseña, auditoría y rate limiting | Pendiente | Requieren una fase de seguridad operativa y una política de negocio. |

## Flujo implementado

`Vue (FormData) → API REST Django → ClientFacade → ClientRegistrationValidator → ClientRepository → MySQL clientes`.

La fachada decide si la operación es válida y única; el repositorio persiste. Esta separación evita que la vista Vue conozca consultas ORM o reglas de negocio.

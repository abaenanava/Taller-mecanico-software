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
| Relación sucursal/taller | Completo en esta continuación | `Client.workshop` es una FK obligatoria hacia `Workshop`; una entidad de sucursal futura puede ampliar esta relación sin modificar el flujo Facade → Repository. |
| Recuperación de contraseña, auditoría y rate limiting | Pendiente | Requieren una fase de seguridad operativa y una política de negocio. |

## Flujo implementado

`Vue (FormData) → API REST Django → ClientFacade → ClientRegistrationValidator → ClientRepository → MySQL clientes`.

La fachada decide si la operación es válida y única; el repositorio persiste. Esta separación evita que la vista Vue conozca consultas ORM o reglas de negocio.

## Continuación: talleres, clientes por taller y código postal

| Elemento | Estado | Implementación y responsabilidad |
| --- | --- | --- |
| Archivo SEPOMEX | Completo | `database/seeds/CPdescarga.txt` se lee en Latin-1; no se versiona mediante `.gitignore`. El importador omite aviso y encabezado. |
| Tabla `codigos_postales` | Completo | `PostalCode` almacena `cp`, colonia, tipo de asentamiento, municipio y estado; `cp` tiene índice y la combinación de fila evita duplicados. |
| `import_sepomex` | Completo | `backend/workshop/management/commands/import_sepomex.py` procesa lotes de 1,000 con `bulk_create(ignore_conflicts=True)`, por lo que puede ejecutarse nuevamente sin duplicar. |
| Consulta postal REST | Completo | `GET /api/codigos-postales/<cp>/` usa `PostalCodeFacade` y `PostalCodeRepository`; entrega estado, municipio, colonias y señal de verificación. |
| Validación de dirección | Completo | `ClientFacade` y `WorkshopFacade` usan el catálogo cuando existe CP; una combinación distinta se rechaza por campo. CP ausente permite captura manual no verificada. |
| Tabla `talleres` | Completo | `Workshop` guarda nombre, dirección, razón social, RFC único, contacto y fotografía; nombre+dirección tiene restricción única. |
| RFC y fotografía | Completo | `validate_workshop` exige RFC mexicano de 12/13 posiciones, teléfono, correo y fotografía PNG/JPG firmada de máximo 15 MB. |
| Talleres por rol | Completo | GET para Administración/Recepción, POST sólo para Administración tanto en Vue como en Django. |
| Relación cliente–taller | Completo | `Client.workshop` usa FK `PROTECT`; la migración crea un taller predeterminado y conserva los clientes previos. |
| Filtros y páginas | Completo | `ClientRepository.list` filtra por taller/estatus, ordena de forma segura y devuelve máximo 10 registros; la API devuelve `total`, `page` y `pages`. |
| Suspensión y reactivación | Completo | `ClientFacade.suspend` cambia a `SUSPENDIDO` y `ClientFacade.activate` restaura `ACTIVO`; ambas rutas y botones exigen `ADMIN`. |
| Migración de alineación | Completo | `0006_align_client_address_fields` sincroniza longitudes de dirección, CP y estatus declarados por `Client` con MySQL. |
| Pruebas | Completo | `ClientRegistrationApiTests` cubre taller duplicado/RFC inválido, rol de Recepción, 12 clientes, páginas, edición, duplicados, suspensión, consulta CP, coincidencia de dirección y CP manual no verificado. |
| Pendiente | No requerido | Edición y detalle de taller no fueron solicitados para esta continuación. |

### Ejecución del catálogo oficial

El archivo descargado de Correos de México se conserva localmente como `database/seeds/CPdescarga.txt`. Para importarlo:

```bash
docker compose exec backend python manage.py import_sepomex --file /app/database/seeds/CPdescarga.txt
```

La ejecución validada leyó 159,311 filas y dejó 159,307 registros únicos. Al repetirla, el total se mantuvo y el comando informó `nuevos registros: 0`. Para `01000`, MySQL devuelve `San Ángel`, `Álvaro Obregón`, `Ciudad de México`, confirmando la conversión correcta de acentos.

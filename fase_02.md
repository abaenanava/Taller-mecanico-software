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

### Componentes, clases y métodos de la continuación

#### Persistencia y migraciones

| Archivo | Componente o método | Responsabilidad concreta |
| --- | --- | --- |
| `backend/workshop/models.py` | `PostalCode` | Representa una fila oficial SEPOMEX: CP, colonia, tipo de asentamiento, municipio y estado. La restricción `cp_asentamiento_unico` evita importar dos veces la misma fila. |
| `backend/workshop/models.py` | `Workshop` | Guarda el taller, su RFC único, contacto, foto y dirección. La restricción `taller_nombre_direccion_unico` bloquea otro taller con la misma dirección y nombre. |
| `backend/workshop/models.py` | `Client.workshop` y `Client.status` | Relaciona cada cliente de forma obligatoria con un taller mediante `PROTECT` y conserva su estado `ACTIVO` o `SUSPENDIDO`. |
| `backend/workshop/migrations/0005_postalcode_workshop_client_workshop_status.py` | `create_default_workshop_and_assign_clients` | Crea el taller predeterminado si aún no existe y asigna a él los clientes anteriores antes de hacer obligatoria la relación, sin borrar registros. |
| `backend/workshop/migrations/0006_align_client_address_fields.py` | Migración de alineación | Ajusta en MySQL las longitudes de colonia, municipio, estado, CP y estatus para que coincidan con el modelo `Client`. |
| `backend/workshop/management/commands/import_sepomex.py` | `Command.add_arguments` | Declara `--file`, que permite cambiar la ruta del TXT sin modificar el código. |
| `backend/workshop/management/commands/import_sepomex.py` | `Command.handle` | Valida el tamaño del archivo, lee Latin-1, omite encabezados, separa por `|`, elimina repeticiones en memoria, guarda lotes de 1,000 e informa filas leídas, registros nuevos y total persistido. |

#### Repository y Facade

| Archivo | Componente o método | Responsabilidad concreta |
| --- | --- | --- |
| `backend/workshop/repositories.py` | `ClientRepository.find_duplicate` | Busca por teléfono personal, correo personal o nombre más fecha de nacimiento; `exclude_id` evita que un cliente choque consigo mismo al editarse. |
| `backend/workshop/repositories.py` | `ClientRepository.save`, `update`, `get_by_id` | Encapsulan la creación, modificación y recuperación de un `Client`, evitando consultas ORM en la vista HTTP. |
| `backend/workshop/repositories.py` | `ClientRepository.list` | Aplica filtro de taller y estatus, permite sólo los órdenes seguros `full_name` y `created_at`, calcula total y devuelve como máximo diez resultados de la página solicitada. |
| `backend/workshop/repositories.py` | `PostalCodeRepository.find` y `matches` | Obtienen colonias de un CP y comprueban que colonia, municipio y estado pertenezcan a ese CP. |
| `backend/workshop/repositories.py` | `WorkshopRepository.find_duplicate`, `save`, `list`, `get_by_id` | Centralizan duplicidad por RFC o dirección, alta, listado y consulta de talleres. |
| `backend/workshop/facades.py` | `ClientFacade.register` | Valida campos y dirección, detecta duplicados antes de insertar y convierte un conflicto de índice MySQL en el registro ya existente. |
| `backend/workshop/facades.py` | `ClientFacade.update` | Obtiene el cliente, valida el formulario multipart, excluye su propio identificador de la búsqueda de duplicados y conserva la foto cuando no se envía otra. |
| `backend/workshop/facades.py` | `ClientFacade.list_clients` y `get_client` | Delegan al repositorio el listado paginado y el detalle usado por la API. |
| `backend/workshop/facades.py` | `ClientFacade.suspend` y `activate` | Cambian exclusivamente el estatus entre `SUSPENDIDO` y `ACTIVO`; no eliminan el expediente ni sus datos. |
| `backend/workshop/facades.py` | `ClientFacade._find_duplicate` y `_validate_address` | Reúnen las tres reglas de duplicidad y confirman que el taller exista y que la dirección coincida con SEPOMEX cuando el CP está catalogado. |
| `backend/workshop/facades.py` | `PostalCodeFacade.lookup` y `verified` | Transforman filas de catálogo en la respuesta REST y permiten captura manual sólo cuando el CP no existe. |
| `backend/workshop/facades.py` | `WorkshopFacade.register` y `list` | Valida el taller, dirección, RFC y duplicados; `register` también cubre conflictos simultáneos del índice único. |

#### Validación, API y permisos

| Archivo | Componente o método | Responsabilidad concreta |
| --- | --- | --- |
| `backend/workshop/validators.py` | `ClientRegistrationValidator.validate` | Revisa obligatorios, edad, fecha, teléfonos, correos, CP, foto PNG/JPG, firma binaria y máximo 15 MB; normaliza teléfonos a `+52` y devuelve errores por nombre de campo. |
| `backend/workshop/validators.py` | `ClientRegistrationValidator.validate_workshop` | Valida los datos de taller, RFC mexicano de 12 o 13 caracteres, correo, teléfono, foto y CP. |
| `backend/workshop/views.py` | `clients`, `create_client`, `client_detail` | Exponen listado, alta y edición REST. Traducen `ClientInputError` a HTTP 422 y duplicados a HTTP 409 con el registro encontrado. |
| `backend/workshop/views.py` | `postal_code` | Atiende `GET /api/codigos-postales/<cp>/` para autocompletar estado, municipio y colonias. |
| `backend/workshop/views.py` | `workshops` | Permite listar talleres a Administración/Recepción y crear talleres únicamente a Administración. |
| `backend/workshop/views.py` | `suspend_client` y `activate_client` | Atienden las rutas POST de cambio de estatus; ambos usan `roles_required(User.Role.ADMIN)`, por lo que Recepción recibe HTTP 403. |
| `backend/config/urls.py` | Rutas de clientes, talleres, CP y estatus | Asocia las URLs REST con sus vistas: clientes, talleres, catálogo postal, suspensión y reactivación. |

#### Vue: funciones de interfaz y consumo REST

| Archivo | Función o cálculo | Responsabilidad concreta |
| --- | --- | --- |
| `frontend/src/main.js` | `emptyClient` y `emptyWorkshop` | Generan formularios vacíos, incluida la lista temporal `_neighborhoods`, para no reutilizar datos del registro anterior. |
| `frontend/src/main.js` | `initials`, `canManageClients`, `isAdmin`, `isEditingClient`, `noticeClass` | Calculan iniciales, permisos visibles, modo de edición y el estilo de mensajes sin repetir lógica en la plantilla. |
| `frontend/src/main.js` | `csrfToken`, `signIn`, `register`, `signOut` | Obtienen el token CSRF y gestionan el ciclo de sesión con las rutas de autenticación existentes. |
| `frontend/src/main.js` | `toggleMenu`, `expandMenu`, `collapseMenu`, `goHome` | Controlan el menú lateral colapsable, la apertura por hover y el regreso al panel principal. |
| `frontend/src/main.js` | `loadWorkshops`, `openWorkshopRegister`, `saveWorkshop` | Cargan los talleres disponibles, restringen visualmente su alta a Administración y envían el formulario multipart al backend. |
| `frontend/src/main.js` | `openRegister`, `openClients`, `loadClients`, `openClientDetail` | Preparan el formulario de alta, solicitan la página filtrada de clientes y recuperan el detalle completo de una tarjeta. |
| `frontend/src/main.js` | `lookupPostal` | Llama al endpoint de CP al capturar cinco dígitos; bloquea estado/municipio para CP verificado o habilita captura manual cuando no existe. |
| `frontend/src/main.js` | `editClient`, `selectPhoto`, `saveClient` | Prepara edición, toma una foto opcional/nueva, construye `FormData` y muestra errores 422, duplicados 409 o confirmaciones de guardado. |
| `frontend/src/main.js` | `changeClientStatus` | Envía `suspend` o `activate` al endpoint correspondiente; sólo se invoca desde botones visibles para Administración y actualiza el detalle/listado al terminar. |
| `frontend/src/style.css` | Sistema visual | Define la interfaz responsiva: acceso, menú lateral, tarjetas, filtros, formularios, alertas, estados activo/suspendido, transiciones y adaptación móvil. No modifica reglas de negocio. |

### Pendientes explícitos de esta continuación

| Pendiente | Motivo y alcance futuro |
| --- | --- |
| Edición y detalle de talleres | La continuación solicitó alta de talleres; las rutas de edición y detalle no se agregaron para no ampliar el alcance. |
| Auditoría de cambios de estatus | Actualmente se conserva el estatus final del cliente; una fase futura puede añadir quién, cuándo y por qué suspendió/reactivó. |
| Recuperación de contraseña y limitación de intentos | Requieren reglas de negocio y operación de correo antes de implementarse. |

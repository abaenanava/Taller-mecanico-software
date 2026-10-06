# Clientes, talleres y códigos postales — documentación técnica

## Alcance actual de la fase 02

El sistema permite a `ADMIN` y `RECEPCION` iniciar sesión, registrar, consultar y modificar clientes y talleres. Cada cliente pertenece a un taller obligatorio. Sólo Administración puede suspender o activar clientes; la Recepcionista no recibe esas acciones en la interfaz y el backend también las bloquea.

Las direcciones de talleres y clientes consultan el catálogo SEPOMEX importado. Cuando el CP existe, municipio, estado y colonias se obtienen del catálogo; cuando no existe, la captura manual queda marcada como no verificada.

## Componentes reales

| Archivo | Componente | Responsabilidad |
| --- | --- | --- |
| `backend/workshop/models.py` | `Client`, `Workshop`, `PostalCode`, `User` | Define las tablas, la relación `Client.workshop`, el estatus activo/suspendido y los índices de unicidad. |
| `backend/workshop/repositories.py` | Repositorios | Centraliza lecturas, filtros paginados, detección de duplicados y persistencia ORM. |
| `backend/workshop/validators.py` | Validadores | Comprueba datos obligatorios, teléfono, correo, RFC, archivos de imagen de hasta 15 MB y coincidencia de la dirección con el catálogo. |
| `backend/workshop/facades.py` | `ClientFacade` | Orquesta alta, edición, listado, suspensión y activación sin llevar reglas de negocio a las vistas HTTP. |
| `backend/workshop/facades.py` | `WorkshopFacade` | Orquesta el alta de talleres y previene RFC o nombre-dirección duplicados. |
| `backend/workshop/facades.py` | `PostalCodeFacade` | Entrega estado, municipio y colonias para un CP. |
| `backend/workshop/permissions.py` | `roles_required` | Exige sesión y verifica los roles admitidos por cada ruta. |
| `backend/workshop/views.py` | Controladores REST | Convierte solicitudes HTTP/multipart en llamadas a Facades y respuestas JSON. |
| `backend/workshop/management/commands/import_sepomex.py` | `import_sepomex` | Importa el archivo local del catálogo en lotes y sin duplicar filas. |
| `frontend/src/main.js` | Vista Vue | Gestiona sesión, menú por rol, formularios, búsqueda de CP, filtros, tarjetas, detalle, paginación y mensajes. |

## Rutas REST usadas por la interfaz

| Ruta | Método | Roles | Uso |
| --- | --- | --- | --- |
| `/api/auth/login/` | `POST` | Público | Inicia sesión Django. |
| `/api/auth/csrf/` | `GET` | Público | Obtiene el token CSRF para solicitudes mutables. |
| `/api/auth/me/` | `GET` | Autenticado | Recupera el usuario y rol actuales. |
| `/api/clients/` | `GET` | ADMIN, RECEPCION | Lista clientes, con filtros, orden y paginación. |
| `/api/clients/register/` | `POST` | ADMIN, RECEPCION | Registra un cliente con taller y foto opcional. |
| `/api/clients/<id>/` | `GET`, `PUT` | ADMIN, RECEPCION | Consulta o modifica un cliente. |
| `/api/clients/<id>/suspend/` | `POST` | ADMIN | Cambia el estatus a suspendido. |
| `/api/clients/<id>/activate/` | `POST` | ADMIN | Reactiva un cliente suspendido. |
| `/api/talleres/` | `GET`, `POST` | ADMIN, RECEPCION | Consulta o registra talleres. |
| `/api/codigos-postales/<cp>/` | `GET` | ADMIN, RECEPCION | Obtiene estado, municipio y colonias de un CP. |

## Diagrama de arquitectura actualizado

- [Diagrama interactivo HTML](diagrama_componentes.html): abrir directamente en un navegador. Incluye zoom, arrastre, filtros, tarjetas de detalle y reproducción de un flujo real de activación/suspensión.
- [Fuente editable ArchiMate](registro_clientes_componentes.archimate): abrir con Archi para modificar el modelo.
- [Fuente PlantUML](registro_clientes_componentes.puml): alternativa de texto para renderizar el mismo mapa de componentes.

El diagrama usa únicamente componentes y rutas presentes en el código de esta fase. La información de cada recuadro está reunida al inicio del HTML en el objeto `architecture`, para que se pueda editar sin cambiar la lógica de interacción.

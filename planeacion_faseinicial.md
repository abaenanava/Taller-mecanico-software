# Planeación de fase inicial — Motora

## Fases y elementos desarrollados

| Fase | Elementos | Estado | Resultado real |
| --- | --- | --- | --- |
| Base técnica | Vue 3/Vite, Django, MySQL 8.4 y Docker Compose | Terminada | Los servicios `frontend`, `backend` y `db` se ejecutan separados. |
| Identidad | CSRF, login, logout, sesión y perfil actual | Terminada | Django autentica y mantiene la sesión con cookie HTTP-only. |
| Usuarios | Registro público con rol inicial `CONSULTA` | Terminada | El navegador no puede elegir ni elevar su rol. |
| Clientes | Alta, consulta, detalle, edición y duplicados | Terminada | Administrador y Recepcionista gestionan datos mediante API REST y Vue. |
| Órdenes | Modelo y consulta de órdenes | Parcial | Existe la consulta; altas, asignación y flujo de reparación quedan pendientes. |

## Módulos y datos

| Módulo terminado | Datos y solución |
| --- | --- |
| Autenticación y autorización | `User` agrega el campo `role`. `roles_required` responde 401 sin sesión y 403 cuando el rol no es `ADMIN` o `RECEPCION`. |
| Usuarios autorizados | `seed_authorized_users` crea/actualiza `administrador` y `recepcionista` con `set_password`; obtiene las contraseñas exclusivamente desde variables de entorno. |
| Clientes | La tabla MySQL `clientes` guarda nombre, contacto alternativo, edad, nacimiento, teléfonos personal/laboral, correos, foto y dirección desglosada. Sus índices únicos impiden repetir correo personal, teléfono personal o nombre con fecha de nacimiento. |
| Vista de clientes | El menú autorizado ofrece registrar y consultar. La consulta usa tarjetas con foto; el detalle permite editar cualquier campo o reemplazar la fotografía. |

## Código generado y responsabilidades

- `backend/workshop/models.py`: define `Client`, usa `db_table = 'clientes'`, mantiene la entidad independiente de talleres/sucursales para agregar una relación futura sin cambiar la API actual, y declara las tres restricciones de unicidad.
- `backend/workshop/validators.py`: `ClientRegistrationValidator.validate` normaliza teléfonos a `+52`, exige campos, valida edad, fecha, correo, CP, máximo de 15 MB y firma PNG/JPG. Devuelve errores por campo mediante `ClientInputError`.
- `backend/workshop/repositories.py`: `ClientRepository` concentra las consultas ORM: búsqueda de duplicado, alta, listado, detalle y actualización. La vista y la fachada no consultan ORM directamente.
- `backend/workshop/facades.py`: `ClientFacade` coordina validación y repositorio. `register` y `update` verifican duplicados antes de escribir y recuperan el existente si un índice único detecta una carrera.
- `backend/workshop/views.py`: traduce solicitudes REST multipart a respuestas JSON. `POST /api/clients/register/`, `GET /api/clients/`, `GET /api/clients/<id>/` y `PUT /api/clients/<id>/` son las rutas del repositorio consumidas por Vue.
- `frontend/src/main.js`: contiene el estado de sesión y las vistas de registro, cuadrícula, detalle y edición; usa `FormData`, CSRF y el mensaje exacto `Registro guardado exitosamente`.
- `backend/workshop/migrations/0003_client_access_constraints.py`: crea el teléfono laboral, renombra la tabla a `clientes` y agrega índices únicos en MySQL.
- `backend/workshop/management/commands/seed_authorized_users.py`: seeder idempotente de los dos roles autorizados; nunca escribe una contraseña literal en el repositorio.

## Configuración de base de datos

Archivo de credenciales local: `/.env` (plantilla: `/.env.example`).

Variables de conexión: `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT`. Para el seeder: `SEED_ADMIN_PASSWORD` y `SEED_RECEPTION_PASSWORD`. No se incluyen valores de credenciales en este documento ni en el repositorio.

## Publicación recomendada

**Frontend: Vercel.** Conectar el repositorio, seleccionar `frontend` como directorio raíz, usar `npm run build`, publicar `dist` y configurar la URL de la API en una variable de entorno de Vite antes de compilar. Cambiar `API` en `frontend/src/main.js` a esa variable durante la preparación de producción.

**Backend y MySQL: Railway.** Crear un servicio desde `backend`, definir las variables anteriores, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` con los dominios finales. Adjuntar una base MySQL administrada, ejecutar `python manage.py migrate`, ejecutar el seeder con las dos variables de contraseña y servir estáticos/media mediante almacenamiento persistente o un proveedor de objetos. Configurar HTTPS antes de activar cookies seguras.

Para despliegue local reproducible: copiar `.env.example` a `.env`, completar secretos, ejecutar `docker compose up --build -d`, aplicar `docker compose exec backend python manage.py migrate` y ejecutar el seeder. La interfaz queda en `http://localhost:5173` y la API en `http://localhost:8000/api/`.

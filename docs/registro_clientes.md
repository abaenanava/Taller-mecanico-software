# Registro de clientes — documentación técnica

## Alcance implementado

El módulo permite que usuarios autenticados con rol `ADMIN` o `RECEPCION` registren y consulten clientes. Las cuentas `TECNICO` y `CONSULTA` no reciben el formulario en Vue y la API rechaza sus llamadas con HTTP `403`. Una solicitud sin sesión recibe HTTP `401`; la interfaz vuelve al login al recibir ese estado.

## Componentes y responsabilidades

| Archivo | Componente | Responsabilidad real |
| --- | --- | --- |
| `backend/workshop/models.py` | `Client` | Persiste identidad, contactos, dirección, fotografía y marcas de tiempo. No relaciona todavía clientes con sucursales o talleres. |
| `backend/workshop/repositories.py` | `ClientRepository` | Centraliza las consultas ORM: lista, persistencia y búsqueda de coincidencias. Ninguna vista consulta directamente `Client.objects`. |
| `backend/workshop/validators.py` | `ClientRegistrationValidator` | Normaliza teléfono mexicano a `+52` + 10 dígitos y valida obligatoriedad, correos, CP, fecha, edad, tamaño/tipo de foto. `ClientInputError` transporta errores por campo. |
| `backend/workshop/facades.py` | `ClientFacade` | Ejecuta el caso de uso: valida, consulta duplicado, evita la escritura si existe y crea el cliente si no existe. |
| `backend/workshop/permissions.py` | `roles_required` | Comprueba sesión, superusuario y rol antes de ejecutar una vista protegida. |
| `backend/workshop/views.py` | `clients` y `create_client` | Son controladores HTTP: toman datos multipart, delegan a la fachada y convierten resultados a JSON/HTTP. |
| `frontend/src/main.js` | Vista Vue | Envía `FormData` con cookie de sesión y CSRF; muestra errores de `422`, cliente existente de `409` y acceso denegado de `403`. |
| `frontend/src/style.css` | Presentación | Define el layout de formulario, listado, alertas de duplicado y vista restringida. |

## API REST

| Ruta | Método | Acceso | Respuesta |
| --- | --- | --- | --- |
| `/api/clients/` | `GET` | `ADMIN`, `RECEPCION` | `200` con colección de clientes. |
| `/api/clients/register/` | `POST` multipart/form-data | `ADMIN`, `RECEPCION` | `201` con cliente nuevo; `409` con el existente; `422` con objeto `fields`; `401`/`403` según sesión/rol. |

La fotografía viaja en el campo `photo`. El backend admite PNG/JPG con tamaño máximo de 30 MB y la persiste en el volumen Docker `media_data` mediante `MEDIA_ROOT=/app/media`.

## Regla de duplicado

Se considera existente el primer cliente que cumpla cualquiera de estas condiciones:

1. Mismo teléfono personal normalizado.
2. Mismo correo personal, sin distinguir mayúsculas/minúsculas.
3. Mismo nombre completo y misma fecha de nacimiento.

La respuesta `409` incluye la ficha serializada del registro encontrado. Vue la muestra en la tarjeta **Registro existente** y no inserta una segunda fila.

## Modelo de datos

`Client` almacena: `full_name`, `alternate_contact_name`, `age`, `birth_date`, `personal_phone`, `street`, `neighborhood`, `municipality`, `state`, `postal_code`, `personal_email`, `work_email`, `photo`, `created_at` y `updated_at`.

El diseño deja a `Client` como entidad independiente. Para habilitar talleres o sucursales después se recomienda crear `Workshop` y una relación `ClientWorkshop` (cliente, sucursal, fecha de alta, estado). No se implementó ahora porque el caso de uso actual no requiere multitenencia y una relación prematura permitiría datos ambiguos.

## Migración y despliegue

`backend/workshop/migrations/0002_client.py` crea la tabla del modelo. El `Dockerfile` aplica migraciones versionadas al iniciar; ya no genera migraciones en tiempo de ejecución.

Para iniciar localmente:

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec backend python manage.py createsuperuser
```

Crear usuarios autorizados desde `/admin/` y asignar `ADMIN` o `RECEPCION`. Las credenciales se leen de `.env`; `.env.example` sólo contiene valores de muestra y `docker-compose.yml` incluye respaldos exclusivamente de desarrollo. No se almacenan secretos reales en el código.

## Diagrama

- Fuente editable de ArchiMate: `docs/registro_clientes_componentes.archimate`.
- Fuente alternativa PlantUML: `docs/registro_clientes_componentes.puml`.
- Vista rápida: `docs/registro_clientes_componentes.svg`.

El gestor de paquetes del sistema no ofrece Archi y bloqueó la instalación del renderizador global por permisos administrativos. Los archivos entregados se mantienen dentro del proyecto y la fuente `.archimate` puede abrirse y editarse con Archi en cualquier equipo donde esté instalado.

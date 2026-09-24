# Planeación — fase inicial de Motora

**Proyecto:** Sistema de reparación para talleres mecánicos  
**Nombre técnico:** Motora  
**Fecha de revisión:** 24 de septiembre de 2026  
**Alcance de este documento:** código generado hasta la fase inicial, su estado real, modelo de datos, seguridad y ruta de despliegue.

---

## 1. Objetivo de la fase inicial

Construir una base web para un taller mecánico que permita identificar usuarios, iniciar y cerrar sesión, registrar usuarios nuevos con privilegios mínimos y consultar órdenes de trabajo. El sistema está separado en una interfaz Vue, una API Django y una base MySQL ejecutados con Docker Compose.

Esta fase **no** es un sistema completo de operación del taller. Su propósito es dejar listas las bases de identidad, seguridad, datos iniciales, interfaz y ejecución local para las fases funcionales posteriores.

## 2. Arquitectura seleccionada

| Capa | Tecnología | Responsabilidad |
| --- | --- | --- |
| Interfaz | Vue 3 + Vite | Presentar login, registro y tablero según la sesión actual. |
| API | Python 3.12, Django 5.2 y Gunicorn | Autenticar, autorizar, aplicar validaciones y exponer datos JSON. |
| Datos | MySQL 8.4 | Persistir usuarios, roles y órdenes de trabajo. |
| Contenedores | Docker Compose | Ejecutar de forma integrada base de datos, backend y frontend. |
| Seguridad de sesión | Sesión de Django + CSRF | Mantener la sesión en cookie HTTP-only y proteger solicitudes que modifican datos. |

Flujo principal:

```text
Navegador (Vue :5173)
        │  fetch con cookies y token CSRF
        ▼
API Django/Gunicorn (:8000) ─────► MySQL 8.4
        │                                │
        └─ autenticación, roles,          └─ usuarios y órdenes
           validación y respuestas JSON
```

## 3. Fases y estado objetivo

| Fase | Módulos incluidos | Estado | Solución implementada |
| --- | --- | --- | --- |
| 0. Base técnica | Docker, Vue, Django, MySQL, configuración | **Terminada** | `docker-compose.yml` inicia los tres servicios; Django se conecta a MySQL mediante variables de entorno. |
| 1. Identidad y acceso | CSRF, login, logout, sesión, perfil actual | **Terminada** | API de autenticación con sesiones Django y cookies HTTP-only. |
| 2. Registro seguro | Alta de usuario desde interfaz | **Terminada** | `POST /api/auth/register/` crea cuentas con rol fijo `CONSULTA`; no acepta el rol enviado por el cliente. |
| 3. Roles | Modelo de roles y visualización del rol | **Terminada parcialmente** | Los roles existen y se devuelven al frontend. Falta aplicar una matriz de permisos por operación de negocio. |
| 4. Órdenes de taller | Entidad y consulta de órdenes | **Terminada parcialmente** | Existe el modelo y `GET /api/orders/`. Faltan crear, editar, asignar técnico, costos, piezas e historial. |
| 5. Operación del taller | Clientes, vehículos, diagnósticos, reparaciones, pagos, reportes | **Pendiente** | Debe planearse e implementarse en siguientes iteraciones. |
| 6. Producción | HTTPS, CI/CD, backups, monitoreo y auditoría | **Pendiente** | La configuración actual es adecuada para desarrollo/local, no para producción. |

## 4. Módulos funcionales y datos tratados

### 4.1 Módulo de usuarios y roles — terminado

**Archivo principal:** `backend/workshop/models.py`

El modelo `User` hereda de `AbstractUser` de Django y añade `role`. Conserva los campos estándar de Django, como `username`, `first_name`, `last_name`, `email`, contraseña hasheada, estado activo y marcas de fecha.

| Rol | Valor almacenado | Uso actual |
| --- | --- | --- |
| Administración | `ADMIN` | Puede administrarse desde Django Admin; falta una matriz de API específica. |
| Recepción | `RECEPCION` | Reservado para futuras altas y gestión de órdenes. |
| Técnico | `TECNICO` | Reservado para diagnósticos, trabajos asignados y actualización de avances. |
| Consulta | `CONSULTA` | Rol asignado a todos los registros públicos; acceso mínimo previsto. |

**Solución de seguridad:** el endpoint de registro no recibe ni confía en un rol proveniente del navegador. La API crea el usuario con `User.Role.VIEWER` (`CONSULTA`). Esto evita una escalación de privilegios por manipulación del formulario.

### 4.2 Módulo de autenticación — terminado

**Archivo principal:** `backend/workshop/views.py`

| Endpoint | Método | Entrada | Resultado | Protección |
| --- | --- | --- | --- | --- |
| `/api/auth/csrf/` | GET | Ninguna | Token CSRF y cookie | `ensure_csrf_cookie` |
| `/api/auth/login/` | POST | `username`, `password` | Usuario y rol, o error | CSRF + autenticación Django |
| `/api/auth/register/` | POST | `first_name`, `username`, `password` | Cuenta creada e inicio de sesión | CSRF + validación de campos |
| `/api/auth/logout/` | POST | Ninguna | Confirmación | CSRF + eliminación de sesión |
| `/api/auth/me/` | GET | Cookie de sesión | Usuario autenticado y rol | Devuelve `401` si no hay sesión |

Validaciones vigentes de registro:

- nombre, usuario y contraseña obligatorios;
- nombre de usuario único, sin distinguir mayúsculas/minúsculas;
- contraseña con al menos 12 caracteres;
- creación mediante `create_user`, que aplica el hash de contraseña de Django;
- inicio de sesión inmediato únicamente después de crear la cuenta.

### 4.3 Módulo de órdenes de trabajo — parcialmente terminado

**Archivo principal:** `backend/workshop/models.py`

Entidad `WorkOrder`:

| Campo | Tipo | Regla / propósito |
| --- | --- | --- |
| `folio` | texto, único | Identificador de orden. |
| `vehicle` | texto | Descripción del automóvil. |
| `service` | texto | Reparación, revisión o diagnóstico solicitado. |
| `status` | enumerado | `DIAGNOSTICO`, `EN_PROCESO` o `LISTO`. |
| `technician` | relación opcional a `User` | Técnico asignado; al eliminarlo queda sin asignar. |
| `created_at` | fecha/hora | Fecha de creación automática. |

La consulta `GET /api/orders/` requiere sesión y devuelve hasta 20 órdenes, de la más reciente a la más antigua. Todavía no hay endpoints de alta, edición ni cambio de estado, por lo que no se debe considerar un módulo operativo terminado.

### 4.4 Módulo de interfaz — terminado para acceso y tablero inicial

**Archivos:** `frontend/src/main.js`, `frontend/src/style.css`, `frontend/vite.config.js`.

La interfaz entrega:

- pantalla visual de login de dos paneles;
- formulario de registro en la misma página;
- manejo de errores mostrados por la API;
- lectura inicial de la sesión existente al cargar;
- tablero inicial con nombre, rol y cierre de sesión;
- diseño adaptable para pantallas pequeñas.

`vite.config.js` configura el compilador de Vue necesario para usar el template definido en `main.js`. Esta configuración corrigió la pantalla vacía detectada durante las pruebas visuales.

## 5. Documentación de archivos generados

| Archivo | Descripción precisa |
| --- | --- |
| `docker-compose.yml` | Declara los servicios `db`, `backend` y `frontend`, sus puertos, variables y volúmenes persistentes. |
| `.env.example` | Plantilla de variables sensibles y de entorno. Se copia a `.env` para cada ambiente; no debe contener secretos reales en Git. |
| `backend/Dockerfile` | Construye la imagen de Django, instala dependencias, usa un usuario no root y ejecuta migraciones/Gunicorn. |
| `backend/requirements.txt` | Dependencias Python: Django, CORS, Gunicorn, PyMySQL y `cryptography` para autenticación MySQL 8. |
| `backend/manage.py` | Punto de entrada de comandos Django. |
| `backend/config/settings.py` | Ajustes de base de datos, aplicación personalizada de usuario, cookies, CORS, CSRF, hosts y seguridad HTTP. |
| `backend/config/urls.py` | Tabla de rutas del admin y API. |
| `backend/config/wsgi.py` | Punto de entrada WSGI usado por Gunicorn. |
| `backend/config/__init__.py` | Registra PyMySQL como adaptador compatible para Django. |
| `backend/workshop/models.py` | Define `User` y `WorkOrder`. |
| `backend/workshop/views.py` | Implementa las respuestas JSON de autenticación, registro y consulta de órdenes. |
| `backend/workshop/admin.py` | Registra `User` y `WorkOrder` en Django Admin. |
| `frontend/package.json` | Dependencias y comandos `dev`/`build` de Vite. |
| `frontend/index.html` | Contenedor raíz donde Vue monta la aplicación. |
| `frontend/src/main.js` | Estado de Vue, llamadas al API, formularios y vistas de login, registro y tablero. |
| `frontend/src/style.css` | Paleta, tipografías, layout, estados de formulario y diseño responsivo. |
| `frontend/vite.config.js` | Plugin Vue y alias de compilación. |
| `README.md` | Arranque rápido, contexto funcional y notas de seguridad. |

## 6. Controles de seguridad presentes y límites actuales

### Implementados

- Contraseñas hasheadas con el mecanismo de Django; no se persisten en texto plano.
- Cookie de sesión `HttpOnly` y `SameSite=Lax`.
- Token CSRF obligatorio en POST de login, registro y cierre de sesión.
- Validación de cuentas activas en login.
- `ALLOWED_HOSTS`, orígenes CORS explícitos y orígenes CSRF configurables.
- `X-Frame-Options: DENY` y `X-Content-Type-Options: nosniff`.
- Backend ejecutado como usuario no root en su contenedor.
- Separación de servicios y volumen persistente para MySQL.

### No terminados / acciones requeridas antes de producción

- Reemplazar todos los valores de ejemplo por secretos fuertes y configurar HTTPS.
- Eliminar el valor de respaldo de `DJANGO_SECRET_KEY` y fallar al iniciar si falta en producción.
- Agregar rate limiting, bloqueo progresivo por intentos fallidos y recuperación de contraseña.
- Añadir auditoría de acciones, respaldo/restauración de MySQL y monitoreo.
- Implementar permisos por endpoint y por objeto; actualmente el rol existe, pero no limita aún cada operación de negocio.
- Versionar migraciones dentro del repositorio. El contenedor actualmente las genera al arrancar, lo cual es útil para esta fase local pero no es el flujo recomendado en producción.
- Reemplazar dependencias `latest` de `frontend/package.json` por versiones bloqueadas.

## 7. Credenciales de MySQL

La plantilla de credenciales se encuentra en **`.env.example`** en la raíz. El archivo real recomendado es **`.env`** en la misma ubicación y no debe subirse a GitHub.

`docker-compose.yml` también contiene valores de desarrollo de respaldo cuando no existe `.env`:

| Variable | Valor de desarrollo actual |
| --- | --- |
| `MYSQL_DATABASE` | `motora` |
| `MYSQL_USER` | `motora_user` |
| `MYSQL_PASSWORD` | `motora_password` |
| `MYSQL_ROOT_PASSWORD` | `motora_root_password` |
| `MYSQL_HOST` | `db` (desde el contenedor backend) |
| `MYSQL_PORT` | `3306` |

Estos valores son **solo para desarrollo local**. Para conectarse desde el host, la base no publica el puerto 3306; se puede usar `docker compose exec db mysql -u motora_user -p motora` o publicar el puerto de manera controlada para un entorno de desarrollo. Nunca se deben reutilizar estas contraseñas en un despliegue real.

## 8. Instrucciones de despliegue local

### Requisitos

- Docker Engine y Docker Compose v2.
- Puertos locales disponibles: `5173` (frontend) y `8000` (API).

### 1. Crear configuración local

Desde la raíz del proyecto:

```bash
cp .env.example .env
```

Editar `.env` y asignar contraseñas y `DJANGO_SECRET_KEY` propios. Una opción para generar una clave es:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 2. Construir e iniciar servicios

```bash
docker compose up --build -d
docker compose ps
```

Resultados esperados:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000/api/auth/csrf/`
- Administración Django: `http://localhost:8000/admin/`

### 3. Crear cuenta administradora

```bash
docker compose exec backend python manage.py createsuperuser
```

Iniciar sesión en `/admin/` y asignar los roles `ADMIN`, `RECEPCION` o `TECNICO` a los usuarios autorizados. Los registros públicos comienzan siempre con `CONSULTA`.

### 4. Detener o reiniciar

```bash
docker compose down
docker compose up -d
```

`docker compose down` conserva el volumen `mysql_data`. Para borrar datos locales deliberadamente se requiere `docker compose down -v`; no usar ese comando en un ambiente con datos relevantes.

## 9. Despliegue para ambiente público (guía inicial)

1. Preparar una máquina Linux con Docker y un dominio.
2. Crear `.env` con credenciales únicas; no usar valores por defecto.
3. Cambiar `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` por el dominio y `CSRF_TRUSTED_ORIGINS` por la URL HTTPS.
4. Ubicar un proxy inverso (Nginx, Caddy o un balanceador administrado) delante de los puertos de la aplicación para terminar TLS/HTTPS.
5. No exponer MySQL a Internet; mantenerlo solo en la red privada de contenedores.
6. Ejecutar `docker compose up --build -d` en el servidor.
7. Configurar copias de seguridad cifradas de MySQL, alertas, registros centralizados y actualizaciones periódicas.
8. Antes de liberar, implementar migraciones versionadas, pruebas automáticas y matriz de permisos por endpoint.

## 10. Pruebas realizadas

| Prueba | Resultado |
| --- | --- |
| Compilación sintáctica Python | Correcta. |
| Inicio de MySQL | Correcto; healthcheck saludable. |
| Inicio de Django y migraciones | Correcto. |
| Inicio de Vite/Vue | Correcto. |
| `GET /api/auth/me/` sin sesión | `401`, comportamiento esperado. |
| Login de técnico de prueba | `200`, sesión y rol devueltos. |
| Registro de usuario | `201`, sesión iniciada y rol `CONSULTA`. |
| `GET /api/orders/` con sesión | `200`, acceso a colección protegida. |
| Inspección visual de login y registro | Correcta después de configurar el alias de Vue. |

## 11. Siguiente fase recomendada

Prioridad de implementación:

1. Diseñar la matriz explícita de permisos por rol y aplicarla en cada endpoint.
2. Implementar clientes y vehículos como entidades separadas.
3. Crear CRUD de órdenes, diagnóstico, asignación técnica y cambio de estado.
4. Añadir piezas, mano de obra, cotizaciones y pagos.
5. Añadir historial/auditoría, filtros, reportes y pruebas automatizadas.

La fase inicial queda cerrada para autenticación, registro seguro, modelo de roles, estructura de órdenes, interfaz de acceso y ejecución local. Las funciones de operación del taller permanecen pendientes y no deben declararse terminadas hasta que cuenten con interfaz, endpoints autorizados y pruebas.

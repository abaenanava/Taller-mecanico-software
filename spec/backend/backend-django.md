---
name: backend-django
description: Guía técnica complementaria a skills.md para desarrollar, revisar y validar el backend Django con MySQL de Motora, traduciendo a Django las reglas escritas para Spring Boot y manteniendo el contrato que consume el frontend.
version: 1.0.1
language: es
requires: ../skills/skills.md
---

## 1. Role

Actúa como un ingeniero backend senior especializado en Django, Python y MySQL.

Tu responsabilidad es mantener y evolucionar el backend de Motora de forma segura, correcta y mantenible, sin romper el contrato que usa el frontend.

Trabajas bajo [orquestador.md](../orquestador/orquestador.md). Este archivo complementa a skills.md: skills.md aporta los principios y este archivo los traduce a Django.

## 2. Relación con skills.md

- skills.md no se modifica. Está escrito para Spring Boot y es la guía del profesor.
- Aplicar de skills.md todo lo que no dependa del framework: protocolo SPEC y trazabilidad, diseño de contratos REST, principios de seguridad, integridad de datos, validación y Definition of Done.
- Cuando skills.md nombre una API de Spring Boot, aplicar su equivalente de la tabla de la sección 3.
- Si skills.md y este archivo chocan en un detalle del framework, gana este archivo.
- Ninguno de los dos archivos autoriza a ampliar el alcance. El orquestador manda sobre ambos.

## 3. Equivalencias Spring Boot a Django

| skills.md (Spring Boot) | Equivalente en Django |
| --- | --- |
| @RestControllerAdvice y ProblemDetail | Manejo central de excepciones que devuelve JSON uniforme sin trazas ni SQL. Con DRF, un exception handler propio |
| DTO de entrada y salida | Serializers (DRF) o formularios y funciones de serialización explícitas. Nunca fields = "__all__" ni devolver el modelo completo |
| Jakarta Bean Validation | Validadores del modelo, forms o serializers en el borde de la API, y restricciones de base de datos como defensa final |
| SecurityFilterChain con denegar por defecto | Autenticación obligatoria por defecto: con DRF, DEFAULT_PERMISSION_CLASSES con IsAuthenticated; sin DRF, login_required o un middleware en cada vista |
| Autorización por operación y por objeto | Permisos por rol y por objeto en cada vista. Filtrar los querysets por lo que el usuario puede ver |
| PasswordEncoder | Password hashers de Django y AUTH_PASSWORD_VALIDATORS. No guardar contraseñas de otra forma |
| Sesión, CSRF y cookies | CsrfViewMiddleware activo, cookie de sesión HttpOnly, cookies Secure en producción |
| CORS mínimo | django-cors-headers con orígenes explícitos y CSRF_TRUSTED_ORIGINS. Sin comodines con credenciales |
| Actuator, Swagger y endpoints administrativos | DEBUG en False, admin de Django restringido o desactivado, documentación de la API solo en desarrollo |
| Spring Data JPA | ORM de Django con select_related y prefetch_related |
| Flyway o Liquibase | Migraciones de Django versionadas en el repositorio |
| @Transactional | transaction.atomic en los casos de uso que escriben varias tablas |
| @Version y bloqueo optimista | Campo de versión, F() para actualizaciones atómicas o select_for_update con justificación |
| Page y Slice | Paginator o la paginación de DRF, con tamaño máximo |
| application.properties y @ConfigurationProperties | settings.py leyendo variables de entorno |
| MockMvc y Testcontainers | Cliente de pruebas de Django o APIClient de DRF, con la base de datos de pruebas MySQL |
| Maven o Gradle con wrapper | requirements.txt con versiones fijas y la imagen de Docker |
| Rate limiting | Throttling de DRF o una librería ya adoptada. No existe por defecto |
| OpenAPI sincronizado | Contrato documentado en el repositorio. Con DRF, un generador de esquema solo si ya se usa |

## 4. Project Context

- Backend: Django con API bajo /api. Usa vistas de Django con JsonResponse; DRF no está declarado en requirements.txt.
- Base de datos: MySQL.
- Autenticación: sesión de Django con cookie y CSRF. No se usa JWT.
- Roles: ADMIN y RECEPCION comparten los accesos operativos. La cuenta nueva tiene permisos de consulta. El rol es CONSULTA.
- Módulos: auth, talleres, clientes (con fotografías), vehículos, estatus y códigos postales (consulta SEPOMEX).
- Entorno: Docker Compose; servicio backend.
- Consumidor: el frontend Vue descrito en frontend.md.

## 5. Core Skills

### Arquitectura
- Organizar el código por apps de negocio, una por módulo.
- Mantener las vistas delgadas: reciben la petición, validan, llaman al caso de uso y responden.
- Mover las reglas de negocio a modelos o a una capa de servicios. No ponerlas en las vistas.
- No introducir capas, microservicios ni librerías que no se hayan pedido.

### Contrato de la API
- Mantener el contrato que ya consume el frontend: rutas, nombres de campos, códigos de estado y formato de errores.
- Respetar la semántica ya usada: 401 sin sesión, 403 sin permiso, 409 conflicto, 422 errores de campos. TODO: si se usa DRF, su validación devuelve 400 por defecto; mantener lo que el frontend espera.
- Devolver los errores de campos en un formato uniforme que el frontend pueda mostrar junto a cada campo.
- Aceptar JSON y multipart (fotografías de clientes y talleres) tal como hoy.
- Mantener un endpoint que establezca la cookie csrftoken al iniciar el frontend, por ejemplo con ensure_csrf_cookie.
- Paginar los listados con un tamaño máximo, y permitir ordenar solo por campos conocidos.
- No cambiar el contrato sin registrar el cambio y coordinarlo con frontend.md.

### Autenticación y autorización
- Exigir autenticación por defecto y declarar de forma explícita lo público.
- Con DRF, cambiar DEFAULT_PERMISSION_CLASSES a IsAuthenticated, porque el valor por defecto es AllowAny.
- Con DRF, no dejar BasicAuthentication activa si la aplicación solo usa sesión.
- Validar rol y permiso en el backend en cada operación, y por objeto cuando aplique. Ocultar un botón en el frontend no protege nada.
- Con SessionAuthentication de DRF, el login y el registro deben seguir exigiendo validación CSRF.
- No usar csrf_exempt, salvo en un caso justificado y documentado.
- El registro de cuentas nunca acepta el rol ni los permisos desde la petición. Siempre crea el rol de consulta.
- TODO: confirmar con el equipo si el registro abierto de cuentas es intencional.
- Usar mensajes de acceso genéricos, como "Correo o contraseña incorrectos".

### Validación
- Validar en el borde de la API con forms o serializers, y respaldar las invariantes con restricciones de la base de datos.
- Limitar tamaño, rango y longitud de los datos de entrada.
- Mantener los mensajes de validación en español y coherentes con el frontend.
- Mapear las excepciones de integridad (por ejemplo, un duplicado) a una respuesta 409 o 422 clara.

### Persistencia y migraciones
- Cambiar el esquema solo con migraciones de Django, versionadas en el repositorio. No modificar tablas a mano.
- No editar una migración que ya se aplicó. Crear una nueva.
- Revisar el SQL de cada migración nueva (sqlmigrate) antes de aplicarla.
- No ejecutar migraciones destructivas ni cambios sobre datos reales sin autorización explícita y sin respaldo.
- Definir claves, unicidad, nulabilidad y checks según las reglas de negocio confirmadas.
- Respaldar la unicidad con restricciones de la base de datos. Una comprobación previa en Python no evita las carreras.
- Usar transaction.atomic cuando una operación escriba en varias tablas.
- Usar select_related y prefetch_related para evitar consultas N+1. No filtrar en Python lo que se puede filtrar en la base de datos.
- Usar el ORM. Si hace falta SQL directo, parametrizarlo y evitar extra() y RawSQL con datos del usuario.
- En MySQL, usar utf8mb4. TODO: confirmar el modo SQL estricto en la configuración.
- Indexar según los filtros y ordenamientos reales, y medir antes de agregar índices.

### Fotografías y archivos
- Validar tamaño, extensión y contenido de cada archivo subido. La verificación de Pillow no basta: un archivo HTML puede pasar como imagen si empieza con una cabecera válida.
- Guardar los archivos con nombres generados, fuera del código de la aplicación.
- No servir los archivos subidos como si fueran código. En producción, servirlos con el servidor web, con el tipo de contenido correcto y, si es posible, desde un dominio distinto.
- Limitar el tamaño de las subidas también en el servidor web.

### Configuración y seguridad
- Leer SECRET_KEY, credenciales de la base de datos y orígenes permitidos de variables de entorno. No escribir secretos en el código.
- Mantener un archivo .env.example sin valores reales y no subir .env al repositorio.
- En producción: DEBUG en False, ALLOWED_HOSTS definido y sin comodines.
- En producción: SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE y CSRF_COOKIE_SECURE en True, y HSTS configurado con cuidado.
- Configurar SECURE_PROXY_SSL_HEADER solo si hay un proxy que lo envíe, entendiendo sus advertencias.
- Mantener SESSION_COOKIE_HTTPONLY en True.
- Mantener CSRF_COOKIE_HTTPONLY en False, porque el frontend lee la cookie csrftoken para enviarla en X-CSRFToken. No cambiarlo sin rediseñar ese flujo con el frontend.
- Mantener activos SecurityMiddleware y XFrameOptionsMiddleware.
- Configurar CORS con django-cors-headers: orígenes explícitos y credenciales permitidas solo para el origen del frontend.
- No registrar contraseñas, tokens ni datos personales en los logs.
- Configurar LOGGING para registrar errores sin exponer detalles al cliente.
- Revisar las dependencias con la herramienta del proyecto. No actualizar versiones mayores sin alcance autorizado.

### Rendimiento
- Medir antes de optimizar. No agregar caché ni índices sin una causa medida.
- Paginar y limitar siempre los listados.
- Limitar el número de consultas por petición y revisarlas con las herramientas del proyecto.
- Definir throttling en el login, el registro y los endpoints costosos solo si se pide. Registrarlo como CR si no existe.

### Pruebas
- Usar el sistema de pruebas de Django (python manage.py test) o el que ya use el proyecto.
- Probar con la base de datos MySQL de pruebas. No usar SQLite para validar comportamiento propio de MySQL.
- Cubrir por cada endpoint tocado: camino correcto, validación, sin sesión (401), rol insuficiente (403), objeto ajeno y conflicto (409).
- No escribir pruebas que solo copien la implementación.

## 6. Contract with Frontend

Lo que frontend.md asume del backend y no debe romperse:

- Base de la API en /api, con CORS y credenciales para el origen del frontend.
- Sesión por cookie y token CSRF en la cookie csrftoken, enviado en X-CSRFToken en POST, PUT, PATCH y DELETE.
- Códigos de estado: 401, 403, 409 y 422 con la semántica de la sección 5.
- Errores de campos devueltos de forma que el frontend los muestre junto a cada campo.
- JSON para la mayoría de las operaciones y multipart para las fotografías.
- URLs de las fotografías devueltas por el backend.
- TODO: documentar en el repositorio la lista de endpoints, campos y formato exacto de errores y paginación.

## 7. Orchestrator

### Carga y registro
- El orquestador debe llamar a este archivo junto con skills.md cuando la tarea sea del backend Django, la API, los permisos, las migraciones o MySQL.
- Al empezar, registrar la versión de skills.md y de este archivo, y las secciones aplicables.
- Aplicar solo lo pertinente al cambio. Estas reglas no autorizan a refactorizar el resto del backend.

### SPEC y alcance
- Escribir criterios AC observables: código de estado, cuerpo de la respuesta, permisos por rol, error de validación y comportamiento ante un objeto ajeno.
- Vincular cada archivo cambiado a un REQ y a un AC.
- Registrar como CR, sin implementar, lo no pedido: dependencias nuevas, throttling, cambios de contrato, cambios de esquema ajenos a la tarea.
- Un cambio de contrato o de esquema que afecte al frontend se informa antes de implementarse.

### Seguridad
- Aplicar la revisión de seguridad.md sobre el diff cuando la tarea toque autenticación, permisos, registro, CSRF, CORS, subida de archivos, secretos, configuración de producción o dependencias.
- Reportar los hallazgos como SEC-xxx. Corregir los que estén dentro del alcance y registrar el resto como CR.

### Validación y evidencia
- Ejecutar dentro del contenedor del backend, con las herramientas del proyecto. El servicio se llama backend en docker-compose.yml.
- Ejecutar python manage.py check, python manage.py makemigrations --check --dry-run y python manage.py test.
- Ejecutar python manage.py check --deploy con la configuración de producción, para detectar ajustes inseguros.
- Aplicar migraciones solo en una base de datos de pruebas o de desarrollo.
- Registrar comando, resultado y limitaciones. No declarar ejecutado lo que no se ejecutó.
- Si no hay entorno o acceso, declararlo como no verificado e indicar cómo comprobarlo.

### Entrega
- Cerrar con la tabla de fases y el resumen ejecutivo del orquestador.
- Incluir: archivos y migraciones cambiados, validaciones ejecutadas y pendientes, cambios de contrato si los hubo, TODO abiertos y hallazgos SEC abiertos.

## 8. Final Checklist

- [ ] python manage.py check sin errores.
- [ ] python manage.py makemigrations --check --dry-run sin cambios pendientes.
- [ ] python manage.py test pasa.
- [ ] python manage.py check --deploy revisado con la configuración de producción.
- [ ] Contrato con el frontend sin cambios, o cambio registrado y coordinado.
- [ ] Autenticación y permisos validados por rol y por objeto.
- [ ] Sin secretos en el código ni en los logs.
- [ ] Migraciones revisadas con sqlmigrate y aplicadas solo en pruebas o desarrollo.
- [ ] Sin dependencias nuevas que no se hayan pedido.
- [ ] Versiones de skills.md y de este archivo registradas, cada AC con su evidencia y las mejoras fuera de alcance como CR.

## 9. Referencias

- Django, seguridad: https://docs.djangoproject.com/en/stable/topics/security/
- Django, lista de verificación de despliegue: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
- Django, CSRF: https://docs.djangoproject.com/en/stable/howto/csrf/
- Django, migraciones: https://docs.djangoproject.com/en/stable/topics/migrations/
- Django, transacciones: https://docs.djangoproject.com/en/stable/topics/db/transactions/
- Django, pruebas: https://docs.djangoproject.com/en/stable/topics/testing/
- Django REST Framework, permisos: https://www.django-rest-framework.org/api-guide/permissions/
- OWASP, Django Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Django_Security_Cheat_Sheet.html
- OWASP, Django REST Framework Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Django_REST_Framework_Cheat_Sheet.html
# Guía del repositorio

## Estructura y organización

Motora gestiona talleres, clientes, vehículos y catálogos de estatus con Django, Vue y MySQL 8.4.

- `backend/config/`: configuración de Django, rutas y WSGI.
- `backend/workshop/`: modelos, vistas HTTP, permisos, validadores, repositorios, fachadas de negocio y pruebas en `tests.py`.
- `backend/workshop/migrations/`: migraciones versionadas; `management/commands/` contiene importadores y comandos de datos iniciales.
- `frontend/src/main.js`: interfaz Vue y comunicación con la API; `style.css`: presentación. `frontend/` contiene la configuración de Vite y dependencias npm.
- `docs/`: documentación y diagramas. `database/seeds/` contiene el catálogo SEPOMEX, excluido de Git. Las imágenes se conservan en el volumen Docker `media_data`.

## Comandos de desarrollo y pruebas

Ejecuta desde la raíz del repositorio, con el motor Linux de Docker Desktop iniciado:

- `docker compose up --build -d`: construye e inicia los servicios; el backend aplica las migraciones al arrancar.
- `docker compose stop`: detiene los servicios conservando los datos.
- `docker compose logs --tail 100 backend frontend`: consulta los registros de ejecución.
- `docker compose exec frontend npm run build`: verifica la compilación del frontend.
- `docker compose exec backend python manage.py test workshop --noinput`: ejecuta las pruebas; requiere credenciales con permiso para crear una base de pruebas independiente.
- `docker compose exec backend python manage.py createsuperuser`: crea un administrador; asigna explícitamente su rol en la aplicación.

Interfaz: `http://localhost:5173`; API: `http://localhost:8000/api/`. Reconstruye después de modificar el backend: su código se copia dentro de la imagen.

## Estilo y nombres

Usa cuatro espacios en Python, funciones `snake_case` y clases `PascalCase`. Conserva dos espacios en JavaScript y métodos `camelCase`. Mantén los procesos de negocio en fachadas, las consultas en repositorios y la normalización en validadores. No hay formateador ni analizador de estilo configurado; evita reformatear código ajeno al cambio.

## Criterios de pruebas

Utiliza `TestCase` de Django y métodos `test_` en `backend/workshop/tests.py`. Cubre solicitudes válidas, validaciones, duplicados y accesos denegados. Conserva permisos operativos iguales para `ADMIN` y `RECEPCION`, tanto en la API como en la interfaz. No existe un porcentaje mínimo de cobertura. Usa MySQL: las migraciones contienen SQL específico de este motor.

## Commits y solicitudes de cambios

El historial utiliza prefijos `feat:`, `fix:` y `docs:`, frecuentemente con descripciones en español. Mantén cada commit enfocado. Las solicitudes de cambios deben explicar el resultado, las verificaciones realizadas, las migraciones y los problemas relacionados cuando corresponda. Incluye capturas para cambios visuales.

## Seguridad y configuración

Copia `.env.example` únicamente si no existe `.env`. No incluyas credenciales, respaldos de bases, imágenes cargadas ni catálogos postales en Git. Conserva las sesiones, CSRF y permisos del backend. Respeta los cambios sin commit y las convenciones de borrado lógico.

## Entrada y alcance de estas instrucciones

La entrada general está en [AGENTS.md](../AGENTS.md); el contrato de trabajo está en [orquestador](orquestador/orquestador.md). Esta guía aporta convenciones y no sustituye las reglas especializadas. En cambios locales conservar el código existente; las mejoras ajenas se registran como CR.

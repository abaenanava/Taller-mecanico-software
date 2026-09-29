# Motora — Gestión segura de taller

Sistema inicial para reparaciones, revisiones y diagnósticos de automóviles.

La documentación del registro de clientes y su diagrama están en [`docs/registro_clientes.md`](docs/registro_clientes.md).

## Arranque

```bash
docker compose up --build
```

- Interfaz: http://localhost:5173
- API: http://localhost:8000/api/

Crear un administrador, después de levantar el stack:

```bash
docker compose exec backend python manage.py createsuperuser
```

Los roles disponibles son `ADMIN`, `RECEPCION`, `TECNICO` y `CONSULTA`. El backend es quien autoriza cada operación; ocultar una vista en el frontend no concede permisos.

## Seguridad incluida

- Contraseñas hasheadas por Django; no se almacenan ni se registran en texto plano.
- Sesiones HTTP-only y protección CSRF para solicitudes que cambian datos.
- Autorización por rol en cada endpoint sensible.
- Validación de origen y host mediante variables de entorno.
- Contenedores separados, usuario no root en backend y credenciales configurables en `.env`.

Ningún sistema puede prometer ser imposible de vulnerar. Antes de producción hay que usar HTTPS, secretos únicos, copias de seguridad, actualizaciones, límites de tasa y una auditoría de seguridad.

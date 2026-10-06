# Motora — Gestión segura de taller

Sistema inicial para reparaciones, revisiones y diagnósticos de automóviles.

La documentación del registro de clientes y su diagrama están en [`docs/registro_clientes.md`](docs/registro_clientes.md).

## Arranque

```bash
docker compose up --build
```

## Códigos postales SEPOMEX

Guarda el TXT oficial descargado desde la página `CodigoPostal_Exportar` de Correos de México en `database/seeds/CPdescarga.txt`. El archivo no se versiona. Con los contenedores levantados, impórtalo una vez (el comando se puede repetir sin duplicar filas):

```bash
docker compose exec backend python manage.py import_sepomex --file /app/database/seeds/CPdescarga.txt
```

- Interfaz: http://localhost:5173
- API: http://localhost:8000/api/

Crear un administrador, después de levantar el stack:

```bash
docker compose exec backend python manage.py createsuperuser
```

## Catálogo oficial de códigos postales

Descarga el TXT nacional desde la página oficial de Correos de México: `https://www.correosdemexico.gob.mx/SSLServicios/ConsultaCP/CodigoPostal_Exportar.aspx`. Selecciona **Todos** y formato **TXT**, y guarda el archivo como `database/seeds/CPdescarga.txt`. El catálogo no se sube a Git.

Después de levantar los contenedores, impórtalo una vez (el comando es idempotente):

```bash
docker compose exec backend python manage.py import_sepomex --file /app/database/seeds/CPdescarga.txt
```

El importador convierte Latin-1 a texto Unicode al leerlo, omite el aviso y encabezado oficiales, e inserta lotes de 1,000 filas. Para consultar un CP desde la API autenticada: `GET /api/codigos-postales/01000/`.

Los roles disponibles son `ADMIN`, `RECEPCION`, `TECNICO` y `CONSULTA`. El backend es quien autoriza cada operación; ocultar una vista en el frontend no concede permisos.

## Seguridad incluida

- Contraseñas hasheadas por Django; no se almacenan ni se registran en texto plano.
- Sesiones HTTP-only y protección CSRF para solicitudes que cambian datos.
- Autorización por rol en cada endpoint sensible.
- Validación de origen y host mediante variables de entorno.
- Contenedores separados, usuario no root en backend y credenciales configurables en `.env`.

Ningún sistema puede prometer ser imposible de vulnerar. Antes de producción hay que usar HTTPS, secretos únicos, copias de seguridad, actualizaciones, límites de tasa y una auditoría de seguridad.

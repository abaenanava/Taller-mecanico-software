# Despliegue de Motora

Configura un servicio Railway con el repositorio como raíz y el `Dockerfile` de esa raíz. El contenedor aplica `migrate --noinput` antes de arrancar Gunicorn. Mantén una sola réplica al aplicar migraciones. La página, la API y Django Admin comparten dominio y puerto.

| Variables | Valor en Railway |
| --- | --- |
| `MYSQL_HOST`, `MYSQL_PORT` | Host DNS de TiDB Cloud y `4000` |
| `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` | Base y credenciales de TiDB |
| `MYSQL_USE_SSL` | `True`. Certifi aporta un bundle de CA que funciona también en Windows. |
| `DB_COMPAT_TIDB` | `True`. Django agrega las claves foráneas en sentencias separadas de sus columnas. |
| `MYSQL_SSL_CA` | Opcional. Ruta a un bundle PEM accesible desde el proceso. |
| `CLOUDINARY_URL` | URL de conexión del panel de Cloudinary. Guárdala como secreto del servicio. |
| `DJANGO_SECRET_KEY` | Clave aleatoria propia del entorno. |
| `DJANGO_DEBUG`, `DJANGO_COOKIE_SECURE` | `False` y `True`, respectivamente. |
| `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | Dominio del servicio sin esquema y origen completo con `https://`, respectivamente. |
| `CORS_ALLOWED_ORIGINS` | Vacío para servir la interfaz desde el mismo origen. |
| `DJANGO_HSTS_SECONDS` | Por ejemplo `3600` para habilitar HSTS. Evalúa subdominios y precarga antes de habilitar sus opciones. |

Railway proporciona `PORT`. Django usa `X-Forwarded-Proto` para reconocer HTTPS y `DJANGO_COOKIE_SECURE=True` activa también la redirección HTTPS por defecto. Conserva la ruta relativa `/api` para que el navegador comparta sesión y CSRF con Django.

Expón el servicio mediante el proxy HTTPS de Railway, que controla `X-Forwarded-Proto`. PyMySQL 1.2.4 exige TLS cuando `MYSQL_USE_SSL=True`, verifica el certificado y el nombre del servidor, y conserva la autenticación `caching_sha2_password` de MySQL local.

Las migraciones 0007 y 0009 crean índices únicos sobre columnas `VIRTUAL` en bases nuevas. Una base MySQL con las migraciones ya registradas conserva su esquema `STORED` y las mismas reglas de unicidad. Si está pendiente 0009, aplícala sin escrituras concurrentes porque retira y recrea el índice de placa. Su reversa se detiene si hay placas de más de ocho caracteres.

Si una migración anterior falló a mitad de camino, revisa el esquema y el historial antes de reintentar. TiDB puede conservar operaciones DDL ejecutadas aunque la migración todavía no aparezca registrada.

Tras aplicar las migraciones, ejecuta una vez los comandos iniciales desde `backend/`, con las dependencias instaladas y el servicio Railway seleccionado en la CLI. Configura `SEED_ADMIN_PASSWORD` y `SEED_RECEPTION_PASSWORD` como secretos para el segundo comando. El importador requiere el TXT SEPOMEX en la máquina local.

```powershell
railway run python manage.py seed_statuses
railway run python manage.py seed_authorized_users
railway run python manage.py import_sepomex --file ../database/seeds/CPdescarga.txt
railway run python manage.py createsuperuser
```

Las fotos nuevas se guardan en Cloudinary y se muestran mediante sus URLs HTTPS. Si importas registros existentes, transfiere también sus fotos y revisa las referencias antes de usar esa base. El almacenamiento de imágenes configurado entrega URLs públicas de Cloudinary. Usa datos de prueba al validar el servicio y revisa esa política de acceso antes de publicar fotos reales.

En desarrollo, Compose usa MySQL con `MYSQL_USE_SSL=False`, fotos en disco y Vite en `http://localhost:5173`. El archivo `.env.example` describe las variables locales.

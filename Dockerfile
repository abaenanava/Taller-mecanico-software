FROM node:22-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/index.html frontend/vite.config.mjs ./
COPY frontend/src ./src
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --create-home --user-group appuser \
    && mkdir -p /app/media \
    && chown appuser:appuser /app/media
COPY backend/manage.py ./manage.py
COPY backend/config ./config
COPY backend/workshop ./workshop
COPY --from=frontend-build /build/dist /app/frontend_dist
RUN DJANGO_DEBUG=True python manage.py collectstatic --noinput
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "mkdir -p /app/media && chown appuser:appuser /app/media && python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind \"0.0.0.0:${PORT:-8000}\" --workers 3"]

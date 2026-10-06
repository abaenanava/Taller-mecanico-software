FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 180 --retries 5 -r requirements.txt && useradd --create-home appuser
COPY . .
RUN chown -R appuser:appuser /app
EXPOSE 8000
CMD ["sh", "-c", "mkdir -p /app/media && chown -R appuser:appuser /app/media && su -s /bin/sh appuser -c 'python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3'"]

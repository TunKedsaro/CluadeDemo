FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect admin static files at build time (dummy key is used only for this step).
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput \
    && chmod +x docker-entrypoint.sh \
    && useradd --system --create-home app \
    && chown -R app /app
USER app

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
# One worker: the rate limit counter lives in per-process memory. Threads give concurrency.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--access-logfile", "-"]

#!/bin/sh
# Wait for DB, migrate, optional superuser + demo seed, then exec the server.
set -e

python - <<'PY'
import os, sys, time
import psycopg

params = dict(
    dbname=os.environ.get("POSTGRES_DB", "event_registration"),
    user=os.environ.get("POSTGRES_USER", "postgres"),
    password=os.environ.get("POSTGRES_PASSWORD", ""),
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    port=os.environ.get("POSTGRES_PORT", "5432"),
    connect_timeout=3,
)
for attempt in range(60):
    try:
        psycopg.connect(**params).close()
        print("database is ready")
        break
    except psycopg.OperationalError:
        time.sleep(1)
else:
    print("database not reachable after 60s", file=sys.stderr)
    sys.exit(1)
PY

python manage.py migrate --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
name = os.environ['DJANGO_SUPERUSER_USERNAME']
if User.objects.filter(username=name).exists():
    print('superuser already exists, skipped')
else:
    User.objects.create_superuser(name, os.environ.get('DJANGO_SUPERUSER_EMAIL', ''), os.environ['DJANGO_SUPERUSER_PASSWORD'])
    print('superuser created')
"
fi

case "$(echo "${SEED_DEMO_DATA:-false}" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes) python manage.py seed_demo_events ;;
esac

exec "$@"

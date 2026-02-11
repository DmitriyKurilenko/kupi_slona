#!/bin/bash

set -e

echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

# Only run migrations and collectstatic for the web service (gunicorn)
# Celery workers should NOT run these to avoid race conditions
if echo "$@" | grep -q "gunicorn"; then
    echo "Running migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "Starting application..."
exec "$@"

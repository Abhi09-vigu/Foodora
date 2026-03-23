#!/usr/bin/env bash
set -euo pipefail

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create/update a superuser for admin access (idempotent).
# Configure these in Railway Variables (preferred):
# - ADMIN_EMAIL
# - ADMIN_PASSWORD
# - ADMIN_USERNAME (optional)
if [[ -n "${ADMIN_EMAIL:-}" ]]; then
  echo "Ensuring private admin user exists..."
  python manage.py create_private_admin --noinput
else
  echo "ADMIN_EMAIL not set; skipping admin creation."
fi

echo "Starting Gunicorn..."
exec gunicorn restaurant_ecommerce.wsgi:application --bind 0.0.0.0:${PORT:-8000}

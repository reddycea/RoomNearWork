#!/usr/bin/env sh
set -e

echo "Creating database tables if missing..."
flask --app backend.app:create_app init-db

echo "Ensuring subscription plans..."
flask --app backend.app:create_app ensure-plans || true

echo "Starting app..."
exec "$@"

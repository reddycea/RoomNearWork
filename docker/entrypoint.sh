#!/usr/bin/env sh
set -e

streamlit run admin/app.py --server.port $PORT --server.address 0.0.0.0

echo "Creating database tables if missing..."
flask --app backend.app:create_app init-db

echo "Ensuring subscription plans..."
flask --app backend.app:create_app ensure-plans || true

if [ "${AUTO_SEED_DB:-1}" = "1" ]; then
  echo "Seeding demo listings if missing..."
  flask --app backend.app:create_app seed-db || echo "Demo seed skipped or failed; app will still start."
fi

echo "Starting app..."
exec "$@"

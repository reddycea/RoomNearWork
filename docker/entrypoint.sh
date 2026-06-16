#!/usr/bin/env bash
set -euo pipefail

# Create tables and billing plans automatically for first-run Docker/local use.
# For production with migrations, set AUTO_INIT_DB=false and run `flask db upgrade` yourself.
if [[ "${AUTO_INIT_DB:-true}" == "true" ]]; then
  flask --app backend.app:create_app init-db
  flask --app backend.app:create_app ensure-plans
fi

# Optional demo data for local testing only.
if [[ "${SEED_DEMO_DATA:-false}" == "true" ]]; then
  flask --app backend.app:create_app seed-db || true
fi

exec "$@"

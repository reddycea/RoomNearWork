#!/usr/bin/env sh
set -e

if [ "${RUN_MIGRATIONS_ON_START:-false}" = "true" ]; then
  flask --app backend.app:create_app db upgrade
fi

exec "$@"

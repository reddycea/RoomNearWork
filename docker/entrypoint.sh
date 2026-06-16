#!/usr/bin/env bash
set -euo pipefail

flask --app backend.app:create_app init-db
exec "$@"

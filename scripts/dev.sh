#!/usr/bin/env bash
set -euo pipefail
export FLASK_APP=backend.app:create_app
flask init-db
flask seed-db
flask run --debug

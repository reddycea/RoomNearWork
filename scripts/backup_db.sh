#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR=${BACKUP_DIR:-./backups}
mkdir -p "$BACKUP_DIR"
TS=$(date +%Y%m%d-%H%M%S)
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_DIR/rnw-$TS.sql.gz"
echo "Backup written to $BACKUP_DIR/rnw-$TS.sql.gz"

#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=${BACKUP_DIR:-backups}
mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d_%H%M%S)

if [[ -n "${MYSQL_DATABASE:-}" && -n "${MYSQL_USER:-}" && -n "${MYSQL_PASSWORD:-}" ]]; then
  mysqldump -h "${MYSQL_HOST:-db}" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" | gzip > "$BACKUP_DIR/rnw_mysql_$STAMP.sql.gz"
  echo "Created MySQL backup: $BACKUP_DIR/rnw_mysql_$STAMP.sql.gz"
elif [[ -f "backend/instance/rnw.sqlite3" ]]; then
  cp backend/instance/rnw.sqlite3 "$BACKUP_DIR/rnw_sqlite_$STAMP.sqlite3"
  echo "Created SQLite backup: $BACKUP_DIR/rnw_sqlite_$STAMP.sqlite3"
else
  echo "No supported database configuration found." >&2
  exit 1
fi

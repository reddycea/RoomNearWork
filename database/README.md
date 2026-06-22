# RNW Database Package

This folder is kept to match the public GitHub repository structure for `reddycea/RoomNearWork`.

## Recommended path

For this updated codebase, the source of truth is the Alembic migration:

    backend/migrations/versions/20260620_0001_rnw_full_upgrade.py

For local development, prefer:

    flask --app backend.app:create_app init-db
    flask --app backend.app:create_app seed-db

For production upgrades, prefer:

    flask --app backend.app:create_app db upgrade

## Files

- `mysql_schema.sql` — MySQL schema helper.
- `mysql_seed_demo.sql` — demo seed notes for MySQL.
- `mysql_rnw_full.sql` — MySQL schema helper + seed notes.
- `postgres_schema.sql` — PostgreSQL schema helper.
- `postgres_seed_demo.sql` — demo seed notes for PostgreSQL.
- `postgres_rnw_full.sql` — PostgreSQL schema helper + seed notes.

The Flask seed command remains safer because it creates password hashes with the installed app code.

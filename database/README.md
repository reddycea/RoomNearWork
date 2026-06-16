# RNW Database Package

This folder contains ready-to-import database files for the upgraded RNW project.

## Recommended for the included Docker setup: MySQL

The current `docker-compose.yml` uses MySQL 8.4, so the easiest database file is:

```bash
mysql_rnw_full.sql
```

### Import into the Docker MySQL container

From the project root:

```bash
docker compose up -d db
cat database/mysql_rnw_full.sql | docker compose exec -T db mysql -urnw -pchange-db-password rnw
```

Then start the full app:

```bash
docker compose up --build
```

## PostgreSQL version

Use these files if you deploy on a host such as Render PostgreSQL:

```bash
postgres_rnw_full.sql
```

Example local import:

```bash
psql "$DATABASE_URL" -f database/postgres_rnw_full.sql
```

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@rnw.local | AdminPass123! |
| Landlord | landlord@rnw.local | LandlordPass123! |
| Tenant | tenant@rnw.local | TenantPass123! |

## Included subscriptions

| Plan | Role | Price | Limit |
|---|---|---:|---:|
| Tenant Plus | tenant | R50pm | Save/apply/recommendations |
| Landlord Pro | landlord | R100pm | 25 active listings |

## Files

- `mysql_schema.sql` — MySQL schema only
- `mysql_seed_demo.sql` — MySQL demo data only
- `mysql_rnw_full.sql` — MySQL schema + demo data
- `postgres_schema.sql` — PostgreSQL schema only
- `postgres_seed_demo.sql` — PostgreSQL demo data only
- `postgres_rnw_full.sql` — PostgreSQL schema + demo data

## Important

These files are for development/demo use. For production, change all demo passwords immediately and use Flask-Migrate/Alembic for database changes after launch.


## Trust/review tables added

The database now includes production launch tables for:

- `property_reviews` — moderated tenant reviews and landlord responses
- `listing_reports` — suspicious/fake listing reports
- `support_tickets` — support/contact tickets
- `legal_consents` — terms/privacy/POPIA consent records
- `payment_webhook_logs` — PayFast/IPN audit logs

The demo seed creates one approved tenant application, one approved review, and one support ticket so the review and admin moderation screens are visible immediately.

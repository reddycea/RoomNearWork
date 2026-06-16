# Migration Notes

The original RNW ZIP had a monolithic Flask application and SQL scripts. The upgraded project uses Flask-Migrate/Alembic.

## New tables added

- `subscription_plans`
- `user_subscriptions`
- `billing_invoices`
- `auth_tokens`
- `login_attempts`

## New columns added

- `users.email_verified_at`
- `users.last_password_reset_at`
- `user_subscriptions.cancelled_at`
- `properties.deposit_amount`
- `properties.transport_access`

## Safe production migration flow

```bash
flask --app backend.app:create_app db migrate -m "billing auth search improvements"
flask --app backend.app:create_app db upgrade
flask --app backend.app:create_app ensure-plans
```

Do not run `init-db` against a live production database because it is intended only for first-time development setup.

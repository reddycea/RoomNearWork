# RNW Deployment

## Recommended production stack

- Gunicorn + Flask
- Nginx reverse proxy
- MySQL or Postgres
- Redis for caching and rate limiting
- PayFast for ZAR subscriptions
- SMTP provider for verification/password emails

## Environment hardening

```env
FLASK_ENV=production
EMAIL_VERIFICATION_REQUIRED=true
PAYMENT_PROVIDER=payfast
PAYFAST_SANDBOX=false
SESSION_COOKIE_SECURE=true
APP_BASE_URL=https://your-domain.example
```

## Backups

Use `scripts/backup_db.sh` on a cron schedule. Store backups away from the server.

## Uploads

Small deployments can use local uploads. Larger deployments should move public images and private verification documents to object storage with signed admin-only URLs.

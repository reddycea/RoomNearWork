# Launch readiness checklist

## Must do before real users

- Replace all secrets and database passwords.
- Use HTTPS and production secure cookies.
- Use PostgreSQL, Redis rate limiting and background workers.
- Configure Google server/browser keys with domain/IP restrictions.
- Review PayFast checkout and ITN validation end-to-end.
- Add antivirus scanning for uploaded ID/proof documents.
- Store private documents in private object storage with short-lived signed URLs.
- Review POPIA, privacy, terms and safety pages with a qualified legal professional.
- Run a restore test from backup.
- Run a security test covering object-level authorization.

## Product polish

- Replace the included SVG background with a licensed kasi/township photograph.
- Add a richer interactive Google map with route polylines if you have a browser key.
- Add WhatsApp notifications only after explicit user consent.

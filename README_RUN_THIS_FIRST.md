# Run Room Near Work First

This package is named to match the GitHub repository: `reddycea/RoomNearWork`.

## Local start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
flask --app backend.app:create_app init-db
flask --app backend.app:create_app seed-db
flask --app backend.app:create_app run
```

Open `http://localhost:5000`.

## Docker start

```bash
docker compose up --build
```

## Important production settings

- Change all secrets in `.env`.
- Set real Google Maps keys for exact workplace address search.
- Use Redis for rate limiting.
- Use PostgreSQL/MySQL in production.
- Keep landlord proof/ID uploads private.

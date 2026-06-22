import os
import sys

bad = []
for key in ["SECRET_KEY", "JWT_SECRET_KEY"]:
    value = os.getenv(key, "")
    if not value or "change" in value or len(value) < 40:
        bad.append(f"{key} is missing or weak")
if os.getenv("FLASK_ENV") == "production" and os.getenv("RATELIMIT_STORAGE_URI", "memory://") == "memory://":
    bad.append("Use Redis-backed rate limiting in production")
if bad:
    print("Security check failed:")
    for item in bad:
        print("-", item)
    sys.exit(1)
print("Security check passed")

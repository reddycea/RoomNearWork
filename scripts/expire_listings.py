from datetime import datetime

from backend.rnw import create_app
from backend.rnw.extensions import db
from backend.rnw.models import Property

app = create_app()
with app.app_context():
    expired = Property.query.filter(Property.is_active.is_(True), Property.expires_at.isnot(None), Property.expires_at < datetime.utcnow()).all()
    for prop in expired:
        prop.status = "expired"
        prop.is_active = False
    db.session.commit()
    print(f"Expired {len(expired)} listings.")

from backend.rnw import create_app
from backend.rnw.services.saved_search_service import run_saved_search_alerts

app = create_app()
with app.app_context():
    count = run_saved_search_alerts()
    print(f"Sent {count} saved-search alert batches.")

import pytest

from backend.rnw import create_app
from backend.rnw.extensions import db
from backend.rnw.services.seed_service import seed_database


@pytest.fixture()
def app():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        seed_database()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()

import pytest

from rnw import create_app
from rnw.extensions import db
from rnw.services.seed_service import seed_database


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

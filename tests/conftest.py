import pytest
import os
import tempfile
from app import app as flask_app
import models


@pytest.fixture
def temp_db():
    """
    Creates an isolated temporary SQLite database for tests.
    """
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    models.init_db(path)
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@pytest.fixture
def client(temp_db):
    """
    Provides an unauthenticated Flask test client with a seeded default admin user.
    """
    models.ensure_default_admin(temp_db)
    flask_app.config['DATABASE'] = temp_db
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client


@pytest.fixture
def auth_client(client):
    """
    Provides an authenticated administrator Flask test client.
    """
    client.post('/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
    return client

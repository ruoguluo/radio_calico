import pytest
import os
from app_prod import app, db, init_db


@pytest.fixture(scope='session')
def test_app():
    """Create and configure a test app instance."""
    # Set test configuration
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL', 'sqlite:///:memory:'),
        'WTF_CSRF_ENABLED': False,
    })
    
    with app.app_context():
        # Initialize the database
        db.create_all()
        yield app
        # Cleanup
        db.drop_all()


@pytest.fixture
def client(test_app):
    """Create a test client for the app."""
    return test_app.test_client()


@pytest.fixture
def app_context(test_app):
    """Create an application context."""
    with test_app.app_context():
        yield test_app

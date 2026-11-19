"""
Pytest Fixtures and Global Test Configuration.
Ensures database tables are initialized before running unit and integration tests.
"""

import pytest
from src.database.session import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initializes the database schema before test suite execution."""
    init_db()
    yield

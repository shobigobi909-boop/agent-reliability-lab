import pytest

from app.db import FakeDB


@pytest.fixture
def fake_db() -> FakeDB:
    return FakeDB()

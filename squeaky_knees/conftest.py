import pytest
from django.core.cache import cache

from squeaky_knees.users.models import User
from squeaky_knees.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture(autouse=True)
def _clear_cache():
    """Keep cache_page-wrapped views from leaking responses across tests."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user(db) -> User:
    return UserFactory()

from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone
from ninja.testing import TestClient  # noqa: F401  (kept for ad-hoc API tests)

from registration.models import Event


@pytest.fixture(autouse=True)
def _reset_state(settings):
    """Clear the rate-limit cache and use a high limit unless a test overrides it."""
    cache.clear()
    settings.REGISTRATION_RATE_LIMIT = "1000/m"
    yield
    cache.clear()


@pytest.fixture
def event(db) -> Event:
    return Event.objects.create(
        name="Django Workshop",
        starts_at=timezone.now() + timedelta(days=7),
        location="Bangkok",
        capacity=2,
    )


@pytest.fixture
def payload() -> dict:
    return {
        "name": "Somchai",
        "email": "somchai@example.com",
        "phone": "0812345678",
        "consent": True,
        "website": "",
    }

"""3.1: rate limit per IP on the registration endpoint."""
from .helpers import post


def test_requests_within_limit_are_not_blocked(client, event, payload, settings):
    settings.REGISTRATION_RATE_LIMIT = "3/m"
    codes = [post(client, event.id, {**payload, "email": f"a{i}@example.com"}).status_code
             for i in range(2)]
    assert 429 not in codes


def test_request_over_limit_returns_429_with_retry_after(client, event, payload, settings):
    settings.REGISTRATION_RATE_LIMIT = "1/m"
    post(client, event.id, payload)
    res = post(client, event.id, payload)
    assert res.status_code == 429
    assert res["Retry-After"] == "60"


def test_rate_limit_is_tracked_per_ip(client, event, payload, settings):
    settings.REGISTRATION_RATE_LIMIT = "1/m"
    first = client.post(f"/api/events/{event.id}/registrations", payload,
                        content_type="application/json", REMOTE_ADDR="10.0.0.1")
    blocked = client.post(f"/api/events/{event.id}/registrations", payload,
                          content_type="application/json", REMOTE_ADDR="10.0.0.1")
    other = client.post(f"/api/events/{event.id}/registrations",
                        {**payload, "email": "other@example.com"},
                        content_type="application/json", REMOTE_ADDR="10.0.0.2")
    assert (first.status_code, blocked.status_code, other.status_code) == (201, 429, 201)


def test_rate_limit_counts_failed_attempts_too(client, event, payload, settings):
    settings.REGISTRATION_RATE_LIMIT = "2/m"
    post(client, event.id, {**payload, "email": "bad"})
    post(client, event.id, {**payload, "email": "bad"})
    assert post(client, event.id, payload).status_code == 429


def test_rate_limit_does_not_apply_to_get_requests(client, event, settings):
    settings.REGISTRATION_RATE_LIMIT = "1/m"
    codes = {client.get("/api/events").status_code for _ in range(5)}
    assert codes == {200}


def test_rate_limited_request_creates_no_registration(client, event, payload, settings):
    from registration.models import Registration
    settings.REGISTRATION_RATE_LIMIT = "1/m"
    post(client, event.id, {**payload, "email": "bad"})
    post(client, event.id, payload)
    assert Registration.objects.count() == 0


def test_rate_limit_resets_after_cache_cleared_window(client, event, payload, settings):
    from django.core.cache import cache
    settings.REGISTRATION_RATE_LIMIT = "1/m"
    post(client, event.id, payload)
    cache.clear()  # simulates window expiry
    res = post(client, event.id, {**payload, "email": "next@example.com"})
    assert res.status_code == 201

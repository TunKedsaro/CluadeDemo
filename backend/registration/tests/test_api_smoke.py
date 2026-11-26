"""Smoke tests for the API. The full QA matrix lives in Tasks.md section 3.1."""
import threading
from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone

from registration.models import Event, Registration


def post(client, event_id, data):
    return client.post(
        f"/api/events/{event_id}/registrations", data, content_type="application/json"
    )


def test_list_and_detail_show_seats_remaining(client, event, payload):
    post(client, event.id, payload)
    listing = client.get("/api/events").json()
    assert listing[0]["seats_remaining"] == 1
    assert set(listing[0]) == {"id", "name", "starts_at", "location", "capacity", "seats_remaining"}
    assert client.get(f"/api/events/{event.id}").json()["seats_remaining"] == 1


def test_detail_404_has_thai_detail(client, db):
    res = client.get("/api/events/999")
    assert res.status_code == 404
    assert isinstance(res.json()["detail"], str)


def test_register_success(client, event, payload):
    res = post(client, event.id, payload)
    assert res.status_code == 201
    reg = Registration.objects.get()
    assert reg.status == "confirmed" and reg.consent_at is not None


def test_duplicate_email_409(client, event, payload):
    post(client, event.id, payload)
    payload["email"] = "SomChai@Example.com"
    assert post(client, event.id, payload).status_code == 409


def test_full_409(client, event, payload):
    for i in range(2):
        payload["email"] = f"u{i}@example.com"
        assert post(client, event.id, payload).status_code == 201
    payload["email"] = "late@example.com"
    assert post(client, event.id, payload).status_code == 409
    assert Registration.objects.count() == 2


def test_past_event_409(client, payload, db):
    past = Event.objects.create(
        name="Old", starts_at=timezone.now() - timedelta(days=1), location="x", capacity=5
    )
    assert post(client, past.id, payload).status_code == 409


def test_missing_event_404(client, payload, db):
    assert post(client, 999, payload).status_code == 404


@pytest.mark.parametrize(
    "change",
    [{"consent": False}, {"email": "bad"}, {"name": ""}, {"phone": "abc"}, {"name": "x" * 101}],
)
def test_invalid_input_422(client, event, payload, change):
    res = post(client, event.id, {**payload, **change})
    assert res.status_code == 422
    assert isinstance(res.json()["detail"], list)


def test_honeypot_rejected(client, event, payload):
    res = post(client, event.id, {**payload, "website": "http://spam"})
    assert res.status_code == 422
    assert isinstance(res.json()["detail"], list)
    assert Registration.objects.count() == 0


def test_cancelled_not_counted_and_email_reusable(client, event, payload):
    post(client, event.id, payload)
    Registration.objects.update(status="cancelled")
    assert client.get(f"/api/events/{event.id}").json()["seats_remaining"] == 2
    assert post(client, event.id, payload).status_code == 201


def test_rate_limit_429(client, event, payload, settings):
    settings.REGISTRATION_RATE_LIMIT = "2/m"
    codes = [post(client, event.id, payload).status_code for _ in range(3)]
    assert codes[-1] == 429
    assert "detail" in post(client, event.id, payload).json()


def test_cors_allows_frontend_origin(client, event):
    res = client.get("/api/events", HTTP_ORIGIN="http://localhost:5500")
    assert res["Access-Control-Allow-Origin"] == "http://localhost:5500"
    res = client.get("/api/events", HTTP_ORIGIN="http://evil.example")
    assert "Access-Control-Allow-Origin" not in res


@pytest.mark.django_db(transaction=True)
def test_last_seat_race_only_one_wins(client, payload):
    event = Event.objects.create(
        name="Race", starts_at=timezone.now() + timedelta(days=1), location="x", capacity=1
    )
    results: list[int] = []
    barrier = threading.Barrier(5)

    def worker(i: int) -> None:
        from django.test import Client

        barrier.wait()
        try:
            res = post(Client(), event.id, {**payload, "email": f"r{i}@example.com"})
            results.append(res.status_code)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sorted(results) == [201, 409, 409, 409, 409]
    assert Registration.objects.count() == 1

"""3.1: GET /api/events and GET /api/events/{id}."""
from datetime import timedelta

from django.utils import timezone

import pytest
from registration.models import Event, Registration

pytestmark = pytest.mark.django_db


def add_reg(event, email, status="confirmed"):
    return Registration.objects.create(
        event=event, name="P", email=email, phone="0800000000",
        consent_at=timezone.now(), status=status,
    )


def test_list_events_returns_empty_list_when_no_events(client, db):
    res = client.get("/api/events")
    assert res.status_code == 200 and res.json() == []


def test_list_shows_full_capacity_when_no_registrations(client, event):
    assert client.get("/api/events").json()[0]["seats_remaining"] == event.capacity


def test_list_seats_remaining_is_zero_when_event_full(client, event):
    add_reg(event, "a@example.com")
    add_reg(event, "b@example.com")
    assert client.get("/api/events").json()[0]["seats_remaining"] == 0


def test_list_excludes_cancelled_from_seat_count(client, event):
    add_reg(event, "a@example.com")
    add_reg(event, "b@example.com", status="cancelled")
    assert client.get("/api/events").json()[0]["seats_remaining"] == 1


def test_list_counts_each_event_separately(client, event):
    other = Event.objects.create(
        name="Other", starts_at=timezone.now() + timedelta(days=9), location="x", capacity=10
    )
    add_reg(event, "a@example.com")
    add_reg(other, "a@example.com")
    add_reg(other, "b@example.com")
    by_id = {e["id"]: e["seats_remaining"] for e in client.get("/api/events").json()}
    assert by_id == {event.id: 1, other.id: 8}


def test_list_is_ordered_by_start_time(client, db):
    now = timezone.now()
    late = Event.objects.create(name="Late", starts_at=now + timedelta(days=9), location="x", capacity=1)
    soon = Event.objects.create(name="Soon", starts_at=now + timedelta(days=1), location="x", capacity=1)
    assert [e["id"] for e in client.get("/api/events").json()] == [soon.id, late.id]


def test_list_includes_past_events(client, db):
    past = Event.objects.create(
        name="Old", starts_at=timezone.now() - timedelta(days=1), location="x", capacity=1
    )
    assert [e["id"] for e in client.get("/api/events").json()] == [past.id]


def test_detail_returns_event_fields(client, event):
    body = client.get(f"/api/events/{event.id}").json()
    assert body["name"] == event.name and body["location"] == event.location
    assert body["capacity"] == 2 and body["seats_remaining"] == 2


def test_detail_seats_remaining_never_negative_when_overbooked(client, event):
    for i in range(3):
        add_reg(event, f"o{i}@example.com")
    assert client.get(f"/api/events/{event.id}").json()["seats_remaining"] == 0


def test_event_endpoints_do_not_expose_registration_data(client, event):
    add_reg(event, "secret@example.com")
    assert "secret@example.com" not in client.get("/api/events").content.decode()
    assert "secret@example.com" not in client.get(f"/api/events/{event.id}").content.decode()


def test_events_endpoint_rejects_post_with_405(client, db):
    assert client.post("/api/events", {}, content_type="application/json").status_code == 405


def test_seats_remaining_property_matches_api(event):
    add_reg(event, "a@example.com")
    assert Event.objects.get(pk=event.pk).seats_remaining == 1

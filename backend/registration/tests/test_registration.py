"""3.1: registration endpoint cases not covered by the smoke tests."""
from datetime import timedelta

import pytest
from django.utils import timezone

from registration.models import Event, Registration

from .helpers import post

pytestmark = pytest.mark.django_db


def make_event(capacity=2, **kwargs):
    defaults = dict(
        name="Event", starts_at=timezone.now() + timedelta(days=3), location="Chiang Mai"
    )
    return Event.objects.create(capacity=capacity, **{**defaults, **kwargs})


def fill(event, n, status="confirmed"):
    for i in range(n):
        Registration.objects.create(
            event=event, name=f"P{i}", email=f"fill{i}-{status}@example.com",
            phone="0800000000", consent_at=timezone.now(), status=status,
        )


# ---- success -------------------------------------------------------------

def test_register_returns_201_with_expected_body(client, event, payload):
    res = post(client, event.id, payload)
    assert res.status_code == 201
    body = res.json()
    assert set(body) == {"id", "event_id", "status", "created_at"}
    assert body["event_id"] == event.id
    assert body["status"] == "confirmed"


def test_register_does_not_echo_personal_data(client, event, payload):
    body = post(client, event.id, payload).json()
    assert "email" not in body and "phone" not in body and "name" not in body


def test_register_decrements_seats_remaining_by_one(client, event, payload):
    before = client.get(f"/api/events/{event.id}").json()["seats_remaining"]
    post(client, event.id, payload)
    after = client.get(f"/api/events/{event.id}").json()["seats_remaining"]
    assert before - after == 1


def test_register_sets_consent_at_to_current_time(client, event, payload):
    start = timezone.now()
    post(client, event.id, payload)
    reg = Registration.objects.get()
    assert start <= reg.consent_at <= timezone.now()


def test_register_stores_submitted_fields(client, event, payload):
    post(client, event.id, payload)
    reg = Registration.objects.get()
    assert (reg.name, reg.email, reg.phone) == ("Somchai", "somchai@example.com", "0812345678")
    assert reg.event_id == event.id


def test_register_lowercases_email_before_saving(client, event, payload):
    post(client, event.id, {**payload, "email": "SomChai@Example.COM"})
    assert Registration.objects.get().email == "somchai@example.com"


def test_register_strips_whitespace_from_name_and_phone(client, event, payload):
    post(client, event.id, {**payload, "name": "  Somchai  ", "phone": "  0812345678 "})
    reg = Registration.objects.get()
    assert reg.name == "Somchai" and reg.phone == "0812345678"


@pytest.mark.parametrize("phone", ["+66 81-234-5678", "(02) 123 4567", "081234"])
def test_register_accepts_allowed_phone_formats(client, event, payload, phone):
    assert post(client, event.id, {**payload, "phone": phone}).status_code == 201


def test_register_accepts_name_at_max_length_100(client, event, payload):
    assert post(client, event.id, {**payload, "name": "x" * 100}).status_code == 201


def test_register_accepts_phone_at_max_length_20(client, event, payload):
    assert post(client, event.id, {**payload, "phone": "1" * 20}).status_code == 201


def test_register_accepts_phone_at_min_length_6(client, event, payload):
    assert post(client, event.id, {**payload, "phone": "1" * 6}).status_code == 201


def test_register_accepts_thai_name(client, event, payload):
    assert post(client, event.id, {**payload, "name": "สมชาย ใจดี"}).status_code == 201


# ---- seats boundary ------------------------------------------------------

def test_register_succeeds_when_one_seat_left(client, payload):
    event = make_event(capacity=3)
    fill(event, 2)
    assert post(client, event.id, payload).status_code == 201
    assert client.get(f"/api/events/{event.id}").json()["seats_remaining"] == 0


def test_register_returns_409_when_zero_seats_left(client, payload):
    event = make_event(capacity=3)
    fill(event, 3)
    assert post(client, event.id, payload).status_code == 409


def test_register_returns_409_and_no_row_when_event_full(client, payload):
    event = make_event(capacity=1)
    fill(event, 1)
    post(client, event.id, payload)
    assert Registration.objects.filter(event=event).count() == 1


def test_register_returns_409_when_capacity_is_zero(client, payload):
    event = make_event(capacity=0)
    assert post(client, event.id, payload).status_code == 409


def test_cancelled_registrations_do_not_use_seats_on_full_capacity(client, payload):
    event = make_event(capacity=2)
    fill(event, 2, status="cancelled")
    assert post(client, event.id, payload).status_code == 201


def test_cancelling_one_registration_frees_seat_of_full_event(client, payload):
    event = make_event(capacity=1)
    fill(event, 1)
    assert post(client, event.id, payload).status_code == 409
    Registration.objects.filter(event=event).update(status="cancelled")
    assert post(client, event.id, payload).status_code == 201


def test_full_event_error_detail_is_string(client, payload):
    event = make_event(capacity=1)
    fill(event, 1)
    assert isinstance(post(client, event.id, payload).json()["detail"], str)


# ---- duplicates ----------------------------------------------------------

def test_same_email_can_register_different_events(client, payload):
    e1, e2 = make_event(name="A"), make_event(name="B")
    assert post(client, e1.id, payload).status_code == 201
    assert post(client, e2.id, payload).status_code == 201


def test_duplicate_email_409_does_not_create_second_row(client, event, payload):
    post(client, event.id, payload)
    post(client, event.id, payload)
    assert Registration.objects.count() == 1


def test_duplicate_check_runs_before_full_check_gives_409_either_way(client, payload):
    event = make_event(capacity=1)
    post(client, event.id, payload)
    assert post(client, event.id, payload).status_code == 409


def test_cancelled_email_can_register_again_and_keeps_history(client, event, payload):
    post(client, event.id, payload)
    Registration.objects.update(status="cancelled")
    assert post(client, event.id, payload).status_code == 201
    assert Registration.objects.filter(status="confirmed").count() == 1
    assert Registration.objects.filter(status="cancelled").count() == 1


# ---- past / not found ----------------------------------------------------

def test_event_that_just_started_returns_409(client, payload):
    event = make_event(starts_at=timezone.now() - timedelta(seconds=1))
    assert post(client, event.id, payload).status_code == 409


def test_event_starting_soon_still_accepts_registration(client, payload):
    event = make_event(starts_at=timezone.now() + timedelta(minutes=5))
    assert post(client, event.id, payload).status_code == 201


def test_past_event_creates_no_registration(client, payload):
    event = make_event(starts_at=timezone.now() - timedelta(days=1))
    post(client, event.id, payload)
    assert Registration.objects.count() == 0


def test_post_to_missing_event_returns_404_with_detail(client, payload, db):
    res = post(client, 999999, payload)
    assert res.status_code == 404
    assert isinstance(res.json()["detail"], str)


def test_get_missing_event_returns_404(client, db):
    assert client.get("/api/events/999999").status_code == 404


def test_post_missing_event_creates_no_registration(client, payload, db):
    post(client, 999999, payload)
    assert Registration.objects.count() == 0


def test_non_numeric_event_id_returns_422(client, payload, db):
    assert post(client, "abc", payload).status_code == 422


# ---- validation (422) ----------------------------------------------------

@pytest.mark.parametrize(
    "change",
    [
        {"name": "   "},
        {"email": ""},
        {"email": "a@"},
        {"email": "@example.com"},
        {"email": "no-at-sign.example.com"},
        {"email": "a b@example.com"},
        {"email": "a@" + "b" * 250 + ".com"},
        {"phone": ""},
        {"phone": "12345"},
        {"phone": "1" * 21},
        {"phone": "08x1234567"},
        {"phone": "<script>"},
        {"phone": "     "},
        {"consent": None},
        {"consent": "abc"},
        {"name": 123},
        {"website": "x" * 201},
    ],
)
def test_register_returns_422_for_invalid_value(client, event, payload, change):
    res = post(client, event.id, {**payload, **change})
    assert res.status_code == 422
    assert Registration.objects.count() == 0


@pytest.mark.parametrize("field", ["name", "email", "phone", "consent"])
def test_register_returns_422_when_required_field_missing(client, event, payload, field):
    del payload[field]
    res = post(client, event.id, payload)
    assert res.status_code == 422
    assert res.json()["detail"][0]["loc"][-1] == field


def test_register_without_honeypot_field_is_allowed(client, event, payload):
    del payload["website"]
    assert post(client, event.id, payload).status_code == 201


def test_register_returns_422_for_empty_body(client, event):
    assert post(client, event.id, {}).status_code == 422


def test_register_returns_422_for_malformed_json(client, event):
    res = client.post(
        f"/api/events/{event.id}/registrations", "{not json", content_type="application/json"
    )
    assert res.status_code in (400, 422)


def test_consent_false_creates_no_registration(client, event, payload):
    post(client, event.id, {**payload, "consent": False})
    assert Registration.objects.count() == 0


def test_422_detail_points_to_consent_field(client, event, payload):
    res = post(client, event.id, {**payload, "consent": False})
    assert res.json()["detail"][0]["loc"][-1] == "consent"


def test_email_with_reserved_test_tld_is_rejected_known_behaviour(client, event, payload):
    """EmailStr rejects special-use domains (.test, localhost); documented in the QA report."""
    assert post(client, event.id, {**payload, "email": "a@example.test"}).status_code == 422
    assert post(client, event.id, {**payload, "email": "a@localhost"}).status_code == 422


def test_sql_injection_like_name_is_stored_literally(client, event, payload):
    name = "Robert'); DROP TABLE registration_registration;--"
    assert post(client, event.id, {**payload, "name": name}).status_code == 201
    assert Registration.objects.get().name == name


def test_html_in_name_is_stored_as_plain_text(client, event, payload):
    name = "<img src=x onerror=alert(1)>"
    post(client, event.id, {**payload, "name": name})
    assert Registration.objects.get().name == name


# ---- honeypot ------------------------------------------------------------

def test_honeypot_with_value_returns_422_without_creating(client, event, payload):
    res = post(client, event.id, {**payload, "website": "spam"})
    assert res.status_code == 422
    assert Registration.objects.count() == 0


def test_honeypot_response_does_not_mention_honeypot(client, event, payload):
    text = post(client, event.id, {**payload, "website": "spam"}).content.decode().lower()
    assert "honeypot" not in text and "website" not in text


def test_honeypot_does_not_consume_a_seat(client, event, payload):
    post(client, event.id, {**payload, "website": "spam"})
    assert client.get(f"/api/events/{event.id}").json()["seats_remaining"] == event.capacity

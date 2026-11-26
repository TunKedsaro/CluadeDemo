"""3.3: Django Admin behaviour (Django test client, real PostgreSQL)."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from registration.models import Event, Registration

from .helpers import post

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(client):
    user = get_user_model().objects.create_superuser(
        username="qa-admin", email="qa-admin@example.com", password="x" * 12 + "Aa1!"
    )
    client.force_login(user)
    return client


def test_admin_requires_login(client, db):
    res = client.get(reverse("admin:registration_event_changelist"))
    assert res.status_code == 302 and "/admin/login/" in res["Location"]


def test_admin_can_create_event(admin_client):
    res = admin_client.post(
        reverse("admin:registration_event_add"),
        {
            "name": "Admin Event", "location": "Phuket", "capacity": 5,
            "starts_at_0": (timezone.localdate() + timedelta(days=10)).isoformat(),
            "starts_at_1": "10:00:00",
        },
    )
    assert res.status_code == 302
    assert Event.objects.get(name="Admin Event").capacity == 5


def test_admin_event_list_shows_seats_remaining(admin_client, event):
    res = admin_client.get(reverse("admin:registration_event_changelist"))
    assert res.status_code == 200
    assert "Seats remaining" in res.content.decode()


def test_admin_can_cancel_selected_registrations_and_seat_returns(admin_client, event, payload):
    post(admin_client, event.id, payload)
    reg = Registration.objects.get()
    assert admin_client.get(f"/api/events/{event.id}").json()["seats_remaining"] == 1
    res = admin_client.post(
        reverse("admin:registration_registration_changelist"),
        {"action": "cancel_selected_registrations", "_selected_action": [reg.pk]},
        follow=True,
    )
    assert res.status_code == 200
    reg.refresh_from_db()
    assert reg.status == "cancelled"
    assert admin_client.get(f"/api/events/{event.id}").json()["seats_remaining"] == 2


def test_admin_cancel_action_only_affects_selected(admin_client, event, payload):
    post(admin_client, event.id, payload)
    post(admin_client, event.id, {**payload, "email": "other@example.com"})
    target = Registration.objects.get(email="somchai@example.com")
    admin_client.post(
        reverse("admin:registration_registration_changelist"),
        {"action": "cancel_selected_registrations", "_selected_action": [target.pk]},
    )
    assert Registration.objects.get(email="other@example.com").status == "confirmed"


def test_admin_cancelled_attendee_can_register_again(admin_client, event, payload):
    post(admin_client, event.id, payload)
    admin_client.post(
        reverse("admin:registration_registration_changelist"),
        {"action": "cancel_selected_registrations",
         "_selected_action": [Registration.objects.get().pk]},
    )
    assert post(admin_client, event.id, payload).status_code == 201


def test_admin_registration_changelist_has_event_and_status_filters(admin_client, event, payload):
    # Django hides the related-object filter when there is only one Event
    Event.objects.create(
        name="Second", starts_at=timezone.now() + timedelta(days=5), location="x", capacity=1
    )
    post(admin_client, event.id, payload)
    html = admin_client.get(reverse("admin:registration_registration_changelist")).content.decode()
    assert "event__id__exact=" in html and "status__exact=" in html


def test_admin_registration_changelist_renders(admin_client, event, payload):
    post(admin_client, event.id, payload)
    res = admin_client.get(reverse("admin:registration_registration_changelist"))
    assert res.status_code == 200 and "somchai@example.com" in res.content.decode()


def test_admin_registration_consent_at_is_readonly(admin_client, event, payload):
    post(admin_client, event.id, payload)
    reg = Registration.objects.get()
    res = admin_client.get(reverse("admin:registration_registration_change", args=[reg.pk]))
    assert 'name="consent_at' not in res.content.decode()

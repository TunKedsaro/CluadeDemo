"""3.1: race conditions. Uses real PostgreSQL with threads (transaction=True)."""
import threading
from datetime import timedelta

import pytest
from django.db import connection
from django.test import Client
from django.utils import timezone

from registration.models import Event, Registration

from .helpers import post


def run_parallel(event_id, payloads):
    """Fire all payloads at the same time; return the list of status codes."""
    results, errors = [], []
    barrier = threading.Barrier(len(payloads))

    def worker(data):
        try:
            barrier.wait(timeout=10)
            results.append(post(Client(), event_id, data).status_code)
        except Exception as exc:  # surfaced in the assertion below
            errors.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(p,)) for p in payloads]
    [t.start() for t in threads]
    [t.join(timeout=30) for t in threads]
    assert not errors, errors
    return results


def make_event(capacity):
    return Event.objects.create(
        name="Race", starts_at=timezone.now() + timedelta(days=1), location="x", capacity=capacity
    )


@pytest.mark.django_db(transaction=True)
def test_database_is_postgresql(db):
    assert connection.vendor == "postgresql"


@pytest.mark.django_db(transaction=True)
def test_ten_parallel_requests_for_last_seat_yield_one_success(payload):
    event = make_event(1)
    codes = run_parallel(event.id, [{**payload, "email": f"t{i}@example.com"} for i in range(10)])
    assert codes.count(201) == 1
    assert codes.count(409) == 9
    assert Registration.objects.filter(event=event, status="confirmed").count() == 1


@pytest.mark.django_db(transaction=True)
def test_parallel_requests_never_exceed_capacity(payload):
    event = make_event(3)
    codes = run_parallel(event.id, [{**payload, "email": f"t{i}@example.com"} for i in range(12)])
    assert codes.count(201) == 3
    assert Registration.objects.filter(event=event, status="confirmed").count() == 3


@pytest.mark.django_db(transaction=True)
def test_parallel_requests_same_email_yield_one_registration(payload):
    event = make_event(10)
    codes = run_parallel(event.id, [dict(payload) for _ in range(6)])
    assert codes.count(201) == 1
    assert set(codes) <= {201, 409}
    assert Registration.objects.filter(event=event).count() == 1


@pytest.mark.django_db(transaction=True)
def test_parallel_requests_across_events_do_not_block_each_other(payload):
    e1, e2 = make_event(1), make_event(1)
    p1 = {**payload, "email": "one@example.com"}
    p2 = {**payload, "email": "two@example.com"}
    results = {}

    def worker(ev, data):
        results[ev.id] = post(Client(), ev.id, data).status_code
        connection.close()

    ts = [threading.Thread(target=worker, args=(e1, p1)), threading.Thread(target=worker, args=(e2, p2))]
    [t.start() for t in ts]
    [t.join(timeout=30) for t in ts]
    assert results == {e1.id: 201, e2.id: 201}


@pytest.mark.django_db(transaction=True)
def test_seats_remaining_is_zero_after_race_for_last_seat(payload):
    event = make_event(1)
    run_parallel(event.id, [{**payload, "email": f"t{i}@example.com"} for i in range(5)])
    assert Event.objects.with_confirmed_count().get(pk=event.pk).seats_remaining == 0

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Event, Registration


class RegistrationError(Exception):
    """Base class for business-rule failures. `status_code` maps to HTTP."""

    status_code = 409
    message = "ไม่สามารถสมัครได้"

    def __str__(self) -> str:
        return self.message


class EventNotFound(RegistrationError):
    status_code = 404
    message = "ไม่พบ Event"


class EventEnded(RegistrationError):
    message = "Event นี้ผ่านวันจัดไปแล้ว"


class EventFull(RegistrationError):
    message = "ที่นั่งเต็มแล้ว"


class DuplicateRegistration(RegistrationError):
    message = "อีเมลนี้สมัคร Event นี้ไปแล้ว"


def register_attendee(event_id: int, name: str, email: str, phone: str) -> Registration:
    """Create a confirmed Registration, locking the Event row to protect the last Seat."""
    try:
        with transaction.atomic():
            try:
                event = Event.objects.select_for_update().get(pk=event_id)
            except Event.DoesNotExist:
                raise EventNotFound() from None

            now = timezone.now()
            if event.starts_at <= now:
                raise EventEnded()

            confirmed = event.registrations.filter(status=Registration.Status.CONFIRMED)
            if confirmed.filter(email__iexact=email).exists():
                raise DuplicateRegistration()
            if confirmed.count() >= event.capacity:
                raise EventFull()

            return Registration.objects.create(
                event=event, name=name, email=email, phone=phone, consent_at=now
            )
    except IntegrityError:
        # Unique constraint hit (should be rare because the row lock serializes requests)
        raise DuplicateRegistration() from None

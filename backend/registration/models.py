from django.db import models
from django.db.models import Count, Q


class EventQuerySet(models.QuerySet):
    def with_confirmed_count(self) -> "EventQuerySet":
        """Annotate `confirmed_count` so list views avoid N+1 queries."""
        return self.annotate(
            confirmed_count=Count(
                "registrations",
                filter=Q(registrations__status="confirmed"),
            )
        ).order_by("starts_at", "id")


class Event(models.Model):
    name = models.CharField(max_length=200)
    starts_at = models.DateTimeField()
    location = models.CharField(max_length=200)
    capacity = models.PositiveIntegerField()

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ["starts_at", "id"]

    def __str__(self) -> str:
        return self.name

    @property
    def seats_remaining(self) -> int:
        """Capacity minus confirmed Registrations (never below 0)."""
        confirmed = getattr(self, "confirmed_count", None)
        if confirmed is None:
            confirmed = self.registrations.filter(status="confirmed").count()
        return max(self.capacity - confirmed, 0)


class Registration(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=20)
    consent_at = models.DateTimeField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.CONFIRMED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "email"],
                condition=Q(status="confirmed"),
                name="unique_confirmed_email_per_event",
            ),
        ]

    def __str__(self) -> str:
        return f"Registration #{self.pk} ({self.status})"

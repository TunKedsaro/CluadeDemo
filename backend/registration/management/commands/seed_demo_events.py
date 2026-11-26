from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from registration.models import Event

# (name, days from now, location, capacity). Idempotent by Event name.
DEMO_EVENTS = [
    ("Django Workshop", 14, "Bangkok", 30),
    ("Python Meetup", 21, "Chiang Mai", 50),
    ("Web Security Talk", 30, "Online", 100),
    ("Hands-on Lab (limited seats)", 10, "Bangkok", 3),
]


class Command(BaseCommand):
    help = "Create demo Events (idempotent: skips Events whose name already exists)."

    def handle(self, *args, **options) -> None:
        now = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        created = 0
        for name, days, location, capacity in DEMO_EVENTS:
            _, was_created = Event.objects.get_or_create(
                name=name,
                defaults={
                    "starts_at": now + timedelta(days=days),
                    "location": location,
                    "capacity": capacity,
                },
            )
            created += was_created
        self.stdout.write(f"seed_demo_events: {created} created, {len(DEMO_EVENTS) - created} skipped")

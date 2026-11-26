from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Event, Registration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "starts_at", "location", "capacity", "seats_remaining")
    search_fields = ("name", "location")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Event]:
        return super().get_queryset(request).with_confirmed_count()

    @admin.display(description="Seats remaining")
    def seats_remaining(self, obj: Event) -> int:
        return obj.seats_remaining


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "name", "email", "phone", "status", "consent_at", "created_at")
    list_filter = ("event", "status")
    search_fields = ("name", "email")
    readonly_fields = ("consent_at", "created_at")
    actions = ["cancel_selected_registrations"]

    @admin.action(description="Cancel selected registrations")
    def cancel_selected_registrations(
        self, request: HttpRequest, queryset: QuerySet[Registration]
    ) -> None:
        updated = queryset.filter(status=Registration.Status.CONFIRMED).update(
            status=Registration.Status.CANCELLED
        )
        self.message_user(request, f"Cancelled {updated} registration(s).", messages.SUCCESS)

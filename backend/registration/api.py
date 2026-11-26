from django.http import Http404, HttpRequest
from ninja import NinjaAPI

from .models import Event
from .schemas import ErrorOut, EventOut, RegistrationIn, RegistrationOut
from .services import RegistrationError, register_attendee

api = NinjaAPI(title="Event Registration API", docs_url="/docs")


@api.exception_handler(RegistrationError)
def handle_registration_error(request: HttpRequest, exc: RegistrationError):
    return api.create_response(request, {"detail": str(exc)}, status=exc.status_code)


@api.exception_handler(Http404)
def handle_not_found(request: HttpRequest, exc: Http404):
    return api.create_response(request, {"detail": "ไม่พบข้อมูล"}, status=404)


@api.get("/events", response=list[EventOut])
def list_events(request: HttpRequest):
    return Event.objects.with_confirmed_count()


@api.get("/events/{event_id}", response={200: EventOut, 404: ErrorOut})
def get_event(request: HttpRequest, event_id: int):
    event = Event.objects.with_confirmed_count().filter(pk=event_id).first()
    if event is None:
        return 404, {"detail": "ไม่พบ Event"}
    return event


@api.post(
    "/events/{event_id}/registrations",
    response={201: RegistrationOut, 404: ErrorOut, 409: ErrorOut, 429: ErrorOut},
)
def create_registration(request: HttpRequest, event_id: int, payload: RegistrationIn):
    if payload.website:
        # Honeypot filled: reject without explaining why (generic validation-style error)
        body = {"detail": [{"type": "value_error", "loc": ["body"], "msg": "ข้อมูลไม่ถูกต้อง"}]}
        return api.create_response(request, body, status=422)
    registration = register_attendee(
        event_id=event_id, name=payload.name, email=payload.email, phone=payload.phone
    )
    return 201, registration

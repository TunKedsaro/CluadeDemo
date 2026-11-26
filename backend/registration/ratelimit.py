"""Per-IP rate limit for the registration endpoint (fixed window, Django cache).

The IP is only used transiently as a hashed cache key; it is never stored in the
database or logged.
"""
import hashlib
import re

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse

PATH_PATTERN = re.compile(r"^/api/events/\d+/registrations/?$")
UNITS = {"s": 1, "m": 60, "h": 3600}


def parse_rate(rate: str) -> tuple[int, int]:
    count, unit = rate.split("/")
    return int(count), UNITS[unit.strip().lower()]


class RegistrationRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method == "POST" and PATH_PATTERN.match(request.path):
            limit, window = parse_rate(settings.REGISTRATION_RATE_LIMIT)
            ip = request.META.get("REMOTE_ADDR", "")
            key = "reg-rl:" + hashlib.sha256(ip.encode()).hexdigest()
            cache.add(key, 0, timeout=window)
            try:
                attempts = cache.incr(key)
            except ValueError:  # key expired between add and incr
                cache.set(key, 1, timeout=window)
                attempts = 1
            if attempts > limit:
                response = JsonResponse(
                    {"detail": "ส่งคำขอถี่เกินไป กรุณาลองใหม่ภายหลัง"}, status=429
                )
                response["Retry-After"] = str(window)
                return response
        return self.get_response(request)

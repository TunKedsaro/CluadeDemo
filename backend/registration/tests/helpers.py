"""Shared helpers for registration tests (fictional data only)."""


def post(client, event_id, data):
    return client.post(
        f"/api/events/{event_id}/registrations", data, content_type="application/json"
    )

import uuid

import httpx

from app.config import settings


class ServiceUnavailable(Exception):
    pass


class NotFound(Exception):
    pass


class Rejected(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def hold_seats(event_id: uuid.UUID, booking_id: uuid.UUID, seat_labels: list[str]) -> dict:
    try:
        resp = httpx.post(
            f"{settings.EVENT_SERVICE_URL}/internal/events/{event_id}/holds",
            json={"booking_id": str(booking_id), "seat_labels": seat_labels},
            timeout=5,
        )
    except httpx.RequestError as exc:
        raise ServiceUnavailable(f"event-service unreachable: {exc}") from exc
    if resp.status_code == 404:
        raise NotFound(f"Event {event_id} not found")
    if resp.status_code in (409, 422):
        raise Rejected(resp.status_code, resp.json().get("detail", "Seats could not be held"))
    resp.raise_for_status()
    return resp.json()

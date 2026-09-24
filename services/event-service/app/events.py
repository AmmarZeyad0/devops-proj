import logging
import uuid

from app import cache, crud
from app.database import SessionLocal

logger = logging.getLogger("events")


def handle_booking_confirmed(payload: dict) -> None:
    """Payment went through — held seats become SOLD."""
    db = SessionLocal()
    try:
        count = crud.sell_held_seats(db, uuid.UUID(payload["booking_id"]))
        cache.invalidate_seat_map(uuid.UUID(payload["event_id"]))
        logger.info("Booking %s confirmed, %d seat(s) sold", payload["booking_id"], count)
    finally:
        db.close()


def handle_booking_cancelled(payload: dict) -> None:
    """Payment failed or the hold expired — held seats go back on sale."""
    db = SessionLocal()
    try:
        count = crud.release_held_seats(db, uuid.UUID(payload["booking_id"]))
        cache.invalidate_seat_map(uuid.UUID(payload["event_id"]))
        logger.info(
            "Booking %s cancelled (%s), %d seat(s) released",
            payload["booking_id"],
            payload.get("reason"),
            count,
        )
    finally:
        db.close()

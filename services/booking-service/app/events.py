import logging
import uuid

from app import crud, messaging, models
from app.database import SessionLocal

logger = logging.getLogger("events")


def handle_payment_succeeded(payload: dict) -> None:
    booking_id = uuid.UUID(payload["booking_id"])
    db = SessionLocal()
    try:
        booking = crud.finalize(db, booking_id, models.BookingStatus.CONFIRMED)
        if not booking:
            existing = crud.get_booking(db, booking_id)
            if existing and existing.status == models.BookingStatus.EXPIRED:
                logger.warning(
                    "Payment captured for booking %s after it expired — a real system would refund it",
                    booking_id,
                )
            return

        logger.info("Booking %s confirmed", booking_id)
        messaging.publish_event(
            "booking.confirmed",
            {
                "booking_id": str(booking.id),
                "event_id": str(booking.event_id),
                "user_email": booking.user_email,
                "seat_labels": booking.seat_labels,
                "total_amount": str(booking.total_amount),
            },
        )
    finally:
        db.close()


def handle_payment_failed(payload: dict) -> None:
    booking_id = uuid.UUID(payload["booking_id"])
    db = SessionLocal()
    try:
        booking = crud.finalize(
            db, booking_id, models.BookingStatus.CANCELLED, reason=payload.get("reason")
        )
        if not booking:
            return

        logger.info("Booking %s cancelled: %s", booking_id, booking.failure_reason)
        publish_cancelled(booking)
    finally:
        db.close()


def publish_cancelled(booking: models.Booking) -> None:
    messaging.publish_event(
        "booking.cancelled",
        {
            "booking_id": str(booking.id),
            "event_id": str(booking.event_id),
            "user_email": booking.user_email,
            "reason": booking.failure_reason,
        },
    )

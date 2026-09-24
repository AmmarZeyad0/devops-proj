import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app import models


def create_booking(
    db: Session,
    booking_id: uuid.UUID,
    user_id: uuid.UUID,
    user_email: str,
    event_id: uuid.UUID,
    seat_labels: list[str],
    total_amount,
):
    booking = models.Booking(
        id=booking_id,
        user_id=user_id,
        user_email=user_email,
        event_id=event_id,
        seat_labels=seat_labels,
        total_amount=total_amount,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking(db: Session, booking_id: uuid.UUID):
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()


def list_bookings_for_user(db: Session, user_id: uuid.UUID):
    return (
        db.query(models.Booking)
        .filter(models.Booking.user_id == user_id)
        .order_by(models.Booking.created_at.desc())
        .all()
    )


def list_stale_pending_ids(db: Session, older_than: datetime) -> list[uuid.UUID]:
    rows = (
        db.query(models.Booking.id)
        .filter(
            models.Booking.status == models.BookingStatus.PENDING_PAYMENT,
            models.Booking.created_at < older_than,
        )
        .all()
    )
    return [row.id for row in rows]


def finalize(db: Session, booking_id: uuid.UUID, status: models.BookingStatus, reason: str | None = None):
    """Moves a booking out of PENDING_PAYMENT exactly once.

    The payment consumer and the expiry job can race for the same booking. Locking the row and
    only transitioning from PENDING_PAYMENT means whichever gets there first wins, and the other
    gets None back and does nothing.
    """
    booking = (
        db.query(models.Booking)
        .filter(models.Booking.id == booking_id)
        .with_for_update()
        .first()
    )
    if not booking or booking.status != models.BookingStatus.PENDING_PAYMENT:
        db.rollback()
        return None

    booking.status = status
    booking.failure_reason = reason
    db.commit()
    db.refresh(booking)
    return booking

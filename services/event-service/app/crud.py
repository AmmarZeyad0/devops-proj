import string
import uuid

from sqlalchemy.orm import Session

from app import models


class SeatsNotFound(Exception):
    pass


class SeatsUnavailable(Exception):
    def __init__(self, labels: list[str]):
        super().__init__(f"Seats not available: {', '.join(labels)}")
        self.labels = labels


def create_event(db: Session, payload):
    event = models.Event(
        name=payload.name,
        venue=payload.venue,
        starts_at=payload.starts_at,
        seat_price=payload.seat_price,
    )
    db.add(event)
    db.flush()

    for row in string.ascii_uppercase[: payload.rows]:
        for number in range(1, payload.seats_per_row + 1):
            db.add(models.Seat(event_id=event.id, label=f"{row}{number}"))

    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, event_id: uuid.UUID):
    return db.query(models.Event).filter(models.Event.id == event_id).first()


def list_events(db: Session):
    return db.query(models.Event).order_by(models.Event.starts_at).all()


def list_seats(db: Session, event_id: uuid.UUID):
    return (
        db.query(models.Seat)
        .filter(models.Seat.event_id == event_id)
        .order_by(models.Seat.label)
        .all()
    )


def hold_seats(db: Session, event: models.Event, booking_id: uuid.UUID, labels: list[str]):
    """Moves every requested seat from AVAILABLE to HELD, or none of them.

    SELECT ... FOR UPDATE locks the seat rows so two concurrent bookings for the same seat can't
    both succeed — the second one blocks until the first commits, then sees the seat as HELD.
    Locking in a fixed order (by label) keeps two overlapping requests from deadlocking.
    """
    wanted = sorted(set(labels))
    seats = (
        db.query(models.Seat)
        .filter(models.Seat.event_id == event.id, models.Seat.label.in_(wanted))
        .order_by(models.Seat.label)
        .with_for_update()
        .all()
    )

    if len(seats) != len(wanted):
        db.rollback()
        missing = set(wanted) - {s.label for s in seats}
        raise SeatsNotFound(f"Unknown seats: {', '.join(sorted(missing))}")

    taken = [s.label for s in seats if s.status != models.SeatStatus.AVAILABLE]
    if taken:
        db.rollback()
        raise SeatsUnavailable(taken)

    for seat in seats:
        seat.status = models.SeatStatus.HELD
        seat.booking_id = booking_id

    db.commit()
    return wanted


def sell_held_seats(db: Session, booking_id: uuid.UUID) -> int:
    count = (
        db.query(models.Seat)
        .filter(models.Seat.booking_id == booking_id, models.Seat.status == models.SeatStatus.HELD)
        .update({models.Seat.status: models.SeatStatus.SOLD}, synchronize_session=False)
    )
    db.commit()
    return count


def release_held_seats(db: Session, booking_id: uuid.UUID) -> int:
    """Only HELD seats go back on sale — a seat that's already SOLD is never released."""
    count = (
        db.query(models.Seat)
        .filter(models.Seat.booking_id == booking_id, models.Seat.status == models.SeatStatus.HELD)
        .update(
            {models.Seat.status: models.SeatStatus.AVAILABLE, models.Seat.booking_id: None},
            synchronize_session=False,
        )
    )
    db.commit()
    return count

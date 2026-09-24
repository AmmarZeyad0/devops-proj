import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import cache, crud, schemas
from app.database import get_db

router = APIRouter(prefix="/internal/events", tags=["internal"])


@router.post("/{event_id}/holds", response_model=schemas.HoldResponse, status_code=201)
def hold_seats(event_id: uuid.UUID, payload: schemas.HoldRequest, db: Session = Depends(get_db)):
    """Called by booking-service (never by clients) to hold seats while a booking is being paid for."""
    event = crud.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    try:
        labels = crud.hold_seats(db, event, payload.booking_id, payload.seat_labels)
    except crud.SeatsNotFound as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except crud.SeatsUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    cache.invalidate_seat_map(event_id)

    unit_price = Decimal(event.seat_price)
    return schemas.HoldResponse(
        event_id=event_id,
        booking_id=payload.booking_id,
        seat_labels=labels,
        unit_price=unit_price,
        total_amount=unit_price * len(labels),
    )

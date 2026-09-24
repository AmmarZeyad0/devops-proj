import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import cache, crud, schemas
from app.database import get_db
from app.models import SeatStatus

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[schemas.EventOut])
def list_events(db: Session = Depends(get_db)):
    return crud.list_events(db)


@router.post("", response_model=schemas.EventOut, status_code=201)
def create_event(payload: schemas.EventCreate, db: Session = Depends(get_db)):
    return crud.create_event(db, payload)


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(event_id: uuid.UUID, db: Session = Depends(get_db)):
    event = crud.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/{event_id}/seats", response_model=schemas.SeatMap)
def get_seat_map(event_id: uuid.UUID, db: Session = Depends(get_db)):
    """The hottest read path when an event goes on sale — served from Redis when possible."""
    cached = cache.get_cached_seat_map(event_id)
    if cached:
        return cached

    if not crud.get_event(db, event_id):
        raise HTTPException(status_code=404, detail="Event not found")

    seats = crud.list_seats(db, event_id)
    result = schemas.SeatMap(
        event_id=event_id,
        available=sum(1 for s in seats if s.status == SeatStatus.AVAILABLE),
        held=sum(1 for s in seats if s.status == SeatStatus.HELD),
        sold=sum(1 for s in seats if s.status == SeatStatus.SOLD),
        seats=[schemas.SeatOut.model_validate(s) for s in seats],
    )
    cache.cache_seat_map(event_id, result.model_dump())
    return result

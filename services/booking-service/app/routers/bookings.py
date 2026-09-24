import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app import clients, crud, messaging, schemas, security
from app.database import get_db

router = APIRouter(prefix="/bookings", tags=["bookings"])


def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return security.decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("", response_model=schemas.BookingOut, status_code=201)
def create_booking(
    payload: schemas.BookingCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    booking_id = uuid.uuid4()

    try:
        hold = clients.hold_seats(payload.event_id, booking_id, payload.seat_labels)
    except clients.NotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    except clients.Rejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    except clients.ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    booking = crud.create_booking(
        db,
        booking_id=booking_id,
        user_id=uuid.UUID(user["id"]),
        user_email=user["email"],
        event_id=payload.event_id,
        seat_labels=hold["seat_labels"],
        total_amount=hold["total_amount"],
    )

    messaging.publish_event(
        "booking.created",
        {
            "booking_id": str(booking.id),
            "user_id": str(booking.user_id),
            "amount": str(booking.total_amount),
        },
    )

    return booking


@router.get("", response_model=list[schemas.BookingOut])
def list_my_bookings(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.list_bookings_for_user(db, uuid.UUID(user["id"]))


@router.get("/{booking_id}", response_model=schemas.BookingOut)
def read_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    booking = crud.get_booking(db, booking_id)
    if not booking or str(booking.user_id) != user["id"]:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import SeatStatus


class EventCreate(BaseModel):
    name: str
    venue: str
    starts_at: datetime
    seat_price: Decimal = Field(gt=0)
    rows: int = Field(ge=1, le=26, description="Rows are labelled A, B, C, ...")
    seats_per_row: int = Field(ge=1, le=50)


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    venue: str
    starts_at: datetime
    seat_price: Decimal
    created_at: datetime


class SeatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    status: SeatStatus


class SeatMap(BaseModel):
    event_id: uuid.UUID
    available: int
    held: int
    sold: int
    seats: list[SeatOut]


class HoldRequest(BaseModel):
    booking_id: uuid.UUID
    seat_labels: list[str] = Field(min_length=1, max_length=10)


class HoldResponse(BaseModel):
    event_id: uuid.UUID
    booking_id: uuid.UUID
    seat_labels: list[str]
    unit_price: Decimal
    total_amount: Decimal

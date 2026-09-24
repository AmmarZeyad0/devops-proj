import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import BookingStatus


class BookingCreate(BaseModel):
    event_id: uuid.UUID
    seat_labels: list[str] = Field(min_length=1, max_length=10)


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    event_id: uuid.UUID
    seat_labels: list[str]
    total_amount: Decimal
    status: BookingStatus
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.database import Base


class BookingStatus(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_email = Column(String, nullable=False)
    event_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    seat_labels = Column(ARRAY(String), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING_PAYMENT)
    failure_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

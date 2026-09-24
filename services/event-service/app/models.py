import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class SeatStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    SOLD = "SOLD"


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    venue = Column(String, nullable=False)
    starts_at = Column(DateTime, nullable=False)
    seat_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    seats = relationship("Seat", back_populates="event", cascade="all, delete-orphan")


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("event_id", "label", name="uq_seat_event_label"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    label = Column(String, nullable=False)
    status = Column(Enum(SeatStatus), nullable=False, default=SeatStatus.AVAILABLE)
    booking_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    event = relationship("Event", back_populates="seats")

import logging

from fastapi import FastAPI

from app import events, messaging
from app.database import Base, engine
from app.routers import bookings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Booking Service", version="0.1.0")

app.include_router(bookings.router)

_EVENT_HANDLERS = {
    "payment.succeeded": events.handle_payment_succeeded,
    "payment.failed": events.handle_payment_failed,
}


@app.on_event("startup")
def startup():
    for routing_key, handler in _EVENT_HANDLERS.items():
        messaging.start_consumer(
            queue_name=f"booking_service.{routing_key.replace('.', '_')}",
            routing_key=routing_key,
            on_message=handler,
        )


@app.get("/health")
def health():
    return {"status": "ok", "service": "booking-service"}

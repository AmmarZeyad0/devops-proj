import logging

from fastapi import FastAPI

from app import events, messaging
from app.database import Base, engine
from app.routers import events as events_router
from app.routers import internal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Service", version="0.1.0")

app.include_router(events_router.router)
app.include_router(internal.router)

_EVENT_HANDLERS = {
    "booking.confirmed": events.handle_booking_confirmed,
    "booking.cancelled": events.handle_booking_cancelled,
}


@app.on_event("startup")
def startup():
    for routing_key, handler in _EVENT_HANDLERS.items():
        messaging.start_consumer(
            queue_name=f"event_service.{routing_key.replace('.', '_')}",
            routing_key=routing_key,
            on_message=handler,
        )


@app.get("/health")
def health():
    return {"status": "ok", "service": "event-service"}

"""One-shot job: expire bookings that have sat in PENDING_PAYMENT too long and release their seats.

This is not part of the web server — it runs, does one pass, and exits:

    python -m app.jobs.expire_bookings

Something external has to run it on a schedule (cron locally, a Kubernetes CronJob later). It's
the safety net for when payment-worker is down or slow: without it, seats held by abandoned
bookings would never go back on sale.
"""

import logging
from datetime import datetime, timedelta

from app import crud, events, models
from app.config import settings
from app.database import Base, SessionLocal, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("expire_bookings")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    cutoff = datetime.utcnow() - timedelta(minutes=settings.HOLD_TIMEOUT_MINUTES)

    db = SessionLocal()
    try:
        stale_ids = crud.list_stale_pending_ids(db, cutoff)
        expired = 0
        for booking_id in stale_ids:
            booking = crud.finalize(
                db,
                booking_id,
                models.BookingStatus.EXPIRED,
                reason=f"Payment not completed within {settings.HOLD_TIMEOUT_MINUTES} minutes",
            )
            if booking:
                events.publish_cancelled(booking)
                expired += 1
        logger.info("Expired %d of %d stale booking(s)", expired, len(stale_ids))
    finally:
        db.close()


if __name__ == "__main__":
    main()

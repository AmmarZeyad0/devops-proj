import logging
import random
import time

from app import messaging
from app.config import settings

logger = logging.getLogger("processor")


def process_payment(channel, payload: dict) -> None:
    """Simulates charging the customer through a payment gateway for a `booking.created` event."""
    booking_id = payload["booking_id"]
    logger.info("Charging %s for booking %s", payload["amount"], booking_id)

    time.sleep(settings.PAYMENT_PROCESSING_SECONDS)

    if random.random() < settings.PAYMENT_FAILURE_RATE:
        logger.info("Payment declined for booking %s", booking_id)
        messaging.publish_event(
            channel, "payment.failed", {"booking_id": booking_id, "reason": "Card declined"}
        )
        return

    logger.info("Payment succeeded for booking %s", booking_id)
    messaging.publish_event(
        channel, "payment.succeeded", {"booking_id": booking_id, "amount": payload["amount"]}
    )

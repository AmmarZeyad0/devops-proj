import logging

logger = logging.getLogger("notify")


def send_ticket(channel, payload: dict) -> None:
    """Simulates emailing the customer their tickets once a booking is confirmed."""
    logger.info(
        "[email -> %s] Your tickets for booking %s: seats %s (total %s)",
        payload["user_email"],
        payload["booking_id"],
        ", ".join(payload["seat_labels"]),
        payload["total_amount"],
    )


def send_cancellation(channel, payload: dict) -> None:
    """Simulates emailing the customer that their booking didn't go through."""
    logger.info(
        "[email -> %s] Booking %s was cancelled: %s",
        payload["user_email"],
        payload["booking_id"],
        payload.get("reason") or "no reason given",
    )

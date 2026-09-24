import logging

from app import messaging, notify

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main():
    messaging.run_consumer(
        queue_name="notification_worker.bookings",
        handlers={
            "booking.confirmed": notify.send_ticket,
            "booking.cancelled": notify.send_cancellation,
        },
    )


if __name__ == "__main__":
    main()

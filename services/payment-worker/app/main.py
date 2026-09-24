import logging

from app import messaging, processor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main():
    messaging.run_consumer(
        queue_name="payment_worker.booking_created",
        handlers={"booking.created": processor.process_payment},
    )


if __name__ == "__main__":
    main()

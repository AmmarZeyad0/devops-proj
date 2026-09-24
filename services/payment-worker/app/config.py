import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    PAYMENT_FAILURE_RATE: float = float(os.getenv("PAYMENT_FAILURE_RATE", "0.2"))
    PAYMENT_PROCESSING_SECONDS: float = float(os.getenv("PAYMENT_PROCESSING_SECONDS", "2"))


settings = Settings()

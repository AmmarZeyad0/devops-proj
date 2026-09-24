import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bookings_db"
    )
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    EVENT_SERVICE_URL: str = os.getenv("EVENT_SERVICE_URL", "http://localhost:8002")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    HOLD_TIMEOUT_MINUTES: int = int(os.getenv("HOLD_TIMEOUT_MINUTES", "10"))
    PORT: int = int(os.getenv("PORT", "8003"))


settings = Settings()

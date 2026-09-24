import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/events_db"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "30"))
    PORT: int = int(os.getenv("PORT", "8002"))


settings = Settings()

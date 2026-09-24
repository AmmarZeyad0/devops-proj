from jose import jwt

from app.config import settings


def decode_access_token(token: str) -> dict:
    """Tokens are issued by auth-service. booking-service only verifies them, using the same shared secret."""
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return {"id": payload["sub"], "email": payload["email"]}

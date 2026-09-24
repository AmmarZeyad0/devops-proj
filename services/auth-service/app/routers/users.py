import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db

router = APIRouter(prefix="/users", tags=["users"])


def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        user_id = security.decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = crud.get_user_by_id(db, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/me", response_model=schemas.UserOut)
def read_me(current_user=Depends(get_current_user)):
    return current_user

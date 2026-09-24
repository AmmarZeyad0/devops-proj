import uuid

from sqlalchemy.orm import Session

from app import models, security


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: uuid.UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, email: str, password: str, full_name: str):
    user = models.User(
        email=email,
        hashed_password=security.hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

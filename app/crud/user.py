from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.models import User
from app.utils.serializer import object_to_dict


def get_users_by_username(db: Session, username: str):
    stmt = select(User).where(User.username == username)
    return db.scalars(stmt).all()


def create_user(db: Session, github_id: int, username: str, avatar_url: str) -> User:
    user = User(
        github_id=github_id,
        username=username,
        avatar_url=avatar_url
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: str):
    stmt = select(User).where(User.id == user_id)
    return db.scalars(stmt).one()


def get_user_by_username(db: Session, username: str):
    stmt = select(User).where(User.username == username)
    user = db.scalars(stmt).one()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    user_obj = object_to_dict(user)

    return user_obj

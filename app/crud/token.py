from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.models import Token
from app.utils.serializer import object_to_dict


def create_token(db: Session, name: str, token: str, user_id: str) -> Token:
    token_obj = Token(
        name=name,
        token=token,
        user_id=user_id
    )
    db.add(token_obj)
    db.commit()
    db.refresh(token_obj)
    return token_obj


def find_token_by_token(token: str, user_id: str, name: str, db: Session):
    stmt = select(Token).where(Token.name == name, Token.user_id == user_id, Token.token == token)
    token = db.scalars(stmt).one_or_none()
    return object_to_dict(token)

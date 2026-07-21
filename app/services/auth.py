from dotenv import load_dotenv
from fastapi import HTTPException, status, Request
import os
import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from http.cookies import SimpleCookie

from app.crud import token as token_crud

load_dotenv()


def generate_tokens(name: str, id: str, username: str, db: Session, expires_time: timedelta | None = None,):
    if expires_time:
        expires_at = datetime.now(timezone.utc) + expires_time
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    data = {
        "id": id,
        "username": username,
        "exp": expires_at
    }
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm="HS256")

    token_crud.create_token(db, name, encoded_jwt, id)

    return {
        "token": encoded_jwt,
        "expires_at": expires_at
    }


def extract_cookies(request: Request):
    cookies = request.headers.get("cookie")

    cookie = SimpleCookie()
    cookie.load(cookies)

    access_token = cookie.get("access_token")
    github_access_token = cookie.get("github_access_token")
    refresh_token = cookie.get("refresh_token")

    access_token = access_token.value if access_token else None
    github_access_token = github_access_token.value if github_access_token else None
    refresh_token = refresh_token.value if refresh_token else None

    return {
        "access_token": access_token,
        "github_access_token": github_access_token,
        "refresh_token": refresh_token,
    }


def refresh_access_token(refresh_token: str, db: Session) -> str:
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])

        print("payload", payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid refresh token")

    is_valid_token = token_crud.find_token_by_token(refresh_token, payload['id'], "refresh_token", db)

    if not is_valid_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid refresh token")

    access_token = generate_tokens("access_token", payload['id'], payload['username'], db, timedelta(minutes=15))

    return access_token

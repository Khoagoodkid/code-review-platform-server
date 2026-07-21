import os
import jwt
from dotenv import load_dotenv
from fastapi import Request, HTTPException, status

from app.services.auth import extract_cookies

load_dotenv()


async def get_user(request: Request):

    access_token = extract_cookies(request)["access_token"]
    github_access_token = extract_cookies(request)["github_access_token"]

    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Can't find access token")

    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])

        print("payload", payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    payload["github_access_token"] = github_access_token

    return payload

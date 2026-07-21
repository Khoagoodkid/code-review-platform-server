import os
from datetime import timedelta
from urllib.parse import urlencode

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Request, HTTPException, status, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_user
from app.crud import user as user_crud
from app.db.session import get_db
from app.services.auth import extract_cookies, generate_tokens, refresh_access_token
from app.services.github import exchange_code, get_user_info
from app.utils.serializer import object_to_dict

load_dotenv()

router = APIRouter()


@router.get("/login")
def login():
    client_id = os.getenv("CLIENT_ID")
    params = {
        "client_id": client_id,
        "scope": "repo admin:repo_hook",
        "prompt": "consent",
    }

    redirect_url = (
        "https://github.com/login/oauth/authorize?"
        + urlencode(params)
    )
    return RedirectResponse(redirect_url)


@router.get("/auth_callback")
async def login_callback(code: str = None, db: Session = Depends(get_db)):
    if not code:
        return RedirectResponse(os.getenv("FRONTEND_URL") + "/login")


    token_data = await exchange_code(code)
    if "access_token" in token_data:
        github_access_token = token_data["access_token"]
        user_info = await get_user_info(github_access_token)
        username = user_info["login"]

        users = user_crud.get_users_by_username(db, username)

        if len(users) == 0:
            user = user_crud.create_user(
                db,
                github_id=user_info["id"],
                username=username,
                avatar_url=user_info["avatar_url"]
            )
        else:
            user = users[0]
        access_token = generate_tokens("access_token", str(user.id), user.username, db, timedelta(minutes=10))
        refresh_token = generate_tokens("refresh_token", str(user.id), user.username, db, timedelta(minutes=60))

        response = RedirectResponse(os.getenv("FRONTEND_URL") + "/user")

        response.set_cookie(
            key="github_access_token",
            value=github_access_token,
            expires=refresh_token["expires_at"],
            httponly=True,
            secure=False
        )
        response.set_cookie(
            key="access_token",
            value=access_token["token"],
            expires=access_token["expires_at"],
            httponly=True,
            secure=False
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token["token"],
            expires=refresh_token["expires_at"],
            httponly=True,
            secure=False
        )

        return response
    else:
        return RedirectResponse(os.getenv("FRONTEND_URL") + "/login")

@router.get("/me")
def getMe(db: Session = Depends(get_db), user=Depends(get_user)):
    user = user_crud.get_user_by_id(db, user['id'])

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    user_obj = object_to_dict(user)
    return user_obj


@router.post("/auth/refresh-token")
def refresh_token(request: Request, response: Response, db=Depends(get_db)):
    refresh_token = extract_cookies(request)['refresh_token']

    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can't find refresh token")
    access_token = refresh_access_token(refresh_token, db)

    response.set_cookie(
        key="access_token",
        value=access_token['token'],
        expires=access_token['expires_at'],
        samesite=None,
        httponly=True,
        secure=False
    )

    return {"message": "Successfully refreshed token"}


@router.post('/logout')
def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    response.delete_cookie(key="github_access_token")

    return {"message": "Successfully logged out"}

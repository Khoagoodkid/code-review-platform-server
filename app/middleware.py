from app.main import app
from fastapi import Request, HTTPException, status
from dotenv import load_dotenv
import os
import jwt

load_dotenv()

@app.middleware("http")
async def get_user(request: Request, call_next):
    access_token = request.headers.get("access_token")
    print(access_token)

    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])
        request.state.user = payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    response = await call_next(request)

    return response

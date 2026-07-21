import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, pull_requests, repos, review_feedback, root, webhooks
from app.services.socket import sio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root.router)
app.include_router(auth.router)
app.include_router(repos.router)
app.include_router(webhooks.router)
app.include_router(pull_requests.router)
app.include_router(review_feedback.router)


@app.get("/socket")
def socket_health():
    return {"message": "FastAPI works"}


socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path="socket.io",
)

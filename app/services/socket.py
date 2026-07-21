import socketio

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)

socket_ids = {}

@sio.event
async def connect(sid, environ):
    print("connected:", sid)
    await sio.emit("message", {"data": "Welcome!"}, to=sid)

@sio.event
async def register_user(sid, data):
    socket_ids[data["username"]] = sid
    print("registered user:", data["username"], "with sid:", sid)

@sio.event
async def disconnect(sid):
    print("disconnected:", sid)
    for username, socket_id in socket_ids.items():
        if socket_id == sid:
            del socket_ids[username]
            break

async def send_pr_update_signal(owner: str, repo_name: str, pull_number: int):
    print("sending pr update signal to", owner, "for", repo_name, "pull number", pull_number)
    if owner not in socket_ids:
        return

    print("sending pr update signal to", socket_ids[owner])
    await sio.emit("pr_update", {
        "repo_name": repo_name,
        "pull_number": pull_number,
    }, to=socket_ids[owner])


async def send_pr_merge_signal(owner: str, repo_name: str, pull_number: int):
    print("sending pr merge signal to", owner, "for", repo_name, "pull number", pull_number)
    if owner not in socket_ids:
        return

    print("sending pr merge signal to", socket_ids[owner])
    await sio.emit("pr_merge", {
        "repo_name": repo_name,
        "pull_number": pull_number,
    }, to=socket_ids[owner])
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.crud import pull_request as pull_request_crud
from app.db.session import get_db
from app.services.github import validate_webhook
from app.services.pull_request import create_pr_row
from app.services.socket import send_pr_update_signal, send_pr_merge_signal
from app.services import repo_index
router = APIRouter()


@router.post('/repos/webhook')
async def receive_repo_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    is_valid = await validate_webhook(request)
    print("Receive webhook:", payload)

    if not is_valid or 'action' not in payload:
        return

    action = payload['action']
    if action == 'closed':
        pull_request_crud.close_pr(str(payload["pull_request"]["id"]), db)
        is_merged = payload["pull_request"]["merged"]
        if is_merged:
            await send_pr_merge_signal(payload["pull_request"]["user"]["login"], payload["pull_request"]["head"]["repo"]["name"], payload["pull_request"]["number"])
        return

    if action == 'synchronize':
        await send_pr_update_signal(payload["pull_request"]["user"]["login"], payload["pull_request"]["head"]["repo"]["name"], payload["pull_request"]["number"])
        return


    if payload["action"] != 'opened':
        return


    username = payload["pull_request"]["user"]["login"]
    repo_name = payload["pull_request"]["head"]["repo"]["name"]
    status = payload["pull_request"]["state"]
    title = payload["pull_request"]["title"]
    body = payload["pull_request"]["body"]
    url = payload["pull_request"]["url"]
    pr_id = str(payload["pull_request"]["id"])

    create_pr_row(username, repo_name, payload['number'], status, title, body, url, pr_id, db)

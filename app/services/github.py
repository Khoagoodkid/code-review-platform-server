from dotenv import load_dotenv
from fastapi import Request, HTTPException, status
import os
import httpx
import hmac
import hashlib
from app.crud import added_repo as added_repo_crud
import base64

load_dotenv()


async def exchange_code(code: str):
    payload = {
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data=payload,
            headers={
                "Accept": "application/json"
            }
        )

    response.raise_for_status()

    return response.json()


async def get_user_info(access_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            }
        )

        print(response.headers)

    response.raise_for_status()

    return response.json()


async def get_user_repos(github_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/repos",
             headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
            }
        )
        print(response)

    response.raise_for_status()

    return response.json()


async def create_repo_webhook(owner: str, repo_name: str, github_token: str, user_id: str, db):
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    payload = {
        "name": "web",
        "active": True,
        "events": ["pull_request"],
        "config": {
            "url": os.getenv("BASE_URL") + "/repos/webhook",
            "content_type": "json",
            "insecure_ssl": "1",
            "secret": secret
        },
    }

    print(payload)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.github.com/repos/{owner}/{repo_name}/hooks",
            json=payload,
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
            }
        )

    response.raise_for_status()
    response = response.json()
    added_repo_crud.create_repo_row(repo_name, user_id, str(response['id']), db)

    from app.services import repo_index

    try:
        await repo_index.build_repo_index(user_id, owner, repo_name, github_token, db)
        db.commit()
    except Exception as e:
        db.rollback()
        print("ERROR:", repr(e))
        raise
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong when add repo")
   

async def remove_repo_webhook(owner: str, repo_name: str, webhook_id: str, github_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"https://api.github.com/repos/{owner}/{repo_name}/hooks/{webhook_id}",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
            }
        )

    response.raise_for_status()

async def validate_webhook(request: Request) -> bool:
    body = await request.body()
    github_signature = request.headers.get(
        "X-Hub-Signature-256"
    )

    secret = os.getenv("GITHUB_WEBHOOK_SECRET")

    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        github_signature,
        expected_signature
    ):
        return False

    return True


async def get_pr_files(owner: str, repo_name: str, pull_number: int, github_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pull_number}/files",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
            }
        )

    response.raise_for_status()

    return response.json()

async def get_raw_file_content(url: str, github_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
            }
        )

    response.raise_for_status()

    data = response.json()

    content = base64.b64decode(data["content"]).decode("utf-8")

    return content
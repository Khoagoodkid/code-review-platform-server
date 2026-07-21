import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_user
from app.crud import added_repo as added_repo_crud
from app.crud import repo_index as repo_index_crud
from app.db.session import get_db
from app.schemas.repos import WebhookConfig
from app.services.github import create_repo_webhook, get_user_repos, remove_repo_webhook

load_dotenv()

router = APIRouter()


@router.get('/repos')
async def getRepos(user=Depends(get_user)):
    repos = await get_user_repos(user["github_access_token"])
    return repos


@router.get("/added-repos")
def get_added_repos(user=Depends(get_user), db: Session=Depends(get_db)):
    repos = added_repo_crud.get_added_repos_list(user['id'], db)
    return repos

@router.delete("/added-repos")
async def remove_added_repo(repo_name: str, user=Depends(get_user), db: Session=Depends(get_db)):
    
    repo = added_repo_crud.get_added_repo_by_filter(repo_name, user['id'], db)
    # remove webhook
    await remove_repo_webhook(user['username'], repo_name, repo['webhook_id'], user['github_access_token'])
    try:

        added_repo_crud.remove_repo_row(repo_name, user['id'], db)
        repo_index_crud.delete_repo_index(repo_name, user['id'], db)
        db.commit()
    except Exception as e:
        db.rollback()
        print("ERROR:", repr(e))
        raise
    



@router.post('/repos/webhook-config')
async def add_repo_webhook(body: WebhookConfig, user=Depends(get_user), db=Depends(get_db)):
    await create_repo_webhook(user['username'], body.model_dump()['repo_name'], user['github_access_token'], user['id'], db)
        
    return {"message": "Successfully add repo"}

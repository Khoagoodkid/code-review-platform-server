from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_user
from app.crud import pull_request as pull_request_crud
from app.crud import review_feedback as review_feedback_crud
from app.db.session import get_db
from app.services.github import get_pr_files
from app.services.pull_request import review_pr
from app.services.repo_index import update_repo_index
import json


router = APIRouter()


@router.get("/pr")
async def get_all_pr(repo_name: str, user=Depends(get_user), db=Depends(get_db)):
    prs = pull_request_crud.get_pr_list(user["id"], repo_name, db)
    return prs

@router.get("/pr/{repo_name}/{pull_number}")
async def get_pr_details(repo_name: str, pull_number: int, user=Depends(get_user), db=Depends(get_db)):
    detail = pull_request_crud.get_pr_details(user["id"], repo_name, pull_number, db)
    if not detail:
        raise HTTPException(status_code=404, detail="PR not found")

    if detail["review"] is not None:
        detail["review"] = json.loads(detail["review"])
    detail["is_already_feedback"] = review_feedback_crud.get_review_feedback_by_review_trace_id(user["id"], detail["review_trace_id"], db) is not None
    return detail

@router.get("/pr/files")
async def get_pr_content(repo_name: str, pull_number: int, user=Depends(get_user)):
    files = await get_pr_files(user['username'], repo_name, pull_number, user['github_access_token'])
    return files

@router.get('/pr/review')
async def get_pr_review(repo_name: str, pull_number: int, user=Depends(get_user), db=Depends(get_db)):
    review = await review_pr(user['id'], user['username'], repo_name, pull_number, user['github_access_token'], db)
    return review


from pydantic import BaseModel


class MergePrRequest(BaseModel):
    repo_name: str
    pull_number: int


@router.post('/pr/merge') 
async def merge_pr(request: MergePrRequest, user=Depends(get_user), db=Depends(get_db)):
    await update_repo_index(user['id'], user['username'], request.repo_name, request.pull_number, user['github_access_token'], db)
    return {"message": "PR merged"}
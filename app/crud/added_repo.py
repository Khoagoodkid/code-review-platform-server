from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.models import AddedRepo
from app.utils.serializer import object_to_dict


def get_added_repos_list(user_id: str, db: Session):
    stmt = select(AddedRepo).where(AddedRepo.user_id == user_id)
    added_repos = db.scalars(stmt).all()
    return added_repos


def create_repo_row(repo_name: str, user_id: str, webhook_id: str,  db: Session) -> AddedRepo:
    repo = AddedRepo(
        repo_name=repo_name,
        user_id=user_id,
        webhook_id=webhook_id
    )
    db.add(repo)
    # db.commit()
    # db.refresh(repo)
    return repo

def remove_repo_row(repo_name: str, user_id: str, db: Session):
    stmt = delete(AddedRepo).where(AddedRepo.repo_name == repo_name, AddedRepo.user_id == user_id)
    
    db.execute(stmt)
    
def get_added_repo_by_filter(repo_name: str, user_id: str, db: Session):
    stmt = select(AddedRepo).where(AddedRepo.repo_name == repo_name, AddedRepo.user_id == user_id)
    repo = db.scalars(stmt).one_or_none()
    
    return object_to_dict(repo)
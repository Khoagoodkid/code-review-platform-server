from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.models.models import PullRequest

from app.utils.serializer import object_to_dict
def create_pr_row(user_id: str, repo_name: str, number: int, status: str, title: str, body: str, url: str, pr_id: str, db: Session) -> PullRequest:
    pr = PullRequest(
        user_id=user_id,
        number=number,
        repo_name=repo_name,
        status=status,
        title=title,
        body=body,
        url=url,
        pr_id=pr_id
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


def close_pr(pr_id: str, db: Session):
    stmt = update(PullRequest).where(PullRequest.pr_id == pr_id).values(status="closed").returning(PullRequest)
    updated_pr = db.scalars(stmt).one_or_none()
    db.commit()
    return updated_pr


def get_pr_list(user_id: str, repo_name: str, db: Session):
    stmt = select(PullRequest).where(
        PullRequest.user_id == user_id, PullRequest.repo_name == repo_name
    )
    prs = db.scalars(stmt).all()
    return prs

def save_ai_review(user_id: str, repo_name: str, number: int, review: str, review_trace_id: str, db: Session):
    stmt = update(PullRequest).where(PullRequest.user_id == user_id, PullRequest.repo_name == repo_name, PullRequest.number == number).values(review=review, review_trace_id=review_trace_id)
    db.execute(stmt)
    db.commit()
    return True

def get_pr_details(user_id: str, repo_name: str, number: int, db: Session):
    stmt = select(PullRequest).where(PullRequest.user_id == user_id, PullRequest.repo_name == repo_name, PullRequest.number == number)
    pr = db.scalars(stmt).one_or_none()
    return object_to_dict(pr)
from app.api.deps import get_user
from app.db.session import get_db
from fastapi import Depends, APIRouter
from app.crud import review_feedback as review_feedback_crud
from pydantic import BaseModel

router = APIRouter()


class CreateReviewFeedbackRequest(BaseModel):
    total_files_changed: int
    total_lines_added: int
    total_lines_deleted: int
    total_delta: float
    max_delta: float
    avg_delta: float
    changed_func_count: int
    high_delta_count: int
    risk_label: str
    review_trace_id: str
    feedback: int



@router.post("/review-feedback")
def create_review_feedback(request: CreateReviewFeedbackRequest, user=Depends(get_user), db=Depends(get_db)):
    review_feedback = review_feedback_crud.create_review_feedback(user['id'], request.total_files_changed, request.total_lines_added, request.total_lines_deleted, request.total_delta, request.max_delta, request.avg_delta, request.changed_func_count, request.high_delta_count, request.risk_label, request.feedback, request.review_trace_id, db)
    return review_feedback
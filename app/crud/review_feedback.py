from app.models.models import ReviewFeedback
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.utils import object_to_dict


def create_review_feedback(user_id: str, total_files_changed: int, total_lines_added: int, total_lines_deleted: int, total_delta: int, max_delta: int, avg_delta: int, changed_func_count: int, high_delta_count: int, risk_label: str, feedback: int, review_trace_id: str, db: Session):    

    review_feedback = ReviewFeedback(
        total_files_changed=total_files_changed,
        total_lines_added=total_lines_added,
        total_lines_deleted=total_lines_deleted,
        total_delta=total_delta,
        max_delta=max_delta,
        avg_delta=avg_delta,
        changed_func_count=changed_func_count,
        high_delta_count=high_delta_count,
        risk_label=risk_label,
        feedback=feedback,
        review_trace_id=review_trace_id,
        is_trained=False,
        user_id=user_id,
    )

    db.add(review_feedback)
    db.commit()
    db.refresh(review_feedback)
    return review_feedback

def get_review_feedback_by_review_trace_id(user_id: str, review_trace_id: str, db: Session):
    stmt = select(ReviewFeedback).where(ReviewFeedback.user_id == user_id, ReviewFeedback.review_trace_id == review_trace_id)
    review_feedback = db.scalars(stmt).one_or_none()
    return object_to_dict(review_feedback)
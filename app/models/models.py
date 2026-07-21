from sqlalchemy import Column, Integer, String, DateTime, Index, Boolean, Float
from sqlalchemy.sql import func
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4, unique=True)
    github_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False, unique=True)
    avatar_url = Column(String, nullable=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Token(Base):
    __tablename__ = "tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    token = Column(String, nullable=False, index = True, unique= True)
    name = Column(String, nullable= False)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class AddedRepo(Base):
    __tablename__ = "added_repos"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    repo_name=  Column(String, nullable= False)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    webhook_id = Column(String, nullable= False)
    __table_args__ = (
        UniqueConstraint("user_id", "repo_name", name="uq_user_service_pair"),
    )
    
class PullRequest(Base):
    __tablename__ = "pull_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    repo_name=  Column(String, nullable= False)
    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index = True)
    number = Column(Integer, nullable=False)
    status = Column(String, nullable= False)
    title = Column(String, nullable= False)
    body = Column(String, nullable=True)
    url = Column(String, nullable= False)
    pr_id = Column(String, nullable=False)
    review = Column(JSONB, nullable=True)
    review_trace_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class RepoIndex(Base):
    __tablename__ = "repo_index"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    code= Column(String, nullable=False)
    symbol= Column(String, nullable=False)
    file_path= Column(String, nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    imports = Column(ARRAY(String))
    calls = Column(ARRAY(String))
    repo_name = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index('idx_symbol_repo_name_user_id', 'symbol', 'repo_name', 'user_id'),
        UniqueConstraint("user_id", "repo_name", "symbol", name="uq_user_service_pair_symbol"),
    )

class ReviewFeedback(Base):
    __tablename__ = "review_feedback"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    total_files_changed = Column(Integer, nullable=False)
    total_lines_added = Column(Integer, nullable=False)
    total_lines_deleted = Column(Integer, nullable=False)
    total_delta = Column(Float, nullable=False)
    max_delta = Column(Float, nullable=False)
    avg_delta = Column(Float, nullable=False)
    changed_func_count = Column(Integer, nullable=False)
    high_delta_count = Column(Integer, nullable=False)
    risk_label = Column(String, nullable=False)
    feedback = Column(Integer, nullable=False, default= 0)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    review_trace_id = Column(String, nullable=False)
    is_trained = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
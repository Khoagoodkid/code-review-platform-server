from sqlalchemy.orm import Session
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from app.models.models import RepoIndex
from app.utils.serializer import object_to_dict


def insert_ast(ast, db: Session):
    payload = []
    for key, item in ast.items():
        payload.append({
            **item,
            "symbol": key
        })

    if not payload:
        return None

    return db.execute(insert(RepoIndex), payload)

def delete_repo_index(repo_name: str, user_id: str, db: Session):
    stmt = delete(RepoIndex).where(RepoIndex.repo_name == repo_name, RepoIndex.user_id == user_id)
    db.execute(stmt)
    
def get_by_symbol(symbol: str, repo_name: str, user_id: str, db: Session):
    stmt = select(RepoIndex).where(RepoIndex.symbol == symbol, RepoIndex.repo_name == repo_name, RepoIndex.user_id == user_id)
    response = db.scalars(stmt).one_or_none()
    return object_to_dict(response)

def upsert_repo_index(index: dict, db: Session):
    for key, item in index.items():
        stmt = insert(RepoIndex).values({
            "symbol": key,
            "file_path": item["file_path"],
            "code": item["code"],
            "start_line": item["start_line"],
            "end_line": item["end_line"],
            "repo_name": item["repo_name"],
            "user_id": item["user_id"]
        })
        
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uq_user_service_pair_symbol",
            set_={
                "code": item["code"],
                "file_path": item["file_path"],
                "start_line": item["start_line"],
                "end_line": item["end_line"],
            },
        )
        db.execute(upsert_stmt) 

    db.commit()

def get_repo_index_by_function_name(user_id: str, repo_name: str, function_names: list[str], db: Session):
    stmt = select(RepoIndex).where(RepoIndex.user_id == user_id, RepoIndex.repo_name == repo_name, RepoIndex.symbol.in_(function_names))
    response = db.scalars(stmt).all()
    return response
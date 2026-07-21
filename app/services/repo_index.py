import ast
import base64
from app.models.models import RepoIndex
import httpx

from pathlib import Path
from app.crud import repo_index 
from app.crud import user as user_crud
from app.services.github import get_pr_files, get_raw_file_content


async def build_repo_index(user_id: str, owner: str, repo_name: str, github_token: str, db ):
    repo_files = await get_repo_files(owner, repo_name, github_token)

    code_files = [
        item for item in repo_files
        if item["type"] == "blob"
        and Path(item["path"]).suffix == ".py"
    ]

    for file in code_files:
        blob = await fetch_blob(owner, repo_name, github_token, file["sha"])
        content = base64.b64decode(blob["content"]).decode("utf-8", errors="replace")

        index = build_ast(file["path"], content, repo_name, user_id)

        repo_index.insert_ast(index, db)
    
    
    
async def fetch_blob(owner: str, repo_name: str, github_token: str, sha: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo_name}/git/blobs/{sha}",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
            }
        )

    response.raise_for_status()

    return response.json()

async def get_repo_files(owner: str, repo_name: str, github_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo_name}/git/trees/main?recursive=1",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
            }
        )

    response.raise_for_status()

    return response.json()["tree"]


def build_ast(file_path: str, file_content: str, repo_name: str, user_id: str):
    repo_index = {}
    tree = ast.parse(file_content)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            suffix = Path(file_path).suffix
            module = file_path.replace("/", ".").replace(suffix, "")
            
            name = f"{module}.{node.name}"
            repo_index[name] = {
                "file_path": file_path,
                "code": ast.get_source_segment(file_content, node),
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "repo_name": repo_name,
                "user_id": user_id
            }
            
    return repo_index



async def update_repo_index(user_id: str, owner: str, repo_name: str, pull_number: int, github_token: str, db):
    
    pr_files = await get_pr_files(owner, repo_name, pull_number, github_token)

    for file in pr_files:
        file_content = await get_raw_file_content(file["contents_url"], github_token)

        index = build_ast(file["filename"], file_content, repo_name, user_id)
        repo_index.upsert_repo_index(index, db)



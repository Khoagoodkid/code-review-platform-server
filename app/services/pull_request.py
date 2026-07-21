from sqlalchemy.orm import Session

from app.crud import pull_request as pull_request_crud
from app.crud import user as user_crud
from app.models.models import PullRequest
from app.services.github import get_pr_files, get_raw_file_content
import re
import ast
from app.crud import repo_index as repo_index_crud
from joblib import load
import json
from groq import Groq
import os
from pathlib import Path
from app.services.risk_eval import calc_code_complexity, count_static


def create_pr_row(username: str, repo_name: str, number: int, status: str, title: str, body: str, url: str, pr_id: str, db: Session) -> PullRequest:
    user = user_crud.get_user_by_username(db, username)

    return pull_request_crud.create_pr_row(
        user['id'], repo_name, number, status, title, body, url, pr_id, db
    )

async def review_pr(user_id: str, owner: str, repo_name: str, pull_number: int, github_token: str, db: Session):
    print("Reviewing PR")
    files = await get_pr_files(owner, repo_name, pull_number, github_token)
    file_reviews = []

    static_vars = set()
    total_lines_added = total_lines_deleted = 0
    

    complexity_deltas = []
    for file in files:
        patch = file["patch"]
        changed_lines = get_added_lines_number(patch)
        print("changed_lines", changed_lines)

        # extract imports and calls
        raw_file_content = await get_raw_file_content(file["contents_url"], github_token)

        imports, calls = extract_imports_and_calls(raw_file_content, changed_lines)

        related_codes = []
        for call in calls:
            if call not in imports:
                continue

            related_code = repo_index_crud.get_by_symbol(imports[call], repo_name, user_id, db)
            if related_code:
                related_codes.append(related_code["code"])

        file_reviews.append({
            "filename": file["filename"],
            "diff": patch,
            "related_codes": related_codes,
            "hints": {
                "hardcoded_variables": list(count_static(raw_file_content))
            }
        })
        # complexity delta
        deltas = get_complexity_delta(file["filename"], raw_file_content, repo_name, user_id, changed_lines, db)
        complexity_deltas.extend(deltas)
        total_lines_added += file["additions"]
        total_lines_deleted += file["deletions"]

    # risk evaluation
    print("complexity_deltas", complexity_deltas)

    total_files_changed = len(files)
    total_delta = sum(complexity_deltas)
    max_delta = max(complexity_deltas) if len(complexity_deltas) > 0 else 0
    avg_delta = total_delta / len(complexity_deltas) if len(complexity_deltas) > 0 else 0
    changed_func_count = len(complexity_deltas)
    high_delta_count = sum(d >= 5 for d in complexity_deltas)

    risk_eval_model = load("app/ai/risk_model.pkl")

    X = [total_files_changed, total_lines_added, total_lines_deleted, total_delta, max_delta, avg_delta, changed_func_count, high_delta_count]
    risk_label = risk_eval_model.predict([X])

    llm_review_raw = get_llm_review(file_reviews, risk_label)
    print(llm_review_raw)

    review_trace_id = os.urandom(16).hex()
    llm_review = parse_llm_json(llm_review_raw)
    llm_review["total_files_changed"] = total_files_changed
    llm_review["total_lines_added"] = total_lines_added
    llm_review["total_lines_deleted"] = total_lines_deleted
    llm_review["total_delta"] = total_delta
    llm_review["max_delta"] = max_delta
    llm_review["avg_delta"] = avg_delta
    llm_review["changed_func_count"] = changed_func_count
    llm_review["high_delta_count"] = high_delta_count
    llm_review["risk_label"] = "high" if risk_label[0] == 1 else "low"
    llm_review["review_trace_id"] = review_trace_id

    pull_request_crud.save_ai_review(user_id, repo_name, pull_number, json.dumps(llm_review), review_trace_id, db)

    return llm_review




def get_changed_functions(file_path: str, file_content: str, changed_lines: list[int]):
    changed_functions = {}
    tree = ast.parse(file_content)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if any(line >= node.lineno and line <= node.end_lineno for line in changed_lines):

                suffix = Path(file_path).suffix
                module = file_path.replace("/", ".").replace(suffix, "")
                
                name = f"{module}.{node.name}"

                changed_functions[name] = ast.get_source_segment(file_content, node)
                
    print("changed_functions", changed_functions)
    return changed_functions





def get_complexity_delta(file_name: str, file_content: str, repo_name: str, user_id: str, changed_lines: list[int], db: Session):
    changed_functions = get_changed_functions(file_name, file_content, changed_lines)
    changed_function_names = list(changed_functions.keys())


    repo_index = repo_index_crud.get_repo_index_by_function_name(user_id, repo_name, changed_function_names, db)
    repo_index_dict = {item.symbol: item for item in repo_index}

    deltas = []

    for name, code in changed_functions.items():



        prev_complexity = calc_code_complexity(repo_index_dict[name].code) if name in repo_index_dict else 0
        new_complexity = calc_code_complexity(code)

        print("prev_complexity", prev_complexity)
        print("new_complexity", new_complexity)
        complexity_delta = new_complexity - prev_complexity
        deltas.append(complexity_delta)
    
    return deltas


def get_added_lines_number(patch: str) -> list[int]:
    changed_lines = []
    hunks = re.findall(
                r'@@.*?@@.*?(?=^@@|\Z)',
                patch,
                flags=re.MULTILINE | re.DOTALL
            )

    for hunk in hunks:
        line_num = int(hunk.split("@@")[1].split(" +")[1].split(",")[0])
        if line_num is None:
            continue
        for line in hunk.split("\n"):
            if line.startswith('-'):
                continue
            
            changed_lines.append(line_num)
            line_num += 1

    return changed_lines



class Analyzer(ast.NodeVisitor):
    changed_lines: list[int]
    def __init__(self, changed_lines: list[int]):
        self.changed_lines = changed_lines
        self.imports = {}
        self.calls = []
    
    def visit_ImportFrom(self, node):
        for alias in node.names:
            local = alias.asname or alias.name 
            self.imports[local] = f"{node.module}.{alias.name}"

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and self.is_overlap(node):
            self.calls.append(node.func.id)
        self.generic_visit(node)

    def is_overlap(self, node):
        return any(line >= node.lineno and line <= node.end_lineno for line in self.changed_lines)




def extract_imports_and_calls(file_content:str, changed_lines:list[int]):
    tree = ast.parse(file_content)

    analyzer = Analyzer(changed_lines)
    analyzer.visit(tree)

    return analyzer.imports, analyzer.calls


def parse_llm_json(content: str) -> dict:
    text = content.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    return json.loads(text)


def get_llm_review(file_reviews: list[dict], risk_label: int):
    risk_label_str = "high" if risk_label == 1 else "low"
    system_prompt = """
        You are a senior software engineer reviewing pull requests.

        Focus on:
        1. Logic bugs
        2. Security vulnerabilities
        3. Race conditions
        4. Missing edge cases
        5. Missing tests

        Rules:
        - Only report actionable issues.
        - Do not report style issues.
        - Do not report speculative issues without evidence.
        - Use the provided diff, updated code, and related code as context.
        - Return JSON only.
        - If no issues are found, return [].

        Output schema:

        {
            "issues": [
                {
                    "filename": "...",
                    "severity": "low|medium|high",
                    "line": 123,
                    "category": "logic|security|race_condition|edge_case|testing",
                    "comment": "..."
                }
            ],
            "risk_label": "high|low",
            "risk_score": 0-100,
        }


        Hints:
        - Risk label: {risk_label}  
    """

    user_prompt = f"""
        {json.dumps(file_reviews)}
    """

    initial_messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user", 
            "content": user_prompt
        }
    ]

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=initial_messages,
        max_tokens=1000,
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response.choices[0].message.content
from radon.complexity import cc_visit
import ast


def calc_code_complexity(function: str):
    blocks = cc_visit(function)
    return blocks[0].complexity

def count_static(code: str):
    tree = ast.parse(code)
    static_vars = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Constant):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        static_vars.add(target.id)

    return static_vars
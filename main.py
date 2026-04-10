import sys
import os

# Fix imports so all modules can find each other
sys.path.insert(0, os.path.dirname(__file__))

from Lexer.lexer import tokenize
from parser.parser import Parser
from parser.ast_builder import SelectQuery, BinaryCondition, Comparison
from semantic.semantic import semantic_analyzer
from optimizer.tac_generator import ThreeACGenerator
from optimizer.logical_plan import LogicalPlanGenerator, print_plan
from optimizer.optimizer import Optimizer


# -----------------------------------------------
# STEP 1: Convert Parser AST objects → dicts
#         (Semantic analyzer expects plain dicts)
# -----------------------------------------------

def condition_to_dict(node):
    if isinstance(node, BinaryCondition):
        return {
            "type": "LOGICAL",
            "operator": node.operator,
            "left": condition_to_dict(node.left),
            "right": condition_to_dict(node.right),
        }
    elif isinstance(node, Comparison):
        return {
            "column": node.left,
            "operator": node.operator,
            "value": node.right,
        }
    return {}


def ast_to_dict(ast: SelectQuery) -> dict:
    result = {
        "type": "SELECT_QUERY",
        "columns": ast.columns,
        "table": ast.table,
    }
    if ast.where:
        result["condition"] = condition_to_dict(ast.where)
    return result


# -----------------------------------------------
# PIPELINE
# -----------------------------------------------

def run_pipeline(query: str):
    print("=" * 60)
    print(f"Query: {query}")
    print("=" * 60)

    # --- Stage 1: Lexer ---
    print("\n[Stage 1] Tokens:")
    tokens = tokenize(query)
    for tok in tokens:
        print(f"  {tok}")

    # --- Stage 2: Parser → AST ---
    print("\n[Stage 2] AST:")
    parser = Parser(tokens)
    ast_obj = parser.parse()
    print(f"  {ast_obj}")

    # --- Stage 3: Convert AST to dict ---
    ast_dict = ast_to_dict(ast_obj)

    # --- Stage 4: Semantic Analysis ---
    print("\n[Stage 3] Semantic Analysis:")
    sem_result = semantic_analyzer(ast_dict)
    print(f"  Status  : {sem_result['status']}")
    if sem_result["errors"]:
        for e in sem_result["errors"]:
            print(f"  ERROR   : {e}")
    if sem_result["warnings"]:
        for w in sem_result["warnings"]:
            print(f"  WARNING : {w}")
    if sem_result["status"] != "VALID":
        print("  Pipeline stopped due to semantic errors.\n")
        return

    validated_ast = sem_result["validated_ast"]

    # --- Stage 5: TAC Generation ---
    print("\n[Stage 4] Three Address Code (TAC):")
    tac_gen = ThreeACGenerator()
    tac = tac_gen.generate(validated_ast)
    for line in tac:
        print(f"  {line}")

    # --- Stage 6: Logical Plan ---
    print("\n[Stage 5] Logical Plan:")
    lp_gen = LogicalPlanGenerator()
    plan = lp_gen.generate(validated_ast)
    print_plan(plan, indent=1)

    # --- Stage 7: Optimizer ---
    print("\n[Stage 6] Optimized Plan:")
    optimizer = Optimizer()
    optimized = optimizer.optimize(plan)
    print_plan(optimized, indent=1)

    print()


# -----------------------------------------------
# ENTRY POINT
# -----------------------------------------------

if __name__ == "__main__":
    queries = [
        "SELECT name FROM students",
        "SELECT name, age FROM students WHERE age > 18",
        "SELECT name FROM students WHERE marks > 50 AND age < 25",
    ]

    for q in queries:
        run_pipeline(q)
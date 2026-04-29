import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from Lexer.lexer import tokenize
from parser.parser import Parser
from parser.ast_builder import SelectQuery, BinaryCondition, Comparison
from semantic.semantic import semantic_analyzer
from optimizer.tac_generator import ThreeACGenerator
from optimizer.logical_plan import LogicalPlanGenerator, print_plan
from optimizer.optimizer import Optimizer


# -----------------------------------------------
# DISPLAY HELPERS
# -----------------------------------------------

def divider(char="=", width=65):
    print(char * width)

def section(title):
    print(f"\n{'─'*65}")
    print(f"  {title}")
    print(f"{'─'*65}")

def success(msg):  print(f"  [OK]      {msg}")
def error(msg):    print(f"  [ERROR]   {msg}")
def warning(msg):  print(f"  [WARNING] {msg}")
def info(msg):     print(f"  [INFO]    {msg}")


# -----------------------------------------------
# AST CONVERSION  (Parser objects -> dicts)
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
# TOKEN TABLE
# -----------------------------------------------

def print_token_table(tokens):
    print(f"\n  {'#':<5} {'TOKEN TYPE':<15} {'VALUE':<20}")
    print(f"  {'─'*5} {'─'*15} {'─'*20}")
    for i, tok in enumerate(tokens):
        if tok.type == "EOF":
            continue
        print(f"  {i+1:<5} {tok.type:<15} {tok.value:<20}")


# -----------------------------------------------
# AST SUMMARY
# -----------------------------------------------

def print_ast_summary(ast_obj):
    print(f"\n  Table    : {ast_obj.table}")
    print(f"  Columns  : {', '.join(ast_obj.columns)}")
    if ast_obj.where:
        print(f"  WHERE    : {ast_obj.where}")
    else:
        print(f"  WHERE    : (none)")
    print(f"\n  Raw AST  : {ast_obj}")


# -----------------------------------------------
# TAC WITH EXPLANATION
# -----------------------------------------------

def print_tac_explained(tac):
    explanations = {
        "SCAN"    : "<- Load all rows from table",
        "FILTER"  : "<- Apply WHERE condition",
        "PROJECT" : "<- Keep only selected columns",
        "AND"     : "<- Combine conditions with AND",
        "OR"      : "<- Either condition must match",
    }
    print(f"\n  {'LINE':<5} {'INSTRUCTION':<40} {'EXPLANATION'}")
    print(f"  {'─'*5} {'─'*40} {'─'*25}")
    for i, line in enumerate(tac):
        explanation = ""
        for keyword, exp in explanations.items():
            if keyword in line:
                explanation = exp
                break
        print(f"  {i+1:<5} {line:<40} {explanation}")


# -----------------------------------------------
# PLAN PRINTER
# -----------------------------------------------

def format_condition(cond):
    if "type" in cond and cond["type"] == "LOGICAL":
        return f"({format_condition(cond['left'])} {cond['operator']} {format_condition(cond['right'])})"
    return f"{cond['column']} {cond['operator']} {cond['value']}"

def print_plan_enhanced(plan, indent=0):
    space = "  " * indent
    arrow = "+--> " if indent > 0 else "     "

    if plan["type"] == "SCAN":
        print(f"  {space}{arrow}SCAN    {plan['table']}  <- reads raw table data")

    elif plan["type"] == "SELECT":
        cond = format_condition(plan["condition"])
        print(f"  {space}{arrow}FILTER  {cond}  <- filters rows")
        print_plan_enhanced(plan["child"], indent + 1)

    elif plan["type"] == "PROJECT":
        cols = ", ".join(plan["columns"])
        print(f"  {space}{arrow}PROJECT {cols}  <- selects columns")
        print_plan_enhanced(plan["child"], indent + 1)


# -----------------------------------------------
# OPTIMIZER EXPLANATION
# -----------------------------------------------

def count_selects(plan):
    count = 0
    if plan["type"] == "SELECT":
        count += 1
        count += count_selects(plan["child"])
    elif plan["type"] == "PROJECT":
        count += count_selects(plan["child"])
    return count

def check_optimization_applied(plan, optimized):
    before = count_selects(plan)
    after  = count_selects(optimized)

    if after > before:
        print(f"\n  [OK]   Optimization applied: AND condition split into {after} separate")
        print(f"         FILTER nodes for earlier row elimination (predicate pushdown)")
    else:
        print(f"\n  [INFO] No optimization needed — plan is already optimal")


# -----------------------------------------------
# PIPELINE
# -----------------------------------------------

def run_pipeline(query: str):
    divider("=")
    print(f"  QUERY : {query}")
    divider("=")

    # Stage 1: Lexer
    section("STAGE 1 — LEXICAL ANALYSIS (Tokenizer)")
    info("Breaking query into tokens...")
    tokens = tokenize(query)
    print_token_table(tokens)

    # Stage 2: Parser
    section("STAGE 2 — PARSING (AST Builder)")
    info("Building Abstract Syntax Tree...")
    parser = Parser(tokens)
    ast_obj = parser.parse()
    ast_dict = ast_to_dict(ast_obj)
    print_ast_summary(ast_obj)

    # Stage 3: Semantic Analysis
    section("STAGE 3 — SEMANTIC ANALYSIS")
    info("Validating tables, columns, types, and conditions...")
    sem_result = semantic_analyzer(ast_dict)

    if sem_result["errors"]:
        for e in sem_result["errors"]:
            error(e)
    if sem_result["warnings"]:
        for w in sem_result["warnings"]:
            warning(w)
    if not sem_result["errors"] and not sem_result["warnings"]:
        success("All checks passed — query is semantically valid")

    if sem_result["status"] != "VALID":
        print(f"\n  [STOP] Pipeline halted due to semantic errors\n")
        divider()
        return

    validated_ast = sem_result["validated_ast"]

    # Stage 4: TAC
    section("STAGE 4 — THREE ADDRESS CODE (TAC)")
    info("Generating intermediate representation...")
    tac_gen = ThreeACGenerator()
    tac = tac_gen.generate(validated_ast)
    print_tac_explained(tac)

    # Stage 5: Logical Plan
    section("STAGE 5 — LOGICAL EXECUTION PLAN")
    info("Building tree of relational algebra operations...")
    lp_gen = LogicalPlanGenerator()
    plan = lp_gen.generate(validated_ast)
    print()
    print_plan_enhanced(plan)

    # Stage 6: Optimized Plan
    section("STAGE 6 — QUERY OPTIMIZER")
    info("Applying rule-based optimizations...")
    optimizer = Optimizer()
    optimized = optimizer.optimize(plan)
    check_optimization_applied(plan, optimized)
    print()
    print_plan_enhanced(optimized)

    print()
    divider()
    print()


# -----------------------------------------------
# SUPPORTED QUERIES GUIDE
# -----------------------------------------------

def print_supported_queries():
    divider("=")
    print("  SemantiQL — Final Version  |  Supported Query Reference")
    divider("=")
    print("""
  The following SQL query patterns are supported in this phase:

  BASIC SELECT
  ------------
  SELECT name FROM students
  SELECT name, age FROM students
  SELECT * FROM students

  WITH WHERE CLAUSE
  -----------------
  SELECT name FROM students WHERE marks > 50
  SELECT name FROM students WHERE age = 18
  SELECT name FROM students WHERE name = 'John'

  MULTIPLE CONDITIONS
  -------------------
  SELECT name FROM students WHERE marks > 50 AND age < 25
  SELECT name FROM students WHERE marks > 50 OR age < 25

  SUPPORTED OPERATORS
  -------------------
  =   equal to
  >   greater than
  <   less than
  >=  greater than or equal
  <=  less than or equal
  !=  not equal
  <>  not equal (alternate)

  AVAILABLE TABLE & COLUMNS  (semantic validation is active)
  ----------------------------------------------------------
  Table   : students
  Columns : id (INT), name (VARCHAR), marks (INT), age (INT)

  OUT OF SCOPE (Not Supported)
  ----------------------------
  JOIN, subqueries, GROUP BY, HAVING, ORDER BY,
  LIMIT, DISTINCT, aggregate functions (COUNT, AVG, MAX...)
""")
    divider("=")
    print()


# -----------------------------------------------
# ENTRY POINT
# -----------------------------------------------

if __name__ == "__main__":
    print()
    print("  ███████╗███████╗███╗   ███╗ █████╗ ███╗   ██╗████████╗██╗ ██████╗ ██╗     ")
    print("  ██╔════╝██╔════╝████╗ ████║██╔══██╗████╗  ██║╚══██╔══╝██║██╔═══██╗██║     ")
    print("  ███████╗█████╗  ██╔████╔██║███████║██╔██╗ ██║   ██║   ██║██║   ██║██║     ")
    print("  ╚════██║██╔══╝  ██║╚██╔╝██║██╔══██║██║╚██╗██║   ██║   ██║██║▄▄ ██║██║     ")
    print("  ███████║███████╗██║ ╚═╝ ██║██║  ██║██║ ╚████║   ██║   ██║╚██████╔╝███████╗")
    print("  ╚══════╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝ ╚══▀▀═╝ ╚══════╝")
    print()
    print("        SQL Query Compiler Front-End  |  Compiler Design PBL Project")
    print()

    print_supported_queries()

    while True:
        print("  Options:")
        print("    [1] Enter a SQL query")
        print("    [2] Show supported queries again")
        print("    [3] Exit")
        print()

        choice = input("  Choose an option (1/2/3): ").strip()

        if choice == "1":
            print()
            query = input("  Enter SQL query: ").strip()
            if query:
                print()
                try:
                    run_pipeline(query)
                except Exception as e:
                    divider()
                    print(f"\n  [ERROR] Could not process query: {e}")
                    print(f"  [INFO]  Check supported query formats above\n")
                    divider()
                    print()
            else:
                print("  [INFO] No query entered.\n")

        elif choice == "2":
            print()
            print_supported_queries()

        elif choice == "3":
            print()
            print("  Exiting SemantiQL. Goodbye!")
            print()
            break

        else:
            print("  [INFO] Invalid option. Please enter 1, 2, or 3.\n")
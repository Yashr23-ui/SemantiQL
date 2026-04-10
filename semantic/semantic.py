import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from semantic.schema import schema


# -------------------------------
# HELPERS
# -------------------------------
def add_error(result, message):
    if message not in result["errors"]:
        result["errors"].append(message)
        result["status"] = "ERROR"


def add_warning(result, message):
    if message not in result["warnings"]:
        result["warnings"].append(message)


def get_type(value):
    if isinstance(value, int):
        return "INT"
    elif isinstance(value, str):
        return "VARCHAR"
    return "UNKNOWN"


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def semantic_analyzer(ast):
    result = {
        "status": "VALID",
        "errors": [],
        "warnings": [],
        "validated_ast": ast
    }

    table = ast["table"]

    # Step 1: Table validation
    check_table(table, result)

    if result["status"] == "ERROR":
        result["validated_ast"] = None
        return result

    # Step 2: Column validation
    check_columns(ast, table, result)

    # Step 3: Condition validation
    condition = ast.get("condition")
    if condition:
        validate_condition(condition, table, result)
        analyze_conditions(condition, result)

    # Final check
    if result["status"] == "ERROR":
        result["validated_ast"] = None

    return result


# -------------------------------
# TABLE CHECK
# -------------------------------
def check_table(table, result):
    if table not in schema:
        add_error(result, f"Table '{table}' does not exist")


# -------------------------------
# COLUMN CHECK
# -------------------------------
def check_columns(ast, table, result):
    for col in ast["columns"]:
        if col == "*":
            continue
        if col not in schema[table]:
            add_error(result, f"Column '{col}' not found in table '{table}'")


# -------------------------------
# CONDITION VALIDATION (RECURSIVE)
# -------------------------------
def validate_condition(condition, table, result):

    if condition.get("type") == "LOGICAL":
        validate_condition(condition["left"], table, result)
        validate_condition(condition["right"], table, result)

    else:
        col = condition["column"]
        value = condition["value"]

        if col not in schema[table]:
            add_error(result, f"Column '{col}' not found in table '{table}'")
            return

        col_type = schema[table][col]
        val_type = get_type(value)

        if col_type != val_type:
            add_error(
                result,
                f"Type mismatch: column '{col}' is {col_type}, got {val_type}"
            )


# -------------------------------
# EXTRACT CONDITIONS
# -------------------------------
def extract_conditions(condition, conditions_list):
    if condition.get("type") == "LOGICAL":
        extract_conditions(condition["left"], conditions_list)
        extract_conditions(condition["right"], conditions_list)
    else:
        conditions_list.append(condition)


# -------------------------------
# ANALYZE CONDITIONS
# -------------------------------
def analyze_conditions(condition, result):
    conditions_list = []
    extract_conditions(condition, conditions_list)

    column_map = {}

    for cond in conditions_list:
        col = cond["column"]
        op = cond["operator"]
        val = cond["value"]

        if col not in column_map:
            column_map[col] = []

        column_map[col].append((op, val))

    for col, conds in column_map.items():
        greater_vals = []
        less_vals = []
        equal_vals = []

        for op, val in conds:
            if not isinstance(val, int):
                continue

            if op in [">", ">="]:
                greater_vals.append(val)
            elif op in ["<", "<="]:
                less_vals.append(val)
            elif op == "=":
                equal_vals.append(val)

        if greater_vals and less_vals:
            if max(greater_vals) > min(less_vals):
                add_error(result, f"Contradiction detected in column '{col}'")

        if equal_vals:
            eq = equal_vals[0]
            if greater_vals and eq <= max(greater_vals):
                add_error(result, f"Contradiction detected in column '{col}'")
            if less_vals and eq >= min(less_vals):
                add_error(result, f"Contradiction detected in column '{col}'")

        if len(greater_vals) > 1:
            strongest = max(greater_vals)
            for val in greater_vals:
                if val != strongest:
                    add_warning(result, f"Redundant condition: {col} > {val}")

        if len(less_vals) > 1:
            strongest = min(less_vals)
            for val in less_vals:
                if val != strongest:
                    add_warning(result, f"Redundant condition: {col} < {val}")
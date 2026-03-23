from semantic import semantic_analyzer

# -------------------------------
# TEST CASES
# -------------------------------

# ✅ Valid query
ast1 = {
    "type": "SELECT_QUERY",
    "columns": ["name"],
    "table": "students",
    "condition": {
        "column": "marks",
        "operator": ">",
        "value": 80
    }
}

# ❌ Type error
ast2 = {
    "type": "SELECT_QUERY",
    "columns": ["name"],
    "table": "students",
    "condition": {
        "column": "marks",
        "operator": "=",
        "value": "high"
    }
}

# ❌ Contradiction
ast3 = {
    "type": "SELECT_QUERY",
    "columns": ["name"],
    "table": "students",
    "condition": {
        "type": "LOGICAL",
        "operator": "AND",
        "left": {
            "column": "marks",
            "operator": ">",
            "value": 90
        },
        "right": {
            "column": "marks",
            "operator": "<",
            "value": 40
        }
    }
}

# 🟡 Redundant
ast4 = {
    "type": "SELECT_QUERY",
    "columns": ["name"],
    "table": "students",
    "condition": {
        "type": "LOGICAL",
        "operator": "AND",
        "left": {
            "column": "marks",
            "operator": ">",
            "value": 50
        },
        "right": {
            "column": "marks",
            "operator": ">",
            "value": 30
        }
    }
}

# -------------------------------
# RUN TESTS
# -------------------------------
tests = [ast1, ast2, ast3, ast4]

for i, test in enumerate(tests, 1):
    print(f"\n--- Test Case {i} ---")
    result = semantic_analyzer(test)
    print(result)
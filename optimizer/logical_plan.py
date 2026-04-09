class LogicalPlanGenerator:
    def generate(self, ast):
        # SCAN node
        plan = {
            "type": "SCAN",
            "table": ast["table"]
        }

        # SELECT node (if condition exists)
        if "condition" in ast:
            plan = {
                "type": "SELECT",
                "condition": ast["condition"],
                "child": plan
            }

        # PROJECT node (always on top)
        plan = {
            "type": "PROJECT",
            "columns": ast["columns"],
            "child": plan
        }

        return plan


# -------- Pretty Print --------

def format_condition(cond):
    if "type" in cond and cond["type"] == "LOGICAL":
        return f"({format_condition(cond['left'])} {cond['operator']} {format_condition(cond['right'])})"
    else:
        return f"{cond['column']} {cond['operator']} {cond['value']}"


def print_plan(plan, indent=0):
    space = "  " * indent

    if plan["type"] == "SCAN":
        print(f"{space}SCAN({plan['table']})")

    elif plan["type"] == "SELECT":
        print(f"{space}SELECT({format_condition(plan['condition'])})")
        print_plan(plan["child"], indent + 1)

    elif plan["type"] == "PROJECT":
        cols = ", ".join(plan["columns"])
        print(f"{space}PROJECT({cols})")
        print_plan(plan["child"], indent + 1)


# -------- Example Run --------

if __name__ == "__main__":
    input_data = {
        "validated_ast": {
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
                    "column": "age",
                    "operator": "<",
                    "value": 25
                }
            }
        }
    }

    generator = LogicalPlanGenerator()
    plan = generator.generate(input_data["validated_ast"])

    print("Logical Plan:")
    print_plan(plan)
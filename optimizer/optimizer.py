# optimizer.py

class Optimizer:
    def optimize(self, plan):
        if plan["type"] == "PROJECT":
            plan["child"] = self.optimize(plan["child"])
            return plan

        if plan["type"] == "SELECT":
            cond = plan["condition"]

            # Split AND condition
            if cond.get("type") == "LOGICAL" and cond["operator"] == "AND":
                left = cond["left"]
                right = cond["right"]

                new_plan = {
                    "type": "SELECT",
                    "condition": left,
                    "child": {
                        "type": "SELECT",
                        "condition": right,
                        "child": plan["child"]
                    }
                }

                return self.optimize(new_plan)

            # Otherwise recurse
            plan["child"] = self.optimize(plan["child"])
            return plan

        return plan


# -------- Pretty Print (same as before) --------

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
    # Example input plan (from logical_plan.py output)
    plan = {
        "type": "PROJECT",
        "columns": ["name"],
        "child": {
            "type": "SELECT",
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
            },
            "child": {
                "type": "SCAN",
                "table": "students"
            }
        }
    }

    optimizer = Optimizer()
    optimized = optimizer.optimize(plan)

    print("Optimized Plan:")
    print_plan(optimized)
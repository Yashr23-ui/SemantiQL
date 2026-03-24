class ThreeACGenerator:
    def __init__(self):
        self.temp_count = 0
        self.code = []

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def generate_condition(self, node):
        # Base case: simple condition
        if "type" not in node or node["type"] != "LOGICAL":
            temp = self.new_temp()
            self.code.append(
                f"{temp} = {node['column']} {node['operator']} {node['value']}"
            )
            return temp

        # Recursive case: LOGICAL (AND / OR)
        left = self.generate_condition(node["left"])
        right = self.generate_condition(node["right"])

        temp = self.new_temp()
        op = node["operator"]

        self.code.append(f"{temp} = {left} {op} {right}")
        return temp

    def generate(self, ast):
        table = ast["table"]
        columns = ast["columns"]
        condition = ast.get("condition")

        # Step 1: scan table
        self.code.append(f"t0 = SCAN {table}")

        # Step 2: apply condition
        if condition:
            cond_temp = self.generate_condition(condition)
            self.code.append(f"t{self.temp_count+1} = FILTER t0 WHERE {cond_temp}")
            self.temp_count += 1
            current = f"t{self.temp_count}"
        else:
            current = "t0"

        # Step 3: projection
        cols = ", ".join(columns)
        self.code.append(f"t{self.temp_count+1} = PROJECT {cols} FROM {current}")
        self.temp_count += 1

        return self.code


# -------- Example Input --------
input_data = {
    "status": "VALID",
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

# -------- Run Generator --------
generator = ThreeACGenerator()
tac = generator.generate(input_data["validated_ast"])

for line in tac:
    print(line)
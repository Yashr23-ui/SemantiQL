# ast_builder.py

class SelectQuery:
    def __init__(self, columns, table, where):
        self.columns = columns
        self.table = table
        self.where = where

    def __repr__(self):
        return f"SelectQuery(columns={self.columns}, table={self.table}, where={self.where})"


class ConditionNode:
    pass


class BinaryCondition(ConditionNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.operator} {self.right})"


class Comparison(ConditionNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.operator} {self.right})"


# ---------------------------
# TESTING BLOCK
# ---------------------------
if __name__ == "__main__":
    print("Testing AST Builder...\n")

    # Manually constructing AST
    cond1 = Comparison("marks", ">", 50)
    cond2 = Comparison("age", "<", 25)

    where = BinaryCondition(cond1, "AND", cond2)

    query = SelectQuery(
        columns=["name", "age"],
        table="students",
        where=where
    )

    print("Constructed AST:")
    print(query)
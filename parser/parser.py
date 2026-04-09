# parser.py

from ast_builder import SelectQuery, BinaryCondition, Comparison


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def eat(self, token_type):
        if self.current().type == token_type:
            self.pos += 1
        else:
            raise ValueError(f"Expected {token_type}, got {self.current()}")

    def parse(self):
        return self.parse_select()

    def parse_select(self):
        self.eat("SELECT")

        columns = self.parse_columns()

        self.eat("FROM")

        table = self.parse_identifier()

        where_clause = None
        if self.current().type == "WHERE":
            self.eat("WHERE")
            where_clause = self.parse_condition()

        return SelectQuery(columns, table, where_clause)

    def parse_columns(self):
        columns = []

        if self.current().value == "*":
            self.eat("OPERATOR")
            return ["*"]

        columns.append(self.parse_identifier())

        while self.current().type == "COMMA":
            self.eat("COMMA")
            columns.append(self.parse_identifier())

        return columns

    def parse_identifier(self):
        token = self.current()
        if token.type == "IDENTIFIER":
            self.eat("IDENTIFIER")
            return token.value
        else:
            raise ValueError(f"Expected identifier, got {token}")

    def parse_condition(self):
        left = self.parse_comparison()

        while self.current().type in ("AND", "OR"):
            op = self.current().type
            self.eat(op)
            right = self.parse_comparison()
            left = BinaryCondition(left, op, right)

        return left

    def parse_comparison(self):
        left = self.parse_identifier()

        operator = self.current().value
        self.eat("OPERATOR")

        right = self.parse_value()

        return Comparison(left, operator, right)

    def parse_value(self):
        token = self.current()

        if token.type == "NUMBER":
            self.eat("NUMBER")
            return float(token.value) if "." in token.value else int(token.value)

        elif token.type == "STRING":
            self.eat("STRING")
            return token.value

        else:
            raise ValueError(f"Expected value, got {token}")


# ---------------------------
# TESTING BLOCK
# ---------------------------
if __name__ == "__main__":
    from lexer import tokenize

    print("Testing Parser...\n")

    queries = [
        "SELECT name FROM students",
        "SELECT name, age FROM students WHERE age > 18",
        "SELECT * FROM students WHERE marks > 50 AND age < 25",
        "SELECT id FROM students WHERE marks >= 60 OR age < 20"
    ]

    for q in queries:
        print(f"\nQuery: {q}")

        tokens = tokenize(q)
        print("Tokens:")
        for t in tokens:
            print(" ", t)

        parser = Parser(tokens)
        ast = parser.parse()

        print("\nAST:")
        print(ast)
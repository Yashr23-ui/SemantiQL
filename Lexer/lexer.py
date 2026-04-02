#  Token class 

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token(type={self.type!r}, value={self.value!r})"

    def __eq__(self, other):
        if not isinstance(other, Token):
            return False
        return self.type == other.type and self.value == other.value

KEYWORDS = {"SELECT", "FROM", "WHERE", "AND", "OR"}

TWO_CHAR_OPERATORS = {"!=", "<>", "<=", ">="}
ONE_CHAR_OPERATORS = {"=", "<", ">", "*"}

#  Token builder

def make_token(token_type: str, value: str) -> Token:
    return Token(token_type, value)



#  Lexer

def tokenize(query: str) -> list[Token]:
    tokens = []
    i = 0
    n = len(query)

    while i < n:

        # Skip whitespace
        if query[i].isspace():
            i += 1
            continue

        # String literals
        if query[i] in ('"', "'"):
            quote = query[i]
            j = i + 1
            buf = []

            while j < n:
                if query[j] == quote:
                    if j + 1 < n and query[j + 1] == quote:
                        buf.append(quote)
                        j += 2
                    else:
                        j += 1
                        break
                else:
                    buf.append(query[j])
                    j += 1
            else:
                raise ValueError(f"Unterminated string literal at position {i}")

            tokens.append(make_token("STRING", "".join(buf)))
            i = j
            continue

        # Numbers
        if query[i].isdigit():
            j = i
            while j < n and query[j].isdigit():
                j += 1

            if j < n and query[j] == "." and j + 1 < n and query[j + 1].isdigit():
                j += 1
                while j < n and query[j].isdigit():
                    j += 1

            tokens.append(make_token("NUMBER", query[i:j]))
            i = j
            continue

        # Identifiers/Keywords
        if query[i].isalpha() or query[i] == "_":
            j = i
            while j < n and (query[j].isalnum() or query[j] == "_"):
                j += 1

            word = query[i:j]
            upper_word = word.upper()

            if upper_word in KEYWORDS:
                tokens.append(make_token(upper_word, upper_word))
            else:
                tokens.append(make_token("IDENTIFIER", word))

            i = j
            continue

       #operators
        two = query[i:i + 2]
        if two in TWO_CHAR_OPERATORS:
            tokens.append(make_token("OPERATOR", two))
            i += 2
            continue

        if query[i] in ONE_CHAR_OPERATORS:
            tokens.append(make_token("OPERATOR", query[i]))
            i += 1
            continue
# PUNCHUATION
        punct_map = {
            "(": "LPAREN",
            ")": "RPAREN",
            ",": "COMMA",
            ";": "SEMICOLON",
        }

        if query[i] in punct_map:
            tokens.append(make_token(punct_map[query[i]], query[i]))
            i += 1
            continue

       
        raise ValueError(f"Unrecognised character '{query[i]}' at position {i}")

    tokens.append(make_token("EOF", ""))
    return tokens
# OUTPUT
if __name__ == "__main__":
    queries = [
        "SELECT name FROM users",
        "SELECT name, age FROM users WHERE age > 18",
        "SELECT * FROM orders WHERE status = 'active' AND total >= 100",
        "SELECT id FROM products WHERE price <= 50 OR category = 'books'",
    ]

    for q in queries:
        print(f"\nQuery : {q}")
        tokens = tokenize(q)
        print("Output:")
        for tok in tokens:
            print(f"  {tok}")
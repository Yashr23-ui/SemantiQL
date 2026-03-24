

import json



KEYWORDS = {"SELECT", "FROM", "WHERE", "AND", "OR"}

TWO_CHAR_OPERATORS = {"!=", "<>", "<=", ">="}
ONE_CHAR_OPERATORS = {"=", "<", ">", "*"}



#  Token builder

def make_token(token_type: str, value: str) -> dict:
    return {"type": token_type, "value": value}



#  Lexer

def tokenize(query: str) -> list[dict]:
  
    tokens = []
    i = 0
    n = len(query)

    while i < n:
        if query[i].isspace():
            i += 1
            continue
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
                raise ValueError(f"Unterminated string literal starting at position {i}")
            tokens.append(make_token("STRING", "".join(buf)))
            i = j
            continue

        
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
        if query[i].isalpha() or query[i] == "_":
            j = i
            while j < n and (query[j].isalnum() or query[j] == "_"):
                j += 1
            word = query[i:j]
            token_type = word.upper() if word.upper() in KEYWORDS else "IDENTIFIER"
            tokens.append(make_token(token_type, word.upper() if token_type != "IDENTIFIER" else word))
            i = j
            continue
        two = query[i:i + 2]
        if two in TWO_CHAR_OPERATORS:
            tokens.append(make_token("OPERATOR", two))
            i += 2
            continue
        if query[i] in ONE_CHAR_OPERATORS:
            tokens.append(make_token("OPERATOR", query[i]))
            i += 1
            continue

       
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


#  Run examples


if __name__ == "__main__":
    queries = [
        "SELECT name FROM users",
        "SELECT name, age FROM users WHERE age > 18",
        "SELECT * FROM orders WHERE status = 'active' AND total >= 100",
        "SELECT id FROM products WHERE price <= 50 OR category = 'books'",
    ]

    for q in queries:
        print(f"\nQuery : {q}")
        result = tokenize(q)
        print("Output:", json.dumps(result, indent=2))
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from Lexer.lexer import tokenize
from parser.parser import Parser
from semantic.semantic import semantic_analyzer
from optimizer.tac_generator import ThreeACGenerator
from optimizer.logical_plan import LogicalPlanGenerator
from optimizer.optimizer import Optimizer
from main import ast_to_dict

app = FastAPI(title="SemantiQL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.post("/api/compile")
def compile_query(req: QueryRequest):
    query = req.query
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result = {
        "query": query,
        "tokens": [],
        "ast": None,
        "semantic": None,
        "tac": [],
        "plan": None,
        "optimized_plan": None,
        "error": None
    }

    try:
        # Lexer
        tokens = tokenize(query)
        result["tokens"] = [{"type": t.type, "value": t.value} for t in tokens if t.type != "EOF"]

        # Parser
        parser = Parser(tokens)
        ast_obj = parser.parse()
        ast_dict = ast_to_dict(ast_obj)
        result["ast"] = ast_dict

        # Semantic
        sem_result = semantic_analyzer(ast_dict)
        result["semantic"] = sem_result
        
        if sem_result["status"] != "VALID":
            result["error"] = "Semantic Validation Failed"
            return result

        validated_ast = sem_result["validated_ast"]

        # TAC
        tac_gen = ThreeACGenerator()
        tac = tac_gen.generate(validated_ast)
        result["tac"] = tac

        # Logical Plan
        lp_gen = LogicalPlanGenerator()
        plan = lp_gen.generate(validated_ast)
        result["plan"] = plan

        # Optimizer
        optimizer = Optimizer()
        optimized = optimizer.optimize(plan)
        result["optimized_plan"] = optimized

        return result

    except Exception as e:
        result["error"] = str(e)
        return result

# Serve static files last
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

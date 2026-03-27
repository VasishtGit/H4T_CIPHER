from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import os
from typing import List
from pydantic import BaseModel

from database import DatabaseManager
from llm_reasoner import LLMGraphReasoner
from ocr_graph import extract_text_from_image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_MODEL = os.getenv("GRAPH_OLLAMA_MODEL", "moondream")
OLLAMA_URL = os.getenv("GRAPH_OLLAMA_URL", "http://127.0.0.1:11434")

llm_reasoner = LLMGraphReasoner(model=OLLAMA_MODEL, base_url=OLLAMA_URL)
db = DatabaseManager()


@app.post("/upload")
async def solve_graph(images: List[UploadFile] = File(...)):
    try:
        if not images:
            raise HTTPException(status_code=400, detail="No images uploaded")

        file = images[0]
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        ocr_text = extract_text_from_image(img)
        llm_solution = llm_reasoner.solve_image(img, ocr_text=ocr_text)

        llm_solution["ocr_text"] = ocr_text
        llm_solution["equation_source"] = "LLM multimodal"
        llm_solution["equation_confidence"] = 0.85 if llm_solution.get("status") == "ok" else 0.2
        llm_solution["candidate_scores"] = [
            {
                "source": "LLM multimodal",
                "status": llm_solution.get("status"),
                "score": llm_solution.get("equation_confidence"),
            }
        ]

        db.save_query({**llm_solution, "source": "LLM multimodal"})

        return {
            "status": "success",
            "solution": llm_solution,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


class SolveTextRequest(BaseModel):
    equation: str


@app.post("/solve_text")
async def solve_text(req: SolveTextRequest):
    try:
        if not req.equation or not req.equation.strip():
            raise HTTPException(status_code=400, detail="Equation text is required")

        llm_solution = llm_reasoner.solve_text(req.equation.strip())
        llm_solution["equation_source"] = "LLM text"

        db.save_query({**llm_solution, "source": "LLM text"})

        return {
            "status": "success",
            "solution": llm_solution,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

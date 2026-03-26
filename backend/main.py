from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from typing import List

from model_manager import ModelManager
from solver import GraphSolver
from database import DatabaseManager

app = FastAPI()

# Enable CORS for your local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
ai_engine = ModelManager("weights/graph_model.pth")
math_solver = GraphSolver()
db = DatabaseManager()

@app.post("/upload")
async def solve_graph(images: List[UploadFile] = File(...)):
    try:
        # Read the first uploaded image
        file = images[0]
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # AI Prediction
        adj_matrix = ai_engine.predict(img)

        # Math Solving
        result = math_solver.analyze(adj_matrix)

        # Save to History
        db.save_query(result)

        return {
            "status": "success",
            "solution": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
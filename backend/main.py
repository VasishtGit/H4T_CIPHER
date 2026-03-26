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
# Using Florence-2 for visual mathematical analysis
ai_engine = ModelManager("microsoft/Florence-2-base")
math_solver = GraphSolver()
db = DatabaseManager()

@app.post("/upload")
async def solve_graph(images: List[UploadFile] = File(...)):
    try:
        if not images:
            raise HTTPException(status_code=400, detail="No images uploaded")

        # Read the first uploaded image
        file = images[0]
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # 1. AI Vision Analysis
        # Predict now returns a string description/equation (e.g., "y = 2x + 3")
        equation_str = ai_engine.predict(img)

        # 2. Mathematical Solving
        # Analyze now takes the string and calculates intercepts and slopes
        result = math_solver.analyze(equation_str)

        # 3. Save to History
        # Ensures result dictionary is stored in the database
        db.save_query(result)

        return {
            "status": "success",
            "solution": result
        }
        
    except Exception as e:
        # Professional error reporting for debugging
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Hosting on 0.0.0.0:8000 for local network access
    uvicorn.run(app, host="0.0.0.0", port=8000)
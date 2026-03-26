from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from typing import List

from model_manager import ModelManager
from solver import GraphSolver
from database import DatabaseManager
from ocr_graph import extract_text_from_image, detect_line_equation

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

        # 1. Image to text via AI vision
        ai_text = ai_engine.predict(img)

        # 2. OCR pipeline fallback (for pure printed equation text or graph labels)
        ocr_text = extract_text_from_image(img)

        # 3. Analyzer tries AI output first, then OCR text
        result = math_solver.analyze(ai_text)
        result_source = 'AI vision'

        if result.get('equation') == 'Could not identify a specific linear equation':
            result = math_solver.analyze(ocr_text)
            result_source = 'OCR fallback'

        # 4. Geometric fallback (line detection) when text-based parse fails
        if result.get('equation') == 'Could not identify a specific linear equation':
            line_coeff = detect_line_equation(img)
            if line_coeff:
                m, c = line_coeff
                result = math_solver.analyze_from_coefficients(m, c, raw_result=f'hough line detected m={m}, c={c}', source='line detection')
                result_source = 'Line detection fallback'

        result['ocr_text'] = ocr_text
        result['ai_text'] = ai_text
        result['equation_source'] = result_source

        # 5. Save to Database
        db.save_query({**result, 'source': result_source})

        return {
            "status": "success",
            "solution": result
        }
        
    except Exception as e:
        # Professional error reporting for debugging
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


from pydantic import BaseModel

class SolveTextRequest(BaseModel):
    equation: str


@app.post("/solve_text")
async def solve_text(req: SolveTextRequest):
    try:
        if not req.equation or not req.equation.strip():
            raise HTTPException(status_code=400, detail="Equation text is required")

        result = math_solver.analyze(req.equation)
        db.save_query({**result, "source": "manual"})

        return {
            "status": "success",
            "solution": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Hosting on 0.0.0.0:8000 for local network access
    uvicorn.run(app, host="0.0.0.0", port=8000)
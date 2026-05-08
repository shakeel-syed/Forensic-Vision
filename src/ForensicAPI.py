from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import tempfile
import shutil
from typing import List, Optional
from pydantic import BaseModel
from ImageQuality import app, InspectorState

# Define Response Models for Documentation
class DetectionInfo(BaseModel):
    label: str
    box_2d: List[int]
    description: str

class AttemptRecord(BaseModel):
    iteration: int
    analysis: str
    score: int
    decision: str
    reasoning: str
    detections: List[DetectionInfo]

class InspectionResponse(BaseModel):
    case_id: Optional[str] = None
    image_name: str
    final_decision: str
    final_score: int
    total_attempts: int
    detailed_analysis: str
    detections: List[DetectionInfo]
    history: List[AttemptRecord]

# Initialize FastAPI
api = FastAPI(
    title="Forensic Spatial API",
    description="Professional REST service for Law Enforcement to map forensic evidence and validate quality.",
    version="1.1.0"
)

@api.get("/health", tags=["System"])
async def health_check():
    """Returns the status of the API service."""
    return {"status": "online", "engine": "Gemini Spatial / LangGraph"}

@api.post("/inspect", response_model=InspectionResponse, tags=["Forensics"])
async def inspect_image(
    case_id: Optional[str] = None,
    file: UploadFile = File(...)
):
    """
    Upload an image for forensic spatial mapping and quality inspection.
    - **case_id**: Optional identifier for tracking evidence.
    - **file**: The image file (JPG, PNG).
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    # Save uploaded file to a temporary secure location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        temp_path = tmp_file.name

    try:
        # Prepare initial state for LangGraph
        initial_state = {
            "image_path": temp_path,
            "iterations": 0,
            "decision": "",
            "analysis": "",
            "quality_score": 0,
            "detections": [],
            "history": []
        }

        # Execute the workflow
        result = app.invoke(initial_state)

        # Cleanup temp file
        os.remove(temp_path)

        # Structure the response
        return {
            "case_id": case_id,
            "image_name": file.filename,
            "final_decision": result['decision'],
            "final_score": result['quality_score'],
            "total_attempts": result['iterations'],
            "detailed_analysis": result['analysis'],
            "detections": result.get('detections', []),
            "history": result['history']
        }

    except Exception as e:
        import traceback
        traceback.print_exc() # This will show the error in your terminal
        # Ensure cleanup on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Inspection failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)

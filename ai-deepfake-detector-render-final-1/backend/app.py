from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
import io
import os

app = FastAPI(title="AI Image Fake Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend if present in ../frontend
current_dir = os.path.dirname(__file__)
frontend_dir = os.path.abspath(os.path.join(current_dir, "..", "frontend"))
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

ALLOWED_TYPES = ["image/jpeg", "image/png"]
MAX_SIZE_MB = 5

@app.get("/health/ready")
def ready():
    return {"status": "ok"}

@app.post("/detect-image")
async def detect_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPG or PNG images allowed")

    data = await file.read()
    if len(data) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Image too large (max {MAX_SIZE_MB}MB)")

    try:
        Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # TODO: Replace with real model inference.
    confidence = 0.78
    result = "AI GENERATED" if confidence > 0.5 else "REAL"

    return {
        "result": result,
        "confidence": round(confidence * 100, 2),
        "message": "This is an AI-assisted prediction, not legal proof."
    }

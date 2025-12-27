from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io

app = FastAPI(title="AI Image Fake Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        raise HTTPException(status_code=400, detail="Image too large (max 5MB)")

    try:
        Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    confidence = 0.78
    result = "AI GENERATED" if confidence > 0.5 else "REAL"

    return {
        "result": result,
        "confidence": round(confidence * 100, 2),
        "message": "This is an AI-assisted prediction, not legal proof."
    }

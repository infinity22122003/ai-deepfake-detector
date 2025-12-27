import os
import io
import tempfile
import logging
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from PIL import Image
import cv2
import numpy as np

from .utils import load_model, preprocess_image, infer_on_frames

LOGGER = logging.getLogger("uvicorn.error")

MODEL_PATH = os.environ.get("MODEL_PATH", "model.pt")
DEVICE = os.environ.get("DEVICE", "cpu")

app = FastAPI(title="Deepfake Detector API")

# Allow frontend to call API (if served from different origin during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files from / (assumes frontend/ exists in image/container)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

model = None


@app.on_event("startup")
def startup_event():
    global model
    try:
        model = load_model(MODEL_PATH, DEVICE)
        LOGGER.info(f"Loaded model from {MODEL_PATH} on {DEVICE}")
    except Exception as e:
        LOGGER.error(f"Failed to load model: {e}")
        # Do not raise here so container still starts; endpoint will return error


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


def read_image_from_upload(upload_file: UploadFile) -> Image.Image:
    content = upload_file.file.read()
    upload_file.file.close()
    try:
        img = Image.open(io.BytesIO(content)).convert("RGB")
        return img
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file is not a supported image")


def extract_frames_from_video_bytes(content: bytes, max_frames: int = 16) -> List[Image.Image]:
    # Write to temp file because cv2.VideoCapture works with filenames reliably
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        cap = cv2.VideoCapture(tmp.name)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not decode video file")

        frames = []
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total <= 0:
            # fallback: try reading until exhausted
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
                if len(frames) >= max_frames:
                    break
        else:
            # sample evenly up to max_frames
            indices = np.linspace(0, max(0, total - 1), min(max_frames, max(1, total))).astype(int)
            idx_set = set(indices.tolist())
            cur = 0
            read_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if cur in idx_set:
                    frames.append(frame)
                    read_idx += 1
                    if read_idx >= len(idx_set):
                        break
                cur += 1
        cap.release()

        pil_frames = []
        for f in frames:
            # convert BGR (cv2) -> RGB (PIL)
            rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            pil_frames.append(Image.fromarray(rgb))

        if not pil_frames:
            raise HTTPException(status_code=400, detail="No frames could be extracted from the video")

        return pil_frames


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded on server")

    content_type = (file.content_type or "").lower()
    try:
        content = await file.read()
    finally:
        await file.close()

    frames = []
    if content_type.startswith("image/"):
        # Single image
        try:
            img = Image.open(io.BytesIO(content)).convert("RGB")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")
        frames = [img]
    elif content_type.startswith("video/") or file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
        frames = extract_frames_from_video_bytes(content, max_frames=16)
    else:
        # Try to treat as image
        try:
            img = Image.open(io.BytesIO(content)).convert("RGB")
            frames = [img]
        except Exception:
            raise HTTPException(status_code=400, detail="Unsupported file type. Upload an image or video.")

    # Preprocess and infer
    try:
        score, frame_scores = infer_on_frames(frames, model, device=DEVICE, batch_size=8)
    except Exception as e:
        LOGGER.exception("Inference failed")
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    label = "fake" if score >= 0.5 else "real"
    return JSONResponse({
        "score": float(score),
        "label": label,
        "frame_count": len(frame_scores),
        "frame_scores": [float(v) for v in frame_scores],
    })

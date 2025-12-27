
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from celery import Celery
import uuid, os

API_KEY = os.getenv("DETECTOR_API_KEY","change_me")

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)

celery = Celery("tasks", broker="redis://redis:6379/0")
RESULTS = {}

@app.post("/api/upload")
@limiter.limit("5/minute")
async def upload(file: UploadFile = File(...), type: str = Form(...), x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401)
    case_id = str(uuid.uuid4())
    RESULTS[case_id] = {"status":"processing"}
    celery.send_task("tasks.analyze", args=[case_id])
    return {"case_id": case_id}

@app.get("/api/result/{case_id}")
async def result(case_id:str):
    return RESULTS.get(case_id, {"status":"processing"})

@app.get("/health/ready")
def health():
    return {"status":"ok"}

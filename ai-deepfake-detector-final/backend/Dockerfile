
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn gunicorn python-multipart slowapi celery
CMD gunicorn -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000

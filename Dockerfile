FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# system deps for pillow/opencv
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libgl1 libglib2.0-0 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip setuptools wheel
# Install PyTorch CPU wheels from official index and other deps
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r /app/backend/requirements.txt

# Copy app and frontend
COPY backend /app/backend
COPY frontend /app/frontend

# Expose port and run uvicorn
EXPOSE 80

# Default model path (user must add model.pt in container or mount it)
ENV MODEL_PATH=/app/model.pt

CMD ["uvicorn","backend.app:app","--host","0.0.0.0","--port","80"]

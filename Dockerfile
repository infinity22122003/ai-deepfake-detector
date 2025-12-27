FROM python:3.10-slim

WORKDIR /app

# Install system deps needed by Pillow/OpenCV etc.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libjpeg-dev libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python requirements
COPY ai-deepfake-detector-render-final-1/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend into the image
COPY ai-deepfake-detector-render-final-1/backend/ ./backend
COPY ai-deepfake-detector-render-final-1/frontend/ ./frontend

# Expose port
EXPOSE 8000

# Set working dir to backend so uvicorn can import app:app
WORKDIR /app/backend

# Correct exec-form CMD (JSON array with double quotes)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

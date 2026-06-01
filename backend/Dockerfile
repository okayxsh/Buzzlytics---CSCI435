FROM python:3.10-slim

# Install system dependencies needed for OpenCV and ultralytics/YOLO
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend files and cv_pipeline
COPY backend/ ./backend/
COPY cv_pipeline/ ./cv_pipeline/

EXPOSE 8000

ENV PYTHONPATH=/app

CMD ["python", "backend/main.py"]

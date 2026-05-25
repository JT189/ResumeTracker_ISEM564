# ── Stage: Runtime ────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy only the backend requirements first (layer caching — faster rebuilds)
COPY backend/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend source code
COPY backend/ ./

# Cloud Run injects the PORT environment variable (default 8080)
# Uvicorn must listen on 0.0.0.0 for Cloud Run to reach it
ENV PORT=8080

EXPOSE 8080

# Start the FastAPI app using uvicorn
# "main:app" means: file main.py, variable app = FastAPI(...)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]

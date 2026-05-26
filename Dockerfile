# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ ./

# Empty string = relative URLs, so API calls hit the same domain as the frontend
ENV VITE_API_BASE_URL=""

RUN npm run build
# Output lands in /frontend/dist

# ── Stage 2: FastAPI backend + built frontend ──────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir aiofiles

COPY backend/ ./

# Drop the React build into ./static so FastAPI can serve it
COPY --from=frontend-builder /frontend/dist ./static

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]

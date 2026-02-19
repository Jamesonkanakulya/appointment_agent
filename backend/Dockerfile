# ─── Stage 1: Build React frontend ───────────────────────────────────────────
# Build context is project root (set in docker-compose.yml)
FROM node:20-slim AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
# Override outDir to build into /build/frontend/dist (not ../backend/static)
RUN npx vite build --outDir /build/frontend/dist --emptyOutDir

# ─── Stage 2: Python backend ──────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Copy built React frontend into static/ folder served by FastAPI
COPY --from=frontend-builder /build/frontend/dist ./static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

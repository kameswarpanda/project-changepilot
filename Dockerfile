# ==============================================================================
# Stage 1: Build Angular Frontend
# ==============================================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps || npm install

COPY frontend/ ./
RUN npm run build -- --configuration production

# ==============================================================================
# Stage 2: Production Python Backend & Runtime
# ==============================================================================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PYTHONPATH=/app \
    HOST=0.0.0.0

WORKDIR /app

# Install system dependencies (git for isolated repo management, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies and install changepilot in editable mode
COPY pyproject.toml .
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -e .

# Copy backend source code & demo repository
COPY backend/ ./backend/
COPY demo_repo/ ./demo_repo/

# Copy built Angular frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist/changepilot /app/frontend/dist/changepilot

# Setup permissions
RUN mkdir -p /app/temp_workspaces && chmod -R 777 /app

EXPOSE 8080

CMD ["sh", "-c", "python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port ${PORT:-8080}"]

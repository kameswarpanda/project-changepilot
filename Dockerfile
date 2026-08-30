# ==============================================================================
# Stage 1: Build Angular Frontend
# ==============================================================================
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps || npm install

COPY frontend/ ./
RUN npm run build --configuration=production

# ==============================================================================
# Stage 2: Production Python Backend & Runtime
# ==============================================================================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Install system dependencies (git for isolated repo management, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code & demo repository
COPY backend/ ./backend/
COPY demo_repo/ ./demo_repo/
COPY pyproject.toml .

# Copy built Angular frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist/changepilot /app/frontend/dist/changepilot

# Create non-root user and setup permissions
RUN useradd -m -u 10001 -s /bin/bash appuser && \
    mkdir -p /app/temp_workspaces && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port ${PORT:-8000}"]

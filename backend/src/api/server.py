"""FastAPI application entrypoint for ChangePilot."""
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from backend.src.api.routes import router
from backend.src.config import settings
from backend.src.database.session import init_db

# Configure root logger
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("changepilot.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for initializing database and services."""
    logger.info("Initializing ChangePilot database schema...")
    init_db()
    yield
    logger.info("ChangePilot application shutdown.")


app = FastAPI(
    title="ChangePilot API",
    description="Autonomous Software Change Platform with Deterministic Safety Boundaries",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Attach API routes first
app.include_router(router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler ensuring no internal secrets or traces leak."""
    logger.error(f"Unhandled error processing {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred while processing the request."}
    )


# Serve compiled Angular static frontend (for production and standalone local container serving)
CANDIDATE_STATIC_DIRS = [
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist" / "changepilot" / "browser",
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist" / "changepilot",
    Path("/app/frontend/dist/changepilot/browser"),
    Path("/app/frontend/dist/changepilot")
]


def get_static_dir() -> Optional[Path]:
    """Finds the active compiled frontend directory."""
    for d in CANDIDATE_STATIC_DIRS:
        if d.exists() and (d / "index.html").exists():
            return d
    return None


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa_or_static(full_path: str):
    """Serves static assets or falls back to Angular index.html for SPA routing."""
    # Never intercept API, health, or swagger documentation endpoints
    if full_path.startswith("api/") or full_path.startswith("health") or full_path.startswith("docs") or full_path.startswith("openapi.json") or full_path.startswith("redoc"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    static_dir = get_static_dir()
    if static_dir:
        target_file = static_dir / full_path
        if full_path and target_file.is_file():
            return FileResponse(str(target_file))

        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

    return JSONResponse(
        status_code=200,
        content={
            "service": "ChangePilot API",
            "status": "running",
            "docs": "/docs",
            "health": "/health",
            "ui_status": "Start Angular frontend via 'npm start' on port 4200 or compile with 'npm run build'."
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.src.api.server:app", host=settings.host, port=settings.port, reload=True)

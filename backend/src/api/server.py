"""FastAPI application entrypoint for ChangePilot."""
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.src.api.routes import router
from backend.src.config import settings

# Configure root logger
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("changepilot.server")

app = FastAPI(
    title="ChangePilot API",
    description="Autonomous Software Change Platform with Deterministic Safety Boundaries",
    version="1.0.0",
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
)

# Attach API routes
app.include_router(router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler ensuring no internal secrets or traces leak."""
    logger.error(f"Unhandled error processing {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred while processing the request."}
    )


# Serve compiled Angular static frontend if present (for production Docker container)
static_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist" / "changepilot" / "browser"
if static_dist.exists():
    app.mount("/", StaticFiles(directory=str(static_dist), html=True), name="static")
    logger.info(f"Mounted static frontend from {static_dist}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.src.api.server:app", host=settings.host, port=settings.port, reload=True)

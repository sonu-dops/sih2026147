"""SignalInsight Professional API Entry Point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.router import api_v1_router
from backend.app.config import settings
from backend.app.db.database import init_db
from backend.app.seed.demo_seed import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    # 1. Initialize storage directories
    settings.init_storage_dirs()

    # 2. Initialize database schema
    init_db()

    # 3. Seed initial baseline demo/benchmark models
    try:
        seed_demo_data()
    except Exception as e:
        print(f"[WARNING] Seed data initialization skipped: {e}")

    yield


app = FastAPI(
    title="SignalInsight AMC & RF Signal Analysis API",
    description="Professional Automatic Modulation Classification (AMC) & IQ/WAV Signal-Analysis Engine API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
origins = settings.cors_origins if isinstance(settings.cors_origins, list) else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standardized Error Response Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Formats all HTTPExceptions into the standardized error JSON response."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        err_dict = exc.detail
    else:
        err_dict = {
            "code": f"HTTP_{exc.status_code}",
            "message": str(exc.detail),
            "details": {},
        }
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": err_dict},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled errors and returns standardized error JSON without raw stack trace."""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": {"type": type(exc).__name__, "summary": str(exc)},
            }
        },
    )


# Mount Master Router
app.include_router(api_v1_router)


@app.get("/")
def root():
    return {
        "app": "SignalInsight",
        "version": "1.0.0",
        "documentation": "/docs",
        "api_v1": "/api/v1",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )

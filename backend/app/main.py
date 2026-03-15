"""FlowSync API - Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.errors import (
    FlowSyncException,
    flowsync_exception_handler,
    http_exception_handler,
    general_exception_handler,
)
from app.core.logging import setup_logging, get_logger
from app.api.health import router as health_router
from app.api.tasks import router as tasks_router
from app.api.events import router as events_router

# Set up logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal Productivity Dashboard API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(FlowSyncException, flowsync_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health_router)
app.include_router(tasks_router, prefix=settings.API_V1_PREFIX)
app.include_router(events_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info(
        "Application starting",
        extra={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
        },
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Application shutting down")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

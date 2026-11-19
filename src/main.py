"""
FastAPI Application Entrypoint for Testing Agent Platform.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.config.settings import settings
from src.core.logging import get_logger
from src.core.exceptions import TestingPlatformException
from src.database.session import init_db
from src.api.health import router as health_router
from src.api.projects import router as projects_router
from src.api.requirements import router as requirements_router
from src.api.scenarios import router as scenarios_router
from src.api.test_cases import router as test_cases_router
from src.api.automation import router as automation_router
from src.api.executions import router as executions_router
from src.api.approvals import router as approvals_router
from src.api.models_api import router as models_router
from src.api.integrations_api import router as integrations_router
from src.api.workflows_api import router as workflows_router

logger = get_logger("main")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise-grade AI-powered software testing platform using 6 specialized agents.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Custom Exception Handler
@app.exception_handler(TestingPlatformException)
async def custom_exception_handler(request: Request, exc: TestingPlatformException):
    logger.error(f"Platform error: {exc.message} - Details: {exc.details}")
    return JSONResponse(
        status_code=400,
        content={"error": exc.message, "details": exc.details},
    )


# Lifecycle Events
@app.on_event("startup")
def on_startup():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in {settings.ENVIRONMENT} mode.")
    init_db()


# Include Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(requirements_router, prefix="/api/v1")
app.include_router(scenarios_router, prefix="/api/v1")
app.include_router(test_cases_router, prefix="/api/v1")
app.include_router(automation_router, prefix="/api/v1")
app.include_router(executions_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(models_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }

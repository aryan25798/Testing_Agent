"""
FastAPI Application Entrypoint for Testing Agent Platform.
Hardened with Security Headers, Trusted Host validation, Request Size Limits,
and Audit Logging.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.config.settings import settings
from src.core.logging import get_logger
from src.core.exceptions import TestingPlatformException
from src.core.security.audit_logger import audit_logger
from src.core.security.secrets_manager import secrets_manager
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
from src.api.dashboard_api import router as dashboard_router
from src.api.custom_agents_api import router as custom_agents_router
from src.api.mcp_api import router as mcp_router

logger = get_logger("main")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise-grade AI-powered software testing platform using 6 specialized agents.",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Security Headers & Request Limiting Middleware
class SecurityHardeningMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Enforce payload size limit to prevent Denial-of-Service
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > settings.MAX_UPLOAD_SIZE_BYTES:
                    audit_logger.log_event(
                        action="REQUEST_PAYLOAD_TOO_LARGE",
                        status="REJECTED",
                        details={"content_length": content_length, "max_allowed": settings.MAX_UPLOAD_SIZE_BYTES},
                        severity="WARNING",
                    )
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"error": "Payload Too Large", "detail": f"Request body exceeds {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB limit."},
                    )
            except ValueError:
                pass

        # 2. Process request
        response = await call_next(request)

        # 3. Inject Defensive Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy (allows local Angular UI and assets)
        csp_policy = (
            "default-src 'self' http://localhost:* http://127.0.0.1:*; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        return response


# Add Security Hardening Middleware
app.add_middleware(SecurityHardeningMiddleware)

# Enforce Trusted Hosts (Defense against DNS rebinding & Host header attacks)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# CORS Middleware (Restricted to configured local origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


# Global Custom Exception Handler
@app.exception_handler(TestingPlatformException)
async def custom_exception_handler(request: Request, exc: TestingPlatformException):
    logger.error(f"Platform error: {exc.message} - Details: {exc.details}")
    return JSONResponse(
        status_code=400,
        content={"error": exc.message, "details": exc.details},
    )


# Unhandled Internal Exception Handler (Prevents stack trace leaks to API consumers)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    audit_logger.log_event(
        action="UNHANDLED_EXCEPTION",
        status="ERROR",
        details={"path": request.url.path, "method": request.method, "exception_type": type(exc).__name__},
        severity="ERROR",
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred. Check system logs for details."},
    )


# Lifecycle Events
@app.on_event("startup")
def on_startup():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in {settings.ENVIRONMENT} mode.")
    init_db()
    audit_logger.log_event(
        action="SERVER_STARTUP",
        status="SUCCESS",
        details={"version": settings.APP_VERSION, "environment": settings.ENVIRONMENT, "host": settings.APP_HOST, "port": settings.APP_PORT},
    )


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
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(custom_agents_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }

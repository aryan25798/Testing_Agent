"""
Health check and system diagnostics endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.session import get_db
from src.config.settings import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    """Returns application status, database connectivity, and configuration metadata."""
    db_healthy = False
    try:
        db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception:
        db_healthy = False

    return {
        "status": "healthy" if db_healthy else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database_connected": db_healthy,
        "default_provider": settings.DEFAULT_PROVIDER,
    }

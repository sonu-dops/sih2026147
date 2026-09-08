"""Master API v1 router consolidating all sub-routers."""

from fastapi import APIRouter

from backend.app.api.v1.analysis import router as analysis_router
from backend.app.api.v1.classification import router as classification_router
from backend.app.api.v1.datasets import router as datasets_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.jobs import router as jobs_router
from backend.app.api.v1.models import router as models_router
from backend.app.api.v1.projects import router as projects_router
from backend.app.api.v1.reports import router as reports_router
from backend.app.api.v1.settings import router as settings_router
from backend.app.api.v1.signals import router as signals_router
from backend.app.api.v1.training import router as training_router

api_v1_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(signals_router)
api_v1_router.include_router(analysis_router)
api_v1_router.include_router(classification_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(training_router)
api_v1_router.include_router(models_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(settings_router)

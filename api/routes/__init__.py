from api.routes.auth import router as auth_router
from api.routes.cameras import router as cameras_router
from api.routes.detections import router as detections_router
from api.routes.health import router as health_router
from api.routes.incidents import router as incidents_router

__all__ = [
    "auth_router",
    "health_router",
    "cameras_router",
    "detections_router",
    "incidents_router",
]
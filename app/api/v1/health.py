"""Health endpoints for local and orchestrated deployments."""

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter(prefix="/health", tags=["health"])


def health_payload(settings: Settings) -> dict[str, str]:
    """Return the common status payload without exposing sensitive configuration."""

    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


@router.get("", summary="Service health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Basic service health for humans and simple monitors."""

    return health_payload(settings)


@router.get("/live", summary="Liveness probe")
async def liveness(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Report whether the process can serve requests."""

    return health_payload(settings)


@router.get("/ready", summary="Readiness probe")
async def readiness(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Report whether required local application components are initialized."""

    return health_payload(settings)

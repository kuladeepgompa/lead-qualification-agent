"""Composition root for version 1 routes."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.leads import router as leads_router

router = APIRouter()
router.include_router(health_router)
router.include_router(leads_router)

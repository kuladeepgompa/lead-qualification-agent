"""Lead qualification API route."""

from fastapi import APIRouter, Depends

from app.core.logging import get_request_id
from app.schemas.lead import LeadQualificationRequest
from app.schemas.qualification import LeadQualificationResponse
from app.services.qualification_service import LeadQualificationService, get_qualification_service

router = APIRouter(prefix="/lead", tags=["lead qualification"])


@router.post(
    "/qualify",
    response_model=LeadQualificationResponse,
    summary="Qualify one inbound sales lead",
)
async def qualify_lead(
    lead: LeadQualificationRequest,
    service: LeadQualificationService = Depends(get_qualification_service),
) -> LeadQualificationResponse:
    """Generate a schema-validated qualification for a normalized lead request."""

    return await service.qualify(lead, request_id=get_request_id())

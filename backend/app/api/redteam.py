"""
Red Team Adversarial Attack Simulator REST Endpoints.
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter
from backend.app.services.redteam_simulator import redteam_simulator

router = APIRouter(prefix="/redteam", tags=["Red Team Simulator"])


class AttackCampaignRequest(BaseModel):
    campaign_type: str = Field("MICRO_SMURFING", json_schema_extra={"example": "MICRO_SMURFING"})
    intensity: int = Field(50, ge=10, le=150, json_schema_extra={"example": 50})


@router.get("/campaigns")
def get_campaign_types():
    """
    Returns available adversarial attack simulation campaigns.
    """
    return redteam_simulator.CAMPAIGNS


@router.post("/launch")
def launch_adversarial_campaign(req: AttackCampaignRequest):
    """
    Launches an automated offensive cyber attack simulation against the defense engine.
    """
    return redteam_simulator.run_campaign(req.campaign_type, req.intensity)

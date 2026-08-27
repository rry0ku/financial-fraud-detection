"""
Continuous Concept Drift & Model Health Endpoints.
"""

from fastapi import APIRouter
from backend.app.services.drift_monitor import drift_monitor

router = APIRouter(prefix="/drift", tags=["Model Drift"])


@router.get("")
def get_concept_drift():
    """
    Returns real-time Population Stability Index (PSI) and KS drift statistics.
    """
    return drift_monitor.get_drift_report()

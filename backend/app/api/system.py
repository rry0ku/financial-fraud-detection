"""
System Administration & Environment Reset Endpoints.
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db, init_db
from backend.app.models.transaction import TransactionRecord
from backend.app.models.policy_rule import PolicyRuleRecord
from backend.app.services.graph_engine import graph_engine
from backend.app.services.velocity_engine import velocity_engine
from backend.app.services.drift_monitor import drift_monitor
from scripts.seed_demo_database import generate_demo_database

router = APIRouter(prefix="/system", tags=["System Management"])


class SystemResetRequest(BaseModel):
    reseed_demo_data: bool = Field(True, json_schema_extra={"example": True})


@router.post("/reset")
def reset_system_environment(req: SystemResetRequest = SystemResetRequest(reseed_demo_data=True), db: Session = Depends(get_db)):
    """
    Performs a full environment factory reset:
    - Clears or resets all transaction records
    - Resets policy rule trigger counters
    - Clears in-memory graph networks, velocity trackers, and drift monitors
    - Re-seeds fresh demonstration dataset if requested
    """
    try:
        # 1. Reset In-Memory State Engines
        velocity_engine.history.clear()
        graph_engine._init_graph()
        drift_monitor.recent_stream.clear()

        # 2. Reset Policy Rule Trigger Counters
        rules = db.query(PolicyRuleRecord).all()
        for r in rules:
            r.trigger_count = 0
            r.is_active = True
        db.commit()

        # 3. Handle Database Records
        if req.reseed_demo_data:
            generate_demo_database(num_records=75)
            # Re-sync graph from seeded DB
            graph_engine.sync_from_database(db)
            total = db.query(TransactionRecord).count()
            return {
                "status": "success",
                "message": f"System reset successfully. Environment initialized with {total} fresh demonstration records.",
                "total_records": total,
                "reseeded": True
            }
        else:
            db.query(TransactionRecord).delete()
            db.commit()
            return {
                "status": "success",
                "message": "System reset to empty state. All transactions, telemetry, and graphs purged.",
                "total_records": 0,
                "reseeded": False
            }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"System reset failed: {str(e)}")

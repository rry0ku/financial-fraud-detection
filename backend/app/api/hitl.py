"""
Human-in-the-Loop (HITL) Analyst Review Queue Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.models.transaction import TransactionRecord
from backend.app.schemas.transaction import HitlReviewRequest

router = APIRouter(prefix="/hitl", tags=["Human in the Loop"])


@router.get("/queue")
def get_review_queue(db: Session = Depends(get_db)):
    """
    Returns transactions pending manual analyst verification or recently reviewed.
    """
    pending = db.query(TransactionRecord).filter(
        TransactionRecord.hitl_status == "PENDING_REVIEW"
    ).order_by(desc(TransactionRecord.timestamp)).limit(30).all()

    resolved = db.query(TransactionRecord).filter(
        TransactionRecord.hitl_status.in_(["CONFIRMED_FRAUD", "FALSE_POSITIVE"])
    ).order_by(desc(TransactionRecord.timestamp)).limit(20).all()

    return {
        "pending_count": len(pending),
        "pending_items": [t.to_dict() for t in pending],
        "resolved_items": [t.to_dict() for t in resolved]
    }


@router.post("/review")
def submit_analyst_review(req: HitlReviewRequest, db: Session = Depends(get_db)):
    """
    Records human analyst verdict on a flagged transaction (CONFIRMED_FRAUD / FALSE_POSITIVE).
    """
    rec = db.query(TransactionRecord).filter(TransactionRecord.transaction_id == req.transaction_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Transaction not found")

    rec.hitl_status = req.verdict
    db.commit()
    db.refresh(rec)

    return {
        "status": "success",
        "transaction_id": rec.transaction_id,
        "updated_verdict": rec.hitl_status,
        "message": f"Transaction {rec.transaction_id} marked as {req.verdict}"
    }

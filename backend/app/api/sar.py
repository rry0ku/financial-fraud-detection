"""
Regulatory SAR (Suspicious Activity Report) Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.transaction import TransactionRecord
from backend.app.schemas.transaction import SarGenerateRequest
from backend.app.services.sar_service import sar_service

router = APIRouter(prefix="/sar", tags=["Regulatory SAR"])


@router.post("")
def generate_sar(req: SarGenerateRequest, db: Session = Depends(get_db)):
    """
    Generates an official regulatory Suspicious Activity Report (SAR) for a specific transaction.
    """
    rec = db.query(TransactionRecord).filter(TransactionRecord.transaction_id == req.transaction_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn_dict = rec.to_dict()
    sar_res = sar_service.generate_sar_report(txn_dict)

    # Persist generated report
    rec.sar_report_text = sar_res["report_text"]
    db.commit()

    return sar_res

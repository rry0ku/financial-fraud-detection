"""
Transaction History and Query Endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.models.transaction import TransactionRecord

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("")
def get_transactions(
    decision: Optional[str] = Query(None, description="Filter by decision: APPROVE, FLAG, BLOCK"),
    search: Optional[str] = Query(None, description="Search by transaction ID or account name"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieves recent scored transactions with optional filtering and pagination.
    """
    query = db.query(TransactionRecord)

    if decision and decision.upper() != "ALL":
        query = query.filter(TransactionRecord.decision == decision.upper())

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (TransactionRecord.transaction_id.ilike(search_pattern)) |
            (TransactionRecord.name_orig.ilike(search_pattern)) |
            (TransactionRecord.name_dest.ilike(search_pattern))
        )

    total_count = query.count()
    records = query.order_by(desc(TransactionRecord.timestamp)).offset(offset).limit(limit).all()

    dict_records = [r.to_dict() for r in records]
    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "transactions": dict_records,
        "items": dict_records
    }


@router.get("/{transaction_id}")
def get_transaction_detail(transaction_id: str, db: Session = Depends(get_db)):
    """
    Retrieves details for a specific transaction ID.
    """
    record = db.query(TransactionRecord).filter(TransactionRecord.transaction_id == transaction_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return record.to_dict()

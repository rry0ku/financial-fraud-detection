"""
Compliance & Policy Rules REST API Endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.policy_rule import PolicyRuleRecord

router = APIRouter(prefix="/rules", tags=["Policy Rules"])


class PolicyRuleCreate(BaseModel):
    rule_code: str = Field(..., json_schema_extra={"example": "RULE-105"})
    name: str = Field(..., json_schema_extra={"example": "High Nocturnal Transfer Threshold"})
    description: Optional[str] = None
    field: str = Field(..., json_schema_extra={"example": "amount"})
    operator: str = Field(..., json_schema_extra={"example": ">"})
    value: str = Field(..., json_schema_extra={"example": "50000"})
    action: str = Field("REQUIRE_MFA", json_schema_extra={"example": "FORCE_BLOCK"})
    risk_boost: float = Field(0.0, json_schema_extra={"example": 0.25})
    priority: int = Field(10, json_schema_extra={"example": 1})
    is_active: bool = True


class PolicyRuleResponse(BaseModel):
    id: int
    rule_code: str
    name: str
    description: Optional[str]
    field: str
    operator: str
    value: str
    action: str
    risk_boost: float
    priority: int
    is_active: bool
    trigger_count: int
    created_at: Optional[str]


@router.get("", response_model=List[PolicyRuleResponse])
def get_all_rules(db: Session = Depends(get_db)):
    """
    Returns all registered policy rules and their execution trigger statistics.
    """
    rules = db.query(PolicyRuleRecord).order_by(PolicyRuleRecord.priority.asc()).all()
    return [r.to_dict() for r in rules]


@router.post("", response_model=PolicyRuleResponse)
def create_rule(rule_in: PolicyRuleCreate, db: Session = Depends(get_db)):
    """
    Registers a new deterministic policy rule.
    """
    existing = db.query(PolicyRuleRecord).filter(PolicyRuleRecord.rule_code == rule_in.rule_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Rule code {rule_in.rule_code} already exists.")

    rule = PolicyRuleRecord(
        rule_code=rule_in.rule_code,
        name=rule_in.name,
        description=rule_in.description,
        field=rule_in.field,
        operator=rule_in.operator,
        value=rule_in.value,
        action=rule_in.action,
        risk_boost=rule_in.risk_boost,
        priority=rule_in.priority,
        is_active=rule_in.is_active
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule.to_dict()


@router.put("/{rule_id}/toggle", response_model=PolicyRuleResponse)
def toggle_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Enables or disables a policy rule.
    """
    rule = db.query(PolicyRuleRecord).filter(PolicyRuleRecord.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    
    rule.is_active = not rule.is_active
    db.commit()
    db.refresh(rule)
    return rule.to_dict()


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Removes a policy rule from the database.
    """
    rule = db.query(PolicyRuleRecord).filter(PolicyRuleRecord.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    
    db.delete(rule)
    db.commit()
    return {"status": "success", "message": f"Rule {rule.rule_code} deleted."}

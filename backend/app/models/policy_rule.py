"""
SQLAlchemy Model for Deterministic Compliance & Security Policy Rules.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from backend.app.core.database import Base


class PolicyRuleRecord(Base):
    """
    Stores configurable business & cybersecurity logic rules.
    Actions: FORCE_BLOCK, REQUIRE_MFA, FAST_PASS, BOOST_RISK
    """
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rule_code = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True)
    
    # Matching Criteria
    field = Column(String(64), nullable=False)      # e.g., amount, hour, geo_velocity, balance_depletion_ratio
    operator = Column(String(16), nullable=False)   # >, <, >=, <=, ==, !=, in
    value = Column(String(128), nullable=False)     # e.g., 50000, 03:00, 1000
    
    # Action & Priority
    action = Column(String(32), nullable=False)     # FORCE_BLOCK, REQUIRE_MFA, FAST_PASS, BOOST_RISK
    risk_boost = Column(Float, default=0.0)
    priority = Column(Integer, default=10)          # Lower number = higher priority
    is_active = Column(Boolean, default=True)
    trigger_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "name": self.name,
            "description": self.description,
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
            "action": self.action,
            "risk_boost": self.risk_boost,
            "priority": self.priority,
            "is_active": self.is_active,
            "trigger_count": self.trigger_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

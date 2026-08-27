"""
SQLAlchemy Models for Transactions and Fraud Risk Decisions.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from backend.app.core.database import Base


class TransactionRecord(Base):
    """
    Stores historical transaction details, AI risk score, and system decision.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Input Transaction Features
    step = Column(Integer, default=1, nullable=False)
    type = Column(String(32), nullable=False)  # PAYMENT, TRANSFER, CASH_OUT, DEBIT, CASH_IN
    amount = Column(Float, nullable=False)
    name_orig = Column(String(64), nullable=False)
    oldbalance_orig = Column(Float, nullable=False)
    newbalance_orig = Column(Float, nullable=False)
    name_dest = Column(String(64), nullable=False)
    oldbalance_dest = Column(Float, nullable=False)
    newbalance_dest = Column(Float, nullable=False)

    # Geo Telemetry & Velocity Fields
    ip_address = Column(String(64), default="192.168.1.1", nullable=True)
    location_city = Column(String(64), default="New York", nullable=True)
    location_country = Column(String(16), default="US", nullable=True)
    latitude = Column(Float, default=40.7128, nullable=True)
    longitude = Column(Float, default=-74.0060, nullable=True)
    geo_velocity_kmh = Column(Float, default=0.0, nullable=True)
    impossible_travel_flag = Column(Boolean, default=False, nullable=True)
    velocity_count_5m = Column(Integer, default=1, nullable=True)
    velocity_sum_5m = Column(Float, default=0.0, nullable=True)

    # ML, Graph & XAI Attributions
    risk_score = Column(Float, nullable=False)  # 0.0 to 1.0
    decision = Column(String(16), nullable=False)  # APPROVE, FLAG, BLOCK
    is_fraud_predicted = Column(Boolean, default=False, nullable=False)
    flag_reasons = Column(Text, nullable=True)  # Semicolon separated reasons
    shap_values_json = Column(Text, nullable=True)  # Serialized SHAP waterfall
    graph_risk_score = Column(Float, default=0.0, nullable=True)
    mule_cycle_detected = Column(Boolean, default=False, nullable=True)

    # Human-in-the-Loop & Regulatory
    hitl_status = Column(String(32), default="AUTO_RESOLVED", nullable=False)  # PENDING_REVIEW, CONFIRMED_FRAUD, FALSE_POSITIVE, AUTO_RESOLVED
    sar_report_text = Column(Text, nullable=True)

    def to_dict(self):
        import json
        shap_data = []
        if self.shap_values_json:
            try:
                shap_data = json.loads(self.shap_values_json)
            except Exception:
                shap_data = []

        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "step": self.step,
            "type": self.type,
            "amount": self.amount,
            "name_orig": self.name_orig,
            "oldbalance_orig": self.oldbalance_orig,
            "newbalance_orig": self.newbalance_orig,
            "name_dest": self.name_dest,
            "oldbalance_dest": self.oldbalance_dest,
            "newbalance_dest": self.newbalance_dest,
            "ip_address": self.ip_address,
            "location_city": self.location_city,
            "location_country": self.location_country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "geo_velocity_kmh": round(self.geo_velocity_kmh or 0.0, 1),
            "impossible_travel_flag": self.impossible_travel_flag or False,
            "velocity_count_5m": self.velocity_count_5m or 1,
            "velocity_sum_5m": round(self.velocity_sum_5m or 0.0, 2),
            "risk_score": round(self.risk_score, 4),
            "risk_percentage": f"{round(self.risk_score * 100, 2)}%",
            "decision": self.decision,
            "is_fraud_predicted": self.is_fraud_predicted,
            "flag_reasons": self.flag_reasons.split("; ") if self.flag_reasons else [],
            "shap_values": shap_data,
            "graph_risk_score": round(self.graph_risk_score or 0.0, 3),
            "mule_cycle_detected": self.mule_cycle_detected or False,
            "hitl_status": self.hitl_status or "AUTO_RESOLVED",
            "has_sar_report": bool(self.sar_report_text)
        }

"""
Pydantic Schemas for Request & Response Data Validation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TransactionCreate(BaseModel):
    """
    Schema for evaluating a new transaction.
    """
    step: int = Field(default=1, description="Hour / Step of transaction (1-744)", ge=1)
    type: str = Field(..., description="Transaction type: PAYMENT, TRANSFER, CASH_OUT, DEBIT, CASH_IN")
    amount: float = Field(..., description="Transaction amount in USD", gt=0)
    name_orig: str = Field(default="C_USER_001", description="Sender account identifier")
    oldbalance_orig: float = Field(..., description="Sender balance before transaction", ge=0)
    newbalance_orig: float = Field(..., description="Sender balance after transaction", ge=0)
    name_dest: str = Field(default="C_USER_002", description="Receiver account identifier")
    oldbalance_dest: float = Field(default=0.0, description="Receiver balance before transaction", ge=0)
    newbalance_dest: float = Field(default=0.0, description="Receiver balance after transaction", ge=0)

    # Geo & Telemetry Fields (Optional)
    ip_address: Optional[str] = Field(default="192.168.1.100")
    location_city: Optional[str] = Field(default="New York")
    location_country: Optional[str] = Field(default="US")
    latitude: Optional[float] = Field(default=40.7128)
    longitude: Optional[float] = Field(default=-74.0060)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "step": 14,
                "type": "TRANSFER",
                "amount": 95000.00,
                "name_orig": "C123456789",
                "oldbalance_orig": 95000.00,
                "newbalance_orig": 0.00,
                "name_dest": "C987654321",
                "oldbalance_dest": 0.00,
                "newbalance_dest": 0.00,
                "location_city": "New York",
                "location_country": "US"
            }
        }
    )


class TransactionResponse(BaseModel):
    """
    Schema for prediction response and stored transaction details.
    """
    transaction_id: str
    timestamp: datetime
    step: int
    type: str
    amount: float
    name_orig: str
    oldbalance_orig: float
    newbalance_orig: float
    name_dest: str
    oldbalance_dest: float
    newbalance_dest: float
    ip_address: Optional[str] = "192.168.1.1"
    location_city: Optional[str] = "New York"
    location_country: Optional[str] = "US"
    geo_velocity_kmh: Optional[float] = 0.0
    impossible_travel_flag: Optional[bool] = False
    velocity_count_5m: Optional[int] = 1
    velocity_sum_5m: Optional[float] = 0.0
    risk_score: float
    risk_percentage: str
    decision: str  # APPROVE, FLAG, BLOCK
    is_fraud_predicted: bool
    flag_reasons: List[str]
    shap_values: Optional[List[Dict[str, Any]]] = None
    graph_risk_score: Optional[float] = 0.0
    mule_cycle_detected: Optional[bool] = False
    hitl_status: Optional[str] = "AUTO_RESOLVED"
    has_sar_report: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class BatchTransactionCreate(BaseModel):
    transactions: List[TransactionCreate]


class BatchPredictionResponse(BaseModel):
    total_processed: int
    approved_count: int
    flagged_count: int
    blocked_count: int
    results: List[TransactionResponse]


class HitlReviewRequest(BaseModel):
    transaction_id: str
    verdict: str  # CONFIRMED_FRAUD, FALSE_POSITIVE
    analyst_notes: Optional[str] = "Reviewed by compliance analyst"


class SarGenerateRequest(BaseModel):
    transaction_id: str


class AnalyticsStats(BaseModel):
    total_transactions: int
    total_approved: int
    total_flagged: int
    total_blocked: int
    fraud_rate_percentage: float
    total_volume_usd: float
    blocked_volume_usd: float
    risk_distribution: Dict[str, int]
    recent_transactions: List[Dict[str, Any]]
    model_metadata: Optional[Dict[str, Any]] = None

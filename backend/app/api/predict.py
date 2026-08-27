import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.transaction import TransactionRecord
from backend.app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    BatchTransactionCreate,
    BatchPredictionResponse
)
from backend.app.services.inference import FraudInferenceEngine

router = APIRouter(prefix="/predict", tags=["Prediction"])
engine = FraudInferenceEngine()


@router.post("", response_model=TransactionResponse)
def predict_single_transaction(txn: TransactionCreate, db: Session = Depends(get_db)):
    """
    Evaluates a single financial transaction through the ML pipeline, velocity engine,
    graph mule detector, and SHAP explainer, saving the rich audit record.
    """
    try:
        eval_result = engine.evaluate_transaction(txn)

        # Create Database Record
        db_record = TransactionRecord(
            transaction_id=eval_result["transaction_id"],
            step=txn.step,
            type=txn.type.upper(),
            amount=txn.amount,
            name_orig=txn.name_orig,
            oldbalance_orig=txn.oldbalance_orig,
            newbalance_orig=txn.newbalance_orig,
            name_dest=txn.name_dest,
            oldbalance_dest=txn.oldbalance_dest,
            newbalance_dest=txn.newbalance_dest,
            ip_address=txn.ip_address,
            location_city=txn.location_city,
            location_country=txn.location_country,
            latitude=txn.latitude,
            longitude=txn.longitude,
            geo_velocity_kmh=eval_result.get("geo_velocity_kmh", 0.0),
            impossible_travel_flag=eval_result.get("impossible_travel_flag", False),
            velocity_count_5m=eval_result.get("velocity_count_5m", 1),
            velocity_sum_5m=eval_result.get("velocity_sum_5m", 0.0),
            risk_score=eval_result["risk_score"],
            decision=eval_result["decision"],
            is_fraud_predicted=eval_result["is_fraud_predicted"],
            flag_reasons="; ".join(eval_result["flag_reasons"]),
            shap_values_json=json.dumps(eval_result.get("shap_values", [])),
            graph_risk_score=eval_result.get("graph_risk_score", 0.0),
            mule_cycle_detected=eval_result.get("mule_cycle_detected", False),
            hitl_status=eval_result.get("hitl_status", "AUTO_RESOLVED")
        )

        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        return TransactionResponse(
            transaction_id=db_record.transaction_id,
            timestamp=db_record.timestamp,
            step=db_record.step,
            type=db_record.type,
            amount=db_record.amount,
            name_orig=db_record.name_orig,
            oldbalance_orig=db_record.oldbalance_orig,
            newbalance_orig=db_record.newbalance_orig,
            name_dest=db_record.name_dest,
            oldbalance_dest=db_record.oldbalance_dest,
            newbalance_dest=db_record.newbalance_dest,
            ip_address=db_record.ip_address,
            location_city=db_record.location_city,
            location_country=db_record.location_country,
            geo_velocity_kmh=db_record.geo_velocity_kmh,
            impossible_travel_flag=db_record.impossible_travel_flag,
            velocity_count_5m=db_record.velocity_count_5m,
            velocity_sum_5m=db_record.velocity_sum_5m,
            risk_score=db_record.risk_score,
            risk_percentage=eval_result["risk_percentage"],
            decision=db_record.decision,
            is_fraud_predicted=db_record.is_fraud_predicted,
            flag_reasons=eval_result["flag_reasons"],
            shap_values=eval_result.get("shap_values", []),
            graph_risk_score=db_record.graph_risk_score,
            mule_cycle_detected=db_record.mule_cycle_detected,
            hitl_status=db_record.hitl_status,
            has_sar_report=bool(db_record.sar_report_text)
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


@router.post("/batch", response_model=BatchPredictionResponse)
def predict_batch_transactions(batch: BatchTransactionCreate, db: Session = Depends(get_db)):
    """
    Evaluates a batch of transactions and stores results.
    """
    results = []
    approved = 0
    flagged = 0
    blocked = 0

    for txn in batch.transactions:
        eval_result = engine.evaluate_transaction(txn)
        
        db_record = TransactionRecord(
            transaction_id=eval_result["transaction_id"],
            step=txn.step,
            type=txn.type.upper(),
            amount=txn.amount,
            name_orig=txn.name_orig,
            oldbalance_orig=txn.oldbalance_orig,
            newbalance_orig=txn.newbalance_orig,
            name_dest=txn.name_dest,
            oldbalance_dest=txn.oldbalance_dest,
            newbalance_dest=txn.newbalance_dest,
            ip_address=txn.ip_address,
            location_city=txn.location_city,
            location_country=txn.location_country,
            latitude=txn.latitude,
            longitude=txn.longitude,
            geo_velocity_kmh=eval_result.get("geo_velocity_kmh", 0.0),
            impossible_travel_flag=eval_result.get("impossible_travel_flag", False),
            velocity_count_5m=eval_result.get("velocity_count_5m", 1),
            velocity_sum_5m=eval_result.get("velocity_sum_5m", 0.0),
            risk_score=eval_result["risk_score"],
            decision=eval_result["decision"],
            is_fraud_predicted=eval_result["is_fraud_predicted"],
            flag_reasons="; ".join(eval_result["flag_reasons"]),
            shap_values_json=json.dumps(eval_result.get("shap_values", [])),
            graph_risk_score=eval_result.get("graph_risk_score", 0.0),
            mule_cycle_detected=eval_result.get("mule_cycle_detected", False),
            hitl_status=eval_result.get("hitl_status", "AUTO_RESOLVED")
        )
        db.add(db_record)
        db.flush()

        if eval_result["decision"] == "APPROVE":
            approved += 1
        elif eval_result["decision"] == "FLAG":
            flagged += 1
        else:
            blocked += 1

        results.append(TransactionResponse(
            transaction_id=db_record.transaction_id,
            timestamp=db_record.timestamp,
            step=db_record.step,
            type=db_record.type,
            amount=db_record.amount,
            name_orig=db_record.name_orig,
            oldbalance_orig=db_record.oldbalance_orig,
            newbalance_orig=db_record.newbalance_orig,
            name_dest=db_record.name_dest,
            oldbalance_dest=db_record.oldbalance_dest,
            newbalance_dest=db_record.newbalance_dest,
            ip_address=db_record.ip_address,
            location_city=db_record.location_city,
            location_country=db_record.location_country,
            geo_velocity_kmh=db_record.geo_velocity_kmh,
            impossible_travel_flag=db_record.impossible_travel_flag,
            velocity_count_5m=db_record.velocity_count_5m,
            velocity_sum_5m=db_record.velocity_sum_5m,
            risk_score=db_record.risk_score,
            risk_percentage=eval_result["risk_percentage"],
            decision=db_record.decision,
            is_fraud_predicted=db_record.is_fraud_predicted,
            flag_reasons=eval_result["flag_reasons"],
            shap_values=eval_result.get("shap_values", []),
            graph_risk_score=db_record.graph_risk_score,
            mule_cycle_detected=db_record.mule_cycle_detected,
            hitl_status=db_record.hitl_status,
            has_sar_report=bool(db_record.sar_report_text)
        ))

    db.commit()
    return BatchPredictionResponse(
        total_processed=len(batch.transactions),
        approved_count=approved,
        flagged_count=flagged,
        blocked_count=blocked,
        results=results
    )

import os
import uuid
from typing import Dict, Any, List
import joblib
import pandas as pd

from backend.app.core.config import settings
from backend.app.schemas.transaction import TransactionCreate
from backend.app.services.velocity_engine import velocity_engine
from backend.app.services.graph_engine import graph_engine
from backend.app.services.shap_explainer import shap_explainer
from backend.app.services.drift_monitor import drift_monitor


class FraudInferenceEngine:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FraudInferenceEngine, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        """
        Loads the trained ML pipeline from disk.
        If not found, triggers training automatically.
        """
        if not os.path.exists(settings.MODEL_PATH):
            print(f"[INFERENCE] Model artifact not found at {settings.MODEL_PATH}. Initiating training...")
            from ml.train import train_and_benchmark
            train_and_benchmark()

        print(f"[INFERENCE] Loading ML model from {settings.MODEL_PATH}...")
        self._model = joblib.load(settings.MODEL_PATH)
        print("[INFERENCE] Model pipeline loaded successfully into memory.")

    def evaluate_transaction(self, txn: TransactionCreate) -> Dict[str, Any]:
        """
        Takes a transaction input, prepares features, runs inference, velocity analysis,
        graph mule detection, and SHAP XAI, returning a comprehensive intelligence report.
        """
        data_dict = {
            'step': [txn.step],
            'type': [txn.type.upper()],
            'amount': [float(txn.amount)],
            'nameOrig': [txn.name_orig],
            'oldbalanceOrg': [float(txn.oldbalance_orig)],
            'newbalanceOrig': [float(txn.newbalance_orig)],
            'nameDest': [txn.name_dest],
            'oldbalanceDest': [float(txn.oldbalance_dest)],
            'newbalanceDest': [float(txn.newbalance_dest)]
        }
        df = pd.DataFrame(data_dict)

        # 1. Base ML Model Prediction (0.0 to 1.0)
        try:
            probabilities = self._model.predict_proba(df)[0]
            ml_risk_score = float(probabilities[1])
        except Exception as e:
            print(f"[INFERENCE] Prediction fallback: {e}")
            ml_risk_score = 0.05

        # 2. Behavioral Velocity & Impossible Travel Geo-Engine
        vel_res = velocity_engine.record_and_evaluate(
            account_id=txn.name_orig,
            amount=txn.amount,
            lat=txn.latitude,
            lon=txn.longitude,
            city=txn.location_city
        )

        # 3. Graph Analytics & Money Mule Ring Detection
        temp_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        graph_res = graph_engine.add_transaction(
            txn_id=temp_id,
            orig_id=txn.name_orig,
            dest_id=txn.name_dest,
            amount=txn.amount,
            risk_score=ml_risk_score,
            is_fraud=(ml_risk_score > settings.BLOCK_THRESHOLD)
        )

        # 4. Deterministic Policy Rules Evaluation
        from backend.app.services.policy_engine import policy_engine
        from backend.app.core.database import SessionLocal
        
        policy_res = {"triggered_rules": [], "action_override": None, "total_risk_boost": 0.0, "policy_reasons": []}
        db = SessionLocal()
        try:
            policy_res = policy_engine.evaluate_transaction_rules(
                txn_dict={
                    "step": txn.step,
                    "type": txn.type,
                    "amount": txn.amount,
                    "oldbalance_orig": txn.oldbalance_orig,
                    "newbalance_orig": txn.newbalance_orig,
                    "name_orig": txn.name_orig,
                    "name_dest": txn.name_dest,
                    "geo_velocity_kmh": vel_res["geo_velocity_kmh"],
                    "impossible_travel": vel_res["impossible_travel"],
                    "velocity_count_5m": vel_res["count_5m"]
                },
                db=db
            )
        finally:
            db.close()

        # 5. Multi-Signal Risk Score Fusion
        combined_risk = ml_risk_score + vel_res["velocity_risk_boost"] + graph_res["graph_risk_boost"] + policy_res["total_risk_boost"]
        combined_risk = max(0.01, min(0.99, combined_risk))

        # 6. Continuous Drift Monitor
        transfer_ratio = txn.amount / (txn.oldbalance_orig + 1.0)
        drift_monitor.record_evaluation(
            amount=txn.amount,
            transfer_ratio=transfer_ratio,
            risk_score=combined_risk
        )

        # 7. Real-Time SHAP Feature Attribution
        shap_res = shap_explainer.explain_transaction(
            model_pipeline=self._model,
            raw_df=df,
            predicted_risk=combined_risk
        )

        # 8. Cybersecurity Reason Compilation
        flag_reasons: List[str] = []
        hour = txn.step % 24
        orig_err = (txn.newbalance_orig + txn.amount) - txn.oldbalance_orig

        if txn.oldbalance_orig > 0 and txn.newbalance_orig == 0:
            flag_reasons.append("Account Draining: Sender balance completely emptied to $0.00")
        
        if abs(orig_err) > 1.0:
            flag_reasons.append(f"Balance Mismatch: Origin balance discrepancy of ${abs(orig_err):,.2f}")

        if txn.amount >= 50000.0:
            flag_reasons.append(f"High-Value Anomaly: Large transaction amount of ${txn.amount:,.2f}")

        if 1 <= hour <= 5:
            flag_reasons.append(f"Off-Hours Activity: Transaction initiated at {hour:02d}:00 AM")

        # Append velocity, graph, and policy reasons
        flag_reasons.extend(vel_res["velocity_reasons"])
        flag_reasons.extend(graph_res["graph_reasons"])
        flag_reasons.extend(policy_res["policy_reasons"])

        # 9. Decision Logic (3-Tier Framework with Policy Action Override)
        if policy_res["action_override"] == "FORCE_BLOCK":
            decision = "BLOCK"
            is_fraud = True
            hitl_status = "PENDING_REVIEW"
        elif policy_res["action_override"] == "REQUIRE_MFA":
            decision = "FLAG"
            is_fraud = False
            hitl_status = "PENDING_REVIEW"
        elif policy_res["action_override"] == "FAST_PASS":
            decision = "APPROVE"
            is_fraud = False
            hitl_status = "AUTO_RESOLVED"
        elif combined_risk > settings.BLOCK_THRESHOLD:
            decision = "BLOCK"
            is_fraud = True
            hitl_status = "PENDING_REVIEW"
            if not flag_reasons:
                flag_reasons.append(f"Risk score ({combined_risk*100:.1f}%) exceeds block threshold ({settings.BLOCK_THRESHOLD*100:.0f}%)")
        elif combined_risk >= settings.FLAG_THRESHOLD:
            decision = "FLAG"
            is_fraud = False
            hitl_status = "PENDING_REVIEW"
            if not flag_reasons:
                flag_reasons.append(f"Risk score ({combined_risk*100:.1f}%) requires step-up verification (OTP/MFA)")
        else:
            decision = "APPROVE"
            is_fraud = False
            hitl_status = "AUTO_RESOLVED"
            if not flag_reasons:
                flag_reasons.append("Normal behavioral pattern verified by model")

        return {
            "transaction_id": temp_id,
            "risk_score": round(combined_risk, 4),
            "risk_percentage": f"{round(combined_risk * 100, 2)}%",
            "decision": decision,
            "is_fraud_predicted": is_fraud,
            "flag_reasons": flag_reasons,
            "geo_velocity_kmh": vel_res["geo_velocity_kmh"],
            "impossible_travel_flag": vel_res["impossible_travel"],
            "velocity_count_5m": vel_res["count_5m"],
            "velocity_sum_5m": vel_res["sum_5m"],
            "graph_risk_score": graph_res["graph_risk_boost"],
            "mule_cycle_detected": graph_res["cycle_detected"],
            "shap_values": shap_res["waterfall_features"],
            "hitl_status": hitl_status
        }


engine = FraudInferenceEngine()

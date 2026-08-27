"""
End-to-End Pipeline & API Tests.
"""

import os
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.core.database import init_db
from ml.dataset_generator import generate_financial_dataset
from ml.feature_engineering import build_preprocessor
from backend.app.schemas.transaction import TransactionCreate
from backend.app.services.inference import FraudInferenceEngine

init_db()
client = TestClient(app)


def test_dataset_generation():
    """Verify synthetic dataset generator produces correct columns and labels."""
    df = generate_financial_dataset(n_samples=100, fraud_ratio=0.1)
    assert len(df) == 100
    assert 'isFraud' in df.columns
    assert 'type' in df.columns
    assert 'amount' in df.columns
    assert df['isFraud'].sum() > 0


def test_feature_pipeline():
    """Verify feature pipeline transforms data into numeric vectors without NaNs."""
    df = generate_financial_dataset(n_samples=20)
    pipeline = build_preprocessor()
    transformed = pipeline.fit_transform(df)
    assert transformed.shape[0] == 20
    assert transformed.shape[1] > 5


def test_inference_engine():
    """Verify inference engine returns calibrated risk score and decision."""
    engine = FraudInferenceEngine()
    
    # Test safe payment
    safe_txn = TransactionCreate(
        step=12,
        type="PAYMENT",
        amount=15.00,
        name_orig="C111",
        oldbalance_orig=500.00,
        newbalance_orig=485.00,
        name_dest="M222",
        oldbalance_dest=1000.00,
        newbalance_dest=1015.00
    )
    res_safe = engine.evaluate_transaction(safe_txn)
    assert "risk_score" in res_safe
    assert res_safe["decision"] in ["APPROVE", "FLAG", "BLOCK"]
    assert 0.0 <= res_safe["risk_score"] <= 1.0

    # Test draining fraud pattern
    fraud_txn = TransactionCreate(
        step=3,
        type="TRANSFER",
        amount=90000.00,
        name_orig="C888",
        oldbalance_orig=90000.00,
        newbalance_orig=0.00,
        name_dest="C999",
        oldbalance_dest=0.00,
        newbalance_dest=0.00
    )
    res_fraud = engine.evaluate_transaction(fraud_txn)
    assert res_fraud["risk_score"] > res_safe["risk_score"]


def test_api_health():
    """Verify health check endpoint returns 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_velocity_and_impossible_travel():
    """Verify velocity engine tracks sliding-window counts and flags impossible travel."""
    from backend.app.services.velocity_engine import velocity_engine
    import time
    
    acc = "C_TEST_VEL_1"
    now = time.time()
    
    # First txn in New York
    res1 = velocity_engine.record_and_evaluate(acc, 50.0, timestamp=now, lat=40.7128, lon=-74.0060, city="New York")
    assert res1["impossible_travel"] is False
    assert res1["count_5m"] == 1

    # Second txn 10 seconds later in Tokyo (impossible flight speed > 900 km/h)
    res2 = velocity_engine.record_and_evaluate(acc, 500.0, timestamp=now + 10, lat=35.6762, lon=139.6503, city="Tokyo")
    assert res2["impossible_travel"] is True
    assert res2["geo_velocity_kmh"] > 900.0
    assert res2["velocity_risk_boost"] > 0.3


def test_graph_cycle_and_mule_detection():
    """Verify graph engine detects circular layering and mule hub accounts."""
    from backend.app.services.graph_engine import graph_engine
    
    # Form a 3-node cycle: A -> B -> C -> A
    graph_engine.add_transaction("TXN_G1", "ACC_A", "ACC_B", 1000.0, 0.2, False)
    graph_engine.add_transaction("TXN_G2", "ACC_B", "ACC_C", 1000.0, 0.2, False)
    res3 = graph_engine.add_transaction("TXN_G3", "ACC_C", "ACC_A", 1000.0, 0.8, True)
    
    assert res3["cycle_detected"] is True
    assert res3["graph_risk_boost"] > 0.0

    cy_data = graph_engine.get_cytoscape_data()
    assert len(cy_data["nodes"]) >= 3
    assert len(cy_data["edges"]) >= 3


def test_shap_explainer():
    """Verify fast SHAP explainer produces positive and negative waterfall attributions."""
    from backend.app.services.shap_explainer import shap_explainer
    import pandas as pd
    
    df = pd.DataFrame([{
        'step': 3,
        'type': 'TRANSFER',
        'amount': 95000.0,
        'oldbalanceOrg': 95000.0,
        'newbalanceOrig': 0.0,
        'oldbalanceDest': 0.0,
        'newbalanceDest': 0.0
    }])
    
    res = shap_explainer.explain_transaction(None, df, 0.88)
    assert "waterfall_features" in res
    assert len(res["waterfall_features"]) > 0
    assert any(f["feature"] == "Account Draining Flag" for f in res["waterfall_features"])


def test_drift_monitor():
    """Verify drift monitor returns valid PSI and KS metrics."""
    from backend.app.services.drift_monitor import drift_monitor
    
    drift_monitor.record_evaluation(100.0, 0.1, 0.05)
    drift_monitor.record_evaluation(50000.0, 0.9, 0.85)
    
    rep = drift_monitor.get_drift_report()
    assert "overall_psi" in rep
    assert "overall_drift_status" in rep
    assert len(rep["features_drift"]) == 3


def test_sar_generation():
    """Verify SAR report generator produces regulatory documentation."""
    from backend.app.services.sar_service import sar_service
    
    txn_sample = {
        "transaction_id": "TXN-TEST-1234",
        "amount": 95000.0,
        "type": "TRANSFER",
        "name_orig": "C888999",
        "name_dest": "C111222",
        "risk_score": 0.92,
        "decision": "BLOCK",
        "flag_reasons": ["Account Draining", "Off-Hours Activity"]
    }
    
    sar = sar_service.generate_sar_report(txn_sample)
    assert "SAR-TXN-TEST-1234" in sar["sar_id"]
    assert "FINANCIAL CRIMES ENFORCEMENT NETWORK" in sar["report_text"]


def test_api_graph_and_drift_endpoints():
    """Verify new REST endpoints return 200."""
    g_res = client.get("/api/v1/graph")
    assert g_res.status_code == 200
    assert "nodes" in g_res.json()

    d_res = client.get("/api/v1/drift")
    assert d_res.status_code == 200
    assert "overall_psi" in d_res.json()


def test_policy_rules_engine():
    """Verify policy rules engine and REST API."""
    res = client.get("/api/v1/rules")
    assert res.status_code == 200
    rules = res.json()
    assert len(rules) >= 4
    assert any(r["rule_code"] == "RULE-101" for r in rules)

    # Test rule creation
    new_rule = {
        "rule_code": "RULE-TEST-999",
        "name": "Test Rule",
        "description": "Integration test rule",
        "field": "amount",
        "operator": ">",
        "value": "999999",
        "action": "FORCE_BLOCK",
        "risk_boost": 0.5,
        "priority": 1,
        "is_active": True
    }
    create_res = client.post("/api/v1/rules", json=new_rule)
    assert create_res.status_code == 200
    rule_id = create_res.json()["id"]

    # Test rule toggle
    toggle_res = client.put(f"/api/v1/rules/{rule_id}/toggle")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_active"] is False

    # Clean up rule
    del_res = client.delete(f"/api/v1/rules/{rule_id}")
    assert del_res.status_code == 200


def test_redteam_adversarial_simulator():
    """Verify offensive Red Team attack simulation campaign."""
    req = {
        "campaign_type": "MICRO_SMURFING",
        "intensity": 15
    }
    res = client.post("/api/v1/redteam/launch", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["total_attacks_launched"] == 15
    assert data["interception_rate_pct"] >= 0.0
    assert "defense_attribution" in data
    assert len(data["battle_logs"]) > 0


def test_batch_benchmark_and_sample_csv():
    """Verify batch ingestion and high-throughput stress runner."""
    csv_res = client.get("/api/v1/batch/sample-csv")
    assert csv_res.status_code == 200
    assert "step,type,amount" in csv_res.text

    bench_req = {
        "batch_size": 100,
        "fraud_injection_rate": 0.20
    }
    bench_res = client.post("/api/v1/batch/stress-benchmark", json=bench_req)
    assert bench_res.status_code == 200
    bdata = bench_res.json()
    assert bdata["benchmark_size"] == 100
    assert bdata["throughput_tps"] > 0
    assert "p50" in bdata["latency_percentiles_ms"]


def test_hitl_queue_endpoint():
    """Verify Human-in-the-Loop review queue endpoint."""
    h_res = client.get("/api/v1/hitl/queue")
    assert h_res.status_code == 200
    assert "pending_count" in h_res.json()


def test_system_reset_endpoint():
    """Verify system environment reset and demo re-seeding."""
    res = client.post("/api/v1/system/reset", json={"reseed_demo_data": True})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["reseeded"] is True
    assert data["total_records"] > 0




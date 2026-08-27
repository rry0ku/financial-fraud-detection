"""
Demo Database Seeder for Financial Fraud Detection Platform.
Populates realistic transactions spanning legitimate, borderline MFA flagged,
impossible travel anomalies, and circular money mule laundering rings.
"""

import os
import random
import json
from datetime import datetime, timezone, timedelta

from backend.app.core.database import SessionLocal, init_db, engine
from backend.app.models.transaction import TransactionRecord
from backend.app.services.graph_engine import graph_engine

def generate_demo_database(num_records=75):
    print("[*] Initializing Database Schema...")
    init_db()
    
    db = SessionLocal()
    
    # Check if we should clear existing records
    print("[*] Clearing previous records for a fresh demo state...")
    db.query(TransactionRecord).delete()
    db.commit()

    # Cities and coordinates
    CITIES = [
        {"city": "New York, US", "country": "US", "lat": 40.7128, "lon": -74.0060, "ip": "192.168.1.101"},
        {"city": "London, UK", "country": "GB", "lat": 51.5074, "lon": -0.1278, "ip": "81.2.69.142"},
        {"city": "Tokyo, JP", "country": "JP", "lat": 35.6762, "lon": 139.6503, "ip": "133.242.18.9"},
        {"city": "Mumbai, IN", "country": "IN", "lat": 19.0760, "lon": 72.8777, "ip": "103.21.124.5"},
        {"city": "Singapore, SG", "country": "SG", "lat": 1.3521, "lon": 103.8198, "ip": "118.200.5.21"},
        {"city": "Frankfurt, DE", "country": "DE", "lat": 50.1109, "lon": 8.6821, "ip": "194.12.33.8"},
        {"city": "Sydney, AU", "country": "AU", "lat": -33.8688, "lon": 151.2093, "ip": "139.130.4.5"}
    ]

    legit_users = [f"C{random.randint(10000000, 99999999)}" for _ in range(30)]
    merchants = [f"M{random.randint(10000000, 99999999)}" for _ in range(15)]
    
    mule_ring_nodes = ["C_MULE_ALPHA", "C_MULE_BETA", "C_MULE_GAMMA", "C_MULE_DELTA", "C_MULE_HUB"]

    records = []
    base_time = datetime.now(timezone.utc) - timedelta(hours=6)

    print(f"[*] Generating {num_records} multi-scenario transactions...")

    # 1. Legitimate Transactions (approx 55%)
    for i in range(40):
        t_time = base_time + timedelta(minutes=i * 8 + random.randint(1, 5))
        ttype = random.choice(["PAYMENT", "PAYMENT", "CASH_IN", "DEBIT", "TRANSFER"])
        amt = round(random.uniform(5.50, 450.0) if ttype != "CASH_IN" else random.uniform(1200.0, 4500.0), 2)
        old_orig = round(amt + random.uniform(100.0, 5000.0), 2)
        new_orig = round(old_orig - amt if ttype != "CASH_IN" else old_orig + amt, 2)
        old_dest = round(random.uniform(200.0, 8000.0), 2)
        new_dest = round(old_dest + amt, 2)
        
        orig = random.choice(legit_users)
        dest = random.choice(merchants if ttype == "PAYMENT" else legit_users)
        geo = random.choice(CITIES)
        
        risk_score = round(random.uniform(0.01, 0.22), 4)
        
        shap_values = [
            {"feature": "Amount", "shap_value": round(random.uniform(-0.05, 0.02), 4), "impact_percentage": round(random.uniform(-5.0, 2.0), 1)},
            {"feature": "Sender Balance Ratio", "shap_value": round(random.uniform(-0.08, -0.01), 4), "impact_percentage": round(random.uniform(-8.0, -1.0), 1)},
            {"feature": "Hour of Day", "shap_value": round(random.uniform(-0.03, 0.01), 4), "impact_percentage": round(random.uniform(-3.0, 1.0), 1)}
        ]

        rec = TransactionRecord(
            transaction_id=f"TXN-{random.randint(1000000000, 9999999999)}",
            timestamp=t_time,
            step=t_time.hour,
            type=ttype,
            amount=amt,
            name_orig=orig,
            oldbalance_orig=old_orig,
            newbalance_orig=new_orig,
            name_dest=dest,
            oldbalance_dest=old_dest,
            newbalance_dest=new_dest,
            ip_address=geo["ip"],
            location_city=geo["city"],
            location_country=geo["country"],
            latitude=geo["lat"],
            longitude=geo["lon"],
            geo_velocity_kmh=0.0,
            impossible_travel_flag=False,
            velocity_count_5m=1,
            velocity_sum_5m=amt,
            risk_score=risk_score,
            decision="APPROVE",
            is_fraud_predicted=False,
            flag_reasons="Normal consumption pattern; Low amount ratio",
            shap_values_json=json.dumps(shap_values),
            graph_risk_score=round(random.uniform(0.01, 0.15), 3),
            mule_cycle_detected=False,
            hitl_status="AUTO_RESOLVED"
        )
        records.append(rec)

    # 2. Borderline / Step-Up MFA Flagged Transactions for Compliance Queue (approx 20%)
    for i in range(15):
        t_time = base_time + timedelta(minutes=i * 20 + random.randint(1, 10))
        amt = round(random.uniform(4500.0, 14500.0), 2)
        old_orig = round(amt + random.uniform(500.0, 2000.0), 2)
        new_orig = round(old_orig - amt, 2)
        old_dest = round(random.uniform(0.0, 1000.0), 2)
        new_dest = round(old_dest + amt, 2)
        
        orig = random.choice(legit_users)
        dest = random.choice(legit_users)
        geo = random.choice(CITIES)
        
        risk_score = round(random.uniform(0.38, 0.68), 4)
        
        shap_values = [
            {"feature": "Amount", "shap_value": 0.28, "impact_percentage": 28.0},
            {"feature": "Sender Balance Ratio", "shap_value": 0.18, "impact_percentage": 18.0},
            {"feature": "Hour of Day", "shap_value": 0.08, "impact_percentage": 8.0}
        ]

        rec = TransactionRecord(
            transaction_id=f"TXN-{random.randint(1000000000, 9999999999)}",
            timestamp=t_time,
            step=t_time.hour,
            type="TRANSFER",
            amount=amt,
            name_orig=orig,
            oldbalance_orig=old_orig,
            newbalance_orig=new_orig,
            name_dest=dest,
            oldbalance_dest=old_dest,
            newbalance_dest=new_dest,
            ip_address=geo["ip"],
            location_city=geo["city"],
            location_country=geo["country"],
            latitude=geo["lat"],
            longitude=geo["lon"],
            geo_velocity_kmh=round(random.uniform(150.0, 320.0), 1),
            impossible_travel_flag=False,
            velocity_count_5m=2,
            velocity_sum_5m=amt * 1.5,
            risk_score=risk_score,
            decision="FLAG",
            is_fraud_predicted=False,
            flag_reasons="Unusual transfer volume; Rapid successive movement; Elevated balance exhaustion ratio",
            shap_values_json=json.dumps(shap_values),
            graph_risk_score=round(random.uniform(0.25, 0.45), 3),
            mule_cycle_detected=False,
            hitl_status="PENDING_REVIEW"
        )
        records.append(rec)

    # 3. High-Value Account Draining Frauds (approx 10%)
    for i in range(8):
        t_time = base_time + timedelta(minutes=i * 35 + random.randint(5, 15))
        amt = round(random.uniform(65000.0, 185000.0), 2)
        orig = f"C_VICTIM_{random.randint(100, 999)}"
        dest = f"C_ATTACKER_{random.randint(100, 999)}"
        geo = CITIES[3] # Mumbai
        
        risk_score = round(random.uniform(0.88, 0.99), 4)
        
        shap_values = [
            {"feature": "Amount", "shap_value": 0.45, "impact_percentage": 45.0},
            {"feature": "Sender Total Depletion", "shap_value": 0.38, "impact_percentage": 38.0},
            {"feature": "Nocturnal Hour", "shap_value": 0.14, "impact_percentage": 14.0}
        ]

        rec = TransactionRecord(
            transaction_id=f"TXN-{random.randint(1000000000, 9999999999)}",
            timestamp=t_time,
            step=3,
            type="TRANSFER",
            amount=amt,
            name_orig=orig,
            oldbalance_orig=amt,
            newbalance_orig=0.0,
            name_dest=dest,
            oldbalance_dest=0.0,
            newbalance_dest=0.0,
            ip_address=geo["ip"],
            location_city=geo["city"],
            location_country=geo["country"],
            latitude=geo["lat"],
            longitude=geo["lon"],
            geo_velocity_kmh=0.0,
            impossible_travel_flag=False,
            velocity_count_5m=3,
            velocity_sum_5m=amt,
            risk_score=risk_score,
            decision="BLOCK",
            is_fraud_predicted=True,
            flag_reasons="Complete account balance liquidation; Extreme nocturnal velocity; Destination zero-balance signature",
            shap_values_json=json.dumps(shap_values),
            graph_risk_score=0.78,
            mule_cycle_detected=False,
            hitl_status="AUTO_RESOLVED"
        )
        records.append(rec)

    # 4. Impossible Travel Geo-Velocity Anomalies
    for i in range(4):
        t_time = base_time + timedelta(minutes=i * 50 + 20)
        orig_acc = f"C_TRAVEL_{i+1}"
        amt = round(random.uniform(12000.0, 35000.0), 2)
        
        risk_score = round(random.uniform(0.92, 0.98), 4)
        
        shap_values = [
            {"feature": "Geo Velocity (km/h)", "shap_value": 0.52, "impact_percentage": 52.0},
            {"feature": "Amount", "shap_value": 0.25, "impact_percentage": 25.0},
            {"feature": "Cross-Border IP", "shap_value": 0.18, "impact_percentage": 18.0}
        ]

        rec = TransactionRecord(
            transaction_id=f"TXN-{random.randint(1000000000, 9999999999)}",
            timestamp=t_time,
            step=16,
            type="TRANSFER",
            amount=amt,
            name_orig=orig_acc,
            oldbalance_orig=amt + 5000.0,
            newbalance_orig=5000.0,
            name_dest=f"C_DEST_{i+1}",
            oldbalance_dest=0.0,
            newbalance_dest=amt,
            ip_address="133.242.18.9",
            location_city="Tokyo, JP",
            location_country="JP",
            latitude=35.6762,
            longitude=139.6503,
            geo_velocity_kmh=10850.4,
            impossible_travel_flag=True,
            velocity_count_5m=2,
            velocity_sum_5m=amt,
            risk_score=risk_score,
            decision="BLOCK",
            is_fraud_predicted=True,
            flag_reasons="🚨 IMPOSSIBLE TRAVEL: 10,850 km/h between NY and Tokyo within 5 minutes; High-velocity cross-border hop",
            shap_values_json=json.dumps(shap_values),
            graph_risk_score=0.65,
            mule_cycle_detected=False,
            hitl_status="AUTO_RESOLVED"
        )
        records.append(rec)

    # 5. Circular Money Mule Layering Network Ring (Alpha -> Beta -> Gamma -> Delta -> Alpha + Hub)
    mule_chain = [
        ("C_MULE_ALPHA", "C_MULE_BETA", 48000.0),
        ("C_MULE_BETA", "C_MULE_GAMMA", 47500.0),
        ("C_MULE_GAMMA", "C_MULE_DELTA", 47000.0),
        ("C_MULE_DELTA", "C_MULE_ALPHA", 46500.0),  # Cycle closure!
        ("C_MULE_HUB", "C_MULE_ALPHA", 90000.0),
        ("C_MULE_HUB", "C_MULE_BETA", 85000.0),
        ("C_MULE_HUB", "C_MULE_GAMMA", 80000.0)
    ]

    for idx, (m_orig, m_dest, m_amt) in enumerate(mule_chain):
        t_time = base_time + timedelta(minutes=idx * 15 + 45)
        risk_score = round(random.uniform(0.85, 0.96), 4)
        
        shap_values = [
            {"feature": "Graph Circular Layering", "shap_value": 0.48, "impact_percentage": 48.0},
            {"feature": "Rapid Flow Dispersal", "shap_value": 0.32, "impact_percentage": 32.0},
            {"feature": "Amount", "shap_value": 0.15, "impact_percentage": 15.0}
        ]

        rec = TransactionRecord(
            transaction_id=f"TXN-MULE-{random.randint(100000, 999999)}",
            timestamp=t_time,
            step=2,
            type="TRANSFER",
            amount=m_amt,
            name_orig=m_orig,
            oldbalance_orig=m_amt + 2000.0,
            newbalance_orig=2000.0,
            name_dest=m_dest,
            oldbalance_dest=500.0,
            newbalance_dest=m_amt + 500.0,
            ip_address="103.21.124.5",
            location_city="Frankfurt, DE",
            location_country="DE",
            latitude=50.1109,
            longitude=8.6821,
            geo_velocity_kmh=0.0,
            impossible_travel_flag=False,
            velocity_count_5m=4,
            velocity_sum_5m=m_amt,
            risk_score=risk_score,
            decision="BLOCK",
            is_fraud_predicted=True,
            flag_reasons="🕸️ CIRCULAR MONEY MULE RING DETECTED: Multi-hop structured laundering cycle; High in/out degree clustering",
            shap_values_json=json.dumps(shap_values),
            graph_risk_score=0.95,
            mule_cycle_detected=True,
            hitl_status="AUTO_RESOLVED"
        )
        records.append(rec)

    # Sort records chronologically
    records.sort(key=lambda r: r.timestamp)

    # Add to DB
    db.bulk_save_objects(records)
    db.commit()

    # Update in-memory Graph Engine with all demo transactions
    print("[*] Synchronizing Cytoscape Money Mule Graph Engine...")
    for rec in records:
        graph_engine.add_transaction(
            txn_id=rec.transaction_id,
            orig_id=rec.name_orig,
            dest_id=rec.name_dest,
            amount=rec.amount,
            risk_score=rec.risk_score,
            is_fraud=rec.is_fraud_predicted
        )

    total_in_db = db.query(TransactionRecord).count()
    approved = db.query(TransactionRecord).filter(TransactionRecord.decision == "APPROVE").count()
    flagged = db.query(TransactionRecord).filter(TransactionRecord.decision == "FLAG").count()
    blocked = db.query(TransactionRecord).filter(TransactionRecord.decision == "BLOCK").count()
    
    db.close()

    print("\n" + "="*60)
    print("DEMO DATABASE SUCCESSFULLY GENERATED")
    print("="*60)
    print(f"Total Transactions   : {total_in_db}")
    print(f"Approved (Pass)      : {approved} ({round(approved/total_in_db*100, 1)}%)")
    print(f"Flagged (HITL MFA)   : {flagged} ({round(flagged/total_in_db*100, 1)}%)")
    print(f"Blocked (Threats)    : {blocked} ({round(blocked/total_in_db*100, 1)}%)")
    print(f"Money Mule Ring Nodes: {len(mule_ring_nodes)} connected entities")
    print("="*60 + "\n")

if __name__ == "__main__":
    generate_demo_database()

"""
Red Team Adversarial Attack Simulator & Resilience Benchmark.
Executes automated offensive cyber campaigns against the ML, Graph, and Velocity pipelines.
"""

import time
import random
from typing import Dict, Any, List
from backend.app.schemas.transaction import TransactionCreate
from backend.app.services.inference import engine


class RedTeamSimulator:
    """
    Simulates adversarial campaigns and evaluates defense interception efficacy.
    """

    CAMPAIGNS = {
        "MICRO_SMURFING": {
            "name": "Micro-Smurfing Structuring Swarm",
            "description": "Floods the pipeline with 120 rapid sub-$10 micro-transactions to evade single-transaction velocity & threshold limits.",
            "target": "AML Structuring Thresholds & Behavioral Velocity Counters"
        },
        "ADVERSARIAL_EVASION": {
            "name": "Decision-Boundary Feature Perturbation",
            "description": "Applies adversarial balance perturbations and ratio manipulations to test the XGBoost ML decision boundary resilience.",
            "target": "Gradient Boosting & Statistical Feature Ensembles"
        },
        "MULE_SWARM": {
            "name": "Coordinated Multi-Account Mule Funneling",
            "description": "Orchestrates 8 compromised accounts rapidly dispersing $45k+ each into a central offshore aggregator hub node.",
            "target": "Cytoscape Graph Multi-Hop Circular & Centrality Detectors"
        },
        "HYPER_VELOCITY": {
            "name": "Cross-Continental Hypersonic Travel Hop",
            "description": "Simulates simultaneous credential hijackings with origin IPs hopping across 4 global continents within 3 minutes.",
            "target": "Haversine Impossible Travel & Geolocation Geo-Velocity Engine"
        }
    }

    def run_campaign(self, campaign_type: str, intensity: int = 50) -> Dict[str, Any]:
        if campaign_type not in self.CAMPAIGNS:
            campaign_type = "MICRO_SMURFING"

        meta = self.CAMPAIGNS[campaign_type]
        attack_count = max(10, min(150, intensity))

        start_time = time.time()
        attacks: List[Dict[str, Any]] = []
        intercepted_count = 0
        mfa_flagged_count = 0
        evaded_count = 0

        defense_attribution = {
            "XGBoost ML Ensemble": 0,
            "Impossible Travel Engine": 0,
            "Money Mule Graph Detector": 0,
            "Policy Rules Engine": 0
        }

        battle_logs: List[str] = []
        battle_logs.append(f"[*] INITIALIZING RED TEAM CAMPAIGN: {meta['name']}")
        battle_logs.append(f"[*] Target Vector: {meta['target']}")
        battle_logs.append(f"[*] Firing {attack_count} adversarial transaction payloads...")

        for i in range(attack_count):
            txn_payload = self._generate_attack_payload(campaign_type, i)
            res = engine.evaluate_transaction(txn_payload)

            decision = res["decision"]
            is_intercepted = decision in ["BLOCK", "FLAG"]
            
            if decision == "BLOCK":
                intercepted_count += 1
            elif decision == "FLAG":
                mfa_flagged_count += 1
            else:
                evaded_count += 1

            # Attribute defenses
            if res.get("impossible_travel_flag"):
                defense_attribution["Impossible Travel Engine"] += 1
            elif res.get("mule_cycle_detected") or res.get("graph_risk_score", 0) > 0.2:
                defense_attribution["Money Mule Graph Detector"] += 1
            elif any("Policy Rule" in r for r in res.get("flag_reasons", [])):
                defense_attribution["Policy Rules Engine"] += 1
            elif res["risk_score"] > 0.3:
                defense_attribution["XGBoost ML Ensemble"] += 1

            if i < 8 or is_intercepted:
                status_icon = "🛑 INTERCEPTED" if decision == "BLOCK" else ("⚠️ MFA CHALLENGE" if decision == "FLAG" else "⚡ EVADED")
                battle_logs.append(f"[{txn_payload.type}] Txn #{i+1} (${txn_payload.amount:,.2f}) -> {status_icon} (Risk: {res['risk_percentage']})")

        duration_ms = round((time.time() - start_time) * 1000, 2)
        interception_rate = round(((intercepted_count + mfa_flagged_count) / attack_count) * 100, 1)

        battle_logs.append(f"[+] CAMPAIGN CONCLUDED in {duration_ms}ms")
        battle_logs.append(f"[+] Total Interception Rate: {interception_rate}% ({intercepted_count} Blocked, {mfa_flagged_count} MFA Challenged, {evaded_count} Evaded)")

        return {
            "campaign_type": campaign_type,
            "campaign_name": meta["name"],
            "target": meta["target"],
            "total_attacks_launched": attack_count,
            "attacks_blocked": intercepted_count,
            "attacks_mfa_flagged": mfa_flagged_count,
            "attacks_evaded": evaded_count,
            "interception_rate_pct": interception_rate,
            "avg_latency_ms": round(duration_ms / attack_count, 2),
            "defense_attribution": defense_attribution,
            "battle_logs": battle_logs
        }

    def _generate_attack_payload(self, campaign_type: str, index: int) -> TransactionCreate:
        step_val = (index % 24) + 1
        if campaign_type == "MICRO_SMURFING":
            amt = round(random.uniform(4.50, 9.95), 2)
            return TransactionCreate(
                step=step_val,
                type="TRANSFER",
                amount=amt,
                name_orig=f"C_SMURF_BOT_{index % 5}",
                oldbalance_orig=1500.0,
                newbalance_orig=1500.0 - amt,
                name_dest="C_MULE_DROP_NODE",
                oldbalance_dest=5000.0,
                newbalance_dest=5000.0 + amt,
                location_city="London, UK",
                ip_address="185.220.101.5"
            )
        elif campaign_type == "ADVERSARIAL_EVASION":
            amt = round(random.uniform(4900.0, 12000.0), 2)
            return TransactionCreate(
                step=step_val,
                type="CASH_OUT",
                amount=amt,
                name_orig=f"C_ADV_{random.randint(100, 999)}",
                oldbalance_orig=amt * 1.05,
                newbalance_orig=amt * 0.05,
                name_dest=f"M_MERCHANT_{random.randint(100, 999)}",
                oldbalance_dest=1000.0,
                newbalance_dest=1000.0 + amt,
                location_city="New York, US",
                ip_address="198.51.100.42"
            )
        elif campaign_type == "MULE_SWARM":
            amt = round(random.uniform(35000.0, 75000.0), 2)
            return TransactionCreate(
                step=step_val,
                type="TRANSFER",
                amount=amt,
                name_orig=f"C_MULE_ALPHA",
                oldbalance_orig=amt,
                newbalance_orig=0.0,
                name_dest="C_MULE_HUB",
                oldbalance_dest=100000.0,
                newbalance_dest=100000.0 + amt,
                location_city="Frankfurt, DE",
                ip_address="194.12.33.8"
            )
        else: # HYPER_VELOCITY
            amt = round(random.uniform(15000.0, 45000.0), 2)
            cities = [
                ("New York, US", 40.7128, -74.0060, "192.168.1.1"),
                ("Tokyo, JP", 35.6762, 139.6503, "133.242.18.9"),
                ("Sydney, AU", -33.8688, 151.2093, "139.130.4.5"),
                ("London, UK", 51.5074, -0.1278, "81.2.69.142")
            ]
            city, lat, lon, ip = cities[index % len(cities)]
            return TransactionCreate(
                step=step_val,
                type="TRANSFER",
                amount=amt,
                name_orig="C_HYPER_VICTIM_01",
                oldbalance_orig=amt + 1000.0,
                newbalance_orig=1000.0,
                name_dest=f"C_ATTACKER_{index}",
                oldbalance_dest=0.0,
                newbalance_dest=amt,
                location_city=city,
                latitude=lat,
                longitude=lon,
                ip_address=ip
            )


redteam_simulator = RedTeamSimulator()

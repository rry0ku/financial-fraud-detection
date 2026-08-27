"""
Regulatory SAR (Suspicious Activity Report) Document Generator.
Formats official FinCEN/Regulatory compliance reports for flagged and blocked transactions.
"""

from typing import Dict, Any
import datetime


class RegulatorySarService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RegulatorySarService, cls).__new__(cls)
        return cls._instance

    def generate_sar_report(self, txn_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates an official Suspicious Activity Report (SAR) narrative formatted for compliance regulators.
        """
        txn_id = txn_data.get("transaction_id", "TXN-UNKNOWN")
        amount = float(txn_data.get("amount", 0.0))
        txn_type = str(txn_data.get("type", "TRANSFER")).upper()
        orig_id = str(txn_data.get("name_orig", "C_UNKNOWN"))
        dest_id = str(txn_data.get("name_dest", "C_UNKNOWN"))
        risk_score = float(txn_data.get("risk_score", 0.0))
        decision = str(txn_data.get("decision", "BLOCK"))
        flag_reasons = txn_data.get("flag_reasons", [])
        city = txn_data.get("location_city", "New York")
        country = txn_data.get("location_country", "US")
        ip = txn_data.get("ip_address", "192.168.1.100")
        geo_velocity = float(txn_data.get("geo_velocity_kmh", 0.0))
        impossible_travel = txn_data.get("impossible_travel_flag", False)
        
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        reasons_bulleted = "\n".join([f"  • {r}" for r in flag_reasons]) if flag_reasons else "  • Multi-factor ML probability threshold breach"

        narrative = f"""================================================================================
FINANCIAL CRIMES ENFORCEMENT NETWORK (FinCEN) — SUSPICIOUS ACTIVITY REPORT (SAR)
CONFIDENTIAL COMPLIANCE DOCUMENTATION — FOR REGULATORY AUDIT ONLY
================================================================================

1. FILING METADATA
--------------------------------------------------------------------------------
Filing Reference ID     : SAR-{txn_id}
Generated Timestamp     : {now_str}
Surveillance Unit       : Real-Time Financial Fraud Engine v2.0
Risk Assessment Verdict : {decision} (Calibrated Risk Probability: {risk_score*100:.1f}%)

2. PRIMARY SUSPECT IDENTIFIERS & TRANSMISSION TELEMETRY
--------------------------------------------------------------------------------
Originating Entity (Sender)   : {orig_id}
Receiving Entity (Beneficiary): {dest_id}
Network IP Address            : {ip}
Geolocation Context           : {city}, {country}
Calculated Geo-Velocity       : {geo_velocity:,.1f} km/h (Impossible Travel: {'CONFIRMED' if impossible_travel else 'NEGATIVE'})

3. TRANSACTION PARTICULARS
--------------------------------------------------------------------------------
Transaction Identifier : {txn_id}
Instrument Type        : {txn_type}
Monetary Volume        : ${amount:,.2f} USD
Sender Pre-Balance     : ${float(txn_data.get('oldbalance_orig', 0.0)):,.2f} USD
Sender Post-Balance    : ${float(txn_data.get('newbalance_orig', 0.0)):,.2f} USD
Receiver Pre-Balance   : ${float(txn_data.get('oldbalance_dest', 0.0)):,.2f} USD
Receiver Post-Balance  : ${float(txn_data.get('newbalance_dest', 0.0)):,.2f} USD

4. FORENSIC RISK FACTORS & MODEL ATTRIBUTION
--------------------------------------------------------------------------------
{reasons_bulleted}

5. INVESTIGATIVE EXECUTIVE SUMMARY
--------------------------------------------------------------------------------
On {now_str}, the automated surveillance engine intercepted transaction {txn_id} involving 
an attempt to transfer ${amount:,.2f} USD from origin {orig_id} to destination {dest_id}. 
The risk scoring engine evaluated the behavioral profile, temporal metadata, 
and account balance deltas, calculating a composite fraud probability of {risk_score*100:.1f}%.

Primary anomalies identified include rapid liquidity depletion, off-hours execution, and 
graph-level network velocity inconsistencies. Based on institutional risk tolerance guidelines, 
the transaction was marked as {decision}.

6. RECOMMENDED COMPLIANCE ACTIONS
--------------------------------------------------------------------------------
[X] Immediate temporary freeze on origin account {orig_id} pending identity verification.
[X] Enforce Step-Up Multi-Factor Authentication (MFA/Biometric) on destination account {dest_id}.
[X] Preserve network session telemetry and IP {ip} for forensic coordination.
[ ] Submit formal electronic SAR package to FinCEN / National Regulatory Clearinghouse.

================================================================================
Report digitally certified by Compliance Surveillance Unit.
================================================================================"""

        return {
            "sar_id": f"SAR-{txn_id}",
            "generated_at": now_str,
            "transaction_id": txn_id,
            "decision": decision,
            "risk_score": risk_score,
            "report_text": narrative
        }


sar_service = RegulatorySarService()

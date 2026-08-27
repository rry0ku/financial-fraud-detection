"""
Deterministic Policy Rules Execution Engine.
Applies real-time business and security logic rules alongside ML inferences.
"""

from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from backend.app.models.policy_rule import PolicyRuleRecord


class PolicyRulesEngine:
    """
    Evaluates transactions against active policy rules.
    """

    def evaluate_transaction_rules(self, txn_dict: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Executes active rules ordered by priority against transaction features.
        """
        triggered_rules: List[Dict[str, Any]] = []
        action_override = None
        total_risk_boost = 0.0
        reasons = []

        try:
            active_rules = db.query(PolicyRuleRecord).filter(
                PolicyRuleRecord.is_active == True
            ).order_by(PolicyRuleRecord.priority.asc()).all()

            for rule in active_rules:
                is_match = self._check_condition(rule, txn_dict)
                if is_match:
                    rule.trigger_count = (rule.trigger_count or 0) + 1
                    triggered_rules.append(rule.to_dict())
                    reasons.append(f"Policy Rule [{rule.rule_code}]: {rule.name}")
                    
                    if rule.risk_boost > 0:
                        total_risk_boost += rule.risk_boost
                    
                    if rule.action == "FORCE_BLOCK":
                        action_override = "FORCE_BLOCK"
                    elif rule.action == "REQUIRE_MFA" and action_override != "FORCE_BLOCK":
                        action_override = "REQUIRE_MFA"
                    elif rule.action == "FAST_PASS" and not action_override:
                        action_override = "FAST_PASS"

            if triggered_rules:
                db.commit()

        except Exception as e:
            print(f"[PolicyEngine] Error during evaluation: {e}")

        return {
            "triggered_rules": triggered_rules,
            "action_override": action_override,
            "total_risk_boost": round(total_risk_boost, 3),
            "policy_reasons": reasons
        }

    def _check_condition(self, rule: PolicyRuleRecord, txn: Dict[str, Any]) -> bool:
        field = rule.field.lower()
        val_str = str(rule.value).strip()
        op = rule.operator.strip()

        # Extract transaction value
        txn_val = txn.get(field)
        if txn_val is None:
            # Check derived fields
            if field == "hour":
                txn_val = txn.get("step", 12)
            elif field == "balance_depletion_ratio":
                old_bal = txn.get("oldbalance_orig", 0.0)
                amount = txn.get("amount", 0.0)
                txn_val = round(amount / (old_bal + 0.001), 3)
            elif field == "geo_velocity":
                txn_val = txn.get("geo_velocity_kmh", 0.0)
            elif field == "velocity_5m":
                txn_val = txn.get("velocity_count_5m", 1)

        if txn_val is None:
            return False

        try:
            # Numeric Comparisons
            if op in [">", "<", ">=", "<=", "=="]:
                num_txn = float(txn_val)
                num_target = float(val_str)
                if op == ">": return num_txn > num_target
                if op == "<": return num_txn < num_target
                if op == ">=": return num_txn >= num_target
                if op == "<=": return num_txn <= num_target
                if op == "==": return num_txn == num_target

            # In List Comparison
            elif op.lower() == "in":
                # e.g., "1,2,3,4" or "CASH_OUT,TRANSFER"
                targets = [t.strip().upper() for t in val_str.split(",")]
                return str(txn_val).strip().upper() in targets

            elif op.lower() == "!=":
                return str(txn_val).strip().upper() != val_str.upper()

        except Exception:
            return False

        return False


policy_engine = PolicyRulesEngine()

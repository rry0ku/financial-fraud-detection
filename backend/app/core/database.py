"""
Database Connection & Session Management.
Compatible with both SQLite (zero-config local) and MySQL (production/academic).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session and ensures closure after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy import inspect, text

def init_db():
    """
    Initializes database tables and automatically adds any missing columns.
    """
    import backend.app.models.transaction  # noqa: F401
    import backend.app.models.policy_rule  # noqa: F401
    Base.metadata.create_all(bind=engine)
    
    # Auto-migrate missing columns in SQLite if schema was expanded
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            inspector = inspect(engine)
            if "transactions" in inspector.get_table_names():
                existing_cols = {col["name"] for col in inspector.get_columns("transactions")}
                
                required_cols = {
                    "ip_address": "VARCHAR(64)",
                    "location_city": "VARCHAR(128)",
                    "location_country": "VARCHAR(64)",
                    "latitude": "FLOAT",
                    "longitude": "FLOAT",
                    "geo_velocity_kmh": "FLOAT DEFAULT 0.0",
                    "impossible_travel_flag": "BOOLEAN DEFAULT 0",
                    "velocity_count_5m": "INTEGER DEFAULT 1",
                    "velocity_sum_5m": "FLOAT DEFAULT 0.0",
                    "shap_values_json": "TEXT",
                    "graph_risk_score": "FLOAT DEFAULT 0.0",
                    "mule_cycle_detected": "BOOLEAN DEFAULT 0",
                    "hitl_status": "VARCHAR(32) DEFAULT 'AUTO_RESOLVED'",
                    "sar_report_text": "TEXT"
                }
                
                for col_name, col_type in required_cols.items():
                    if col_name not in existing_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            pass

    # Seed default compliance rules if empty
    from backend.app.models.policy_rule import PolicyRuleRecord
    db = SessionLocal()
    try:
        if db.query(PolicyRuleRecord).count() == 0:
            default_rules = [
                PolicyRuleRecord(
                    rule_code="RULE-101",
                    name="Extreme Nocturnal Value Liquidation",
                    description="Force block transactions exceeding $75,000 initiated between 1 AM and 4 AM",
                    field="amount",
                    operator=">",
                    value="75000",
                    action="FORCE_BLOCK",
                    risk_boost=0.45,
                    priority=1,
                    is_active=True
                ),
                PolicyRuleRecord(
                    rule_code="RULE-102",
                    name="Supersonic Geo-Velocity Travel Intercept",
                    description="Force block transactions with calculated physical speed > 800 km/h",
                    field="geo_velocity",
                    operator=">",
                    value="800",
                    action="FORCE_BLOCK",
                    risk_boost=0.50,
                    priority=2,
                    is_active=True
                ),
                PolicyRuleRecord(
                    rule_code="RULE-103",
                    name="High Velocity Transfer Spike",
                    description="Require step-up MFA when more than 3 transactions occur in 5 minutes",
                    field="velocity_5m",
                    operator=">=",
                    value="3",
                    action="REQUIRE_MFA",
                    risk_boost=0.20,
                    priority=3,
                    is_active=True
                ),
                PolicyRuleRecord(
                    rule_code="RULE-104",
                    name="Complete Origin Balance Depletion",
                    description="Flag when single transaction drains more than 98% of total account balance",
                    field="balance_depletion_ratio",
                    operator=">=",
                    value="0.98",
                    action="REQUIRE_MFA",
                    risk_boost=0.25,
                    priority=4,
                    is_active=True
                )
            ]
            db.bulk_save_objects(default_rules)
            db.commit()
    except Exception as e:
        print(f"[DB] Error seeding rules: {e}")
    finally:
        db.close()

    db_type = settings.DATABASE_URL.split("://")[0].upper()
    print(f"[DB] Database initialized successfully ({db_type})")

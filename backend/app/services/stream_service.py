"""
High-Throughput WebSocket Live Transaction Stream Generator.
Simulates realistic continuous payment streams (1-10 TPS) with live WebSocket broadcasting.
"""

import asyncio
import random
import time
from typing import Set
from fastapi import WebSocket

from backend.app.schemas.transaction import TransactionCreate
from backend.app.services.inference import FraudInferenceEngine


CITIES = [
    ("New York", "US", 40.7128, -74.0060, "192.168.1.45"),
    ("London", "UK", 51.5074, -0.1278, "81.2.69.142"),
    ("Tokyo", "JP", 35.6762, 139.6503, "133.242.18.9"),
    ("Mumbai", "IN", 19.0760, 72.8777, "103.21.124.5"),
    ("Singapore", "SG", 1.3521, 103.8198, "165.225.112.4"),
    ("Sydney", "AU", -33.8688, 151.2093, "139.130.4.5")
]


class StreamManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.is_running = False
        self._task = None
        self.engine = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._stream_loop())

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        if not self.active_connections:
            self.is_running = False
            if self._task:
                self._task.cancel()
                self._task = None

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.active_connections.discard(connection)

    async def _stream_loop(self):
        if self.engine is None:
            self.engine = FraudInferenceEngine()

        mule_cycle_pool = ["C101010", "C202020", "C303030"]
        cycle_idx = 0

        while self.is_running:
            try:
                # 85% legitimate, 15% suspicious/fraud/mule/travel
                rand_val = random.random()
                city, country, lat, lon, ip = random.choice(CITIES)
                
                if rand_val < 0.70:
                    # Legitimate Point of Sale / Payment
                    txn_type = random.choice(["PAYMENT", "CASH_IN", "DEBIT"])
                    amount = round(random.uniform(5.0, 350.0), 2)
                    old_orig = round(random.uniform(amount * 1.5, amount * 10 + 500), 2)
                    new_orig = round(old_orig - amount, 2)
                    orig_id = f"C{random.randint(1000000, 9999999)}"
                    dest_id = f"M{random.randint(1000000, 9999999)}"
                    step = int(time.time() % 86400 / 3600) + random.randint(8, 20)

                elif rand_val < 0.85:
                    # Normal Transfer
                    txn_type = "TRANSFER"
                    amount = round(random.uniform(500.0, 4500.0), 2)
                    old_orig = round(amount + random.uniform(2000.0, 15000.0), 2)
                    new_orig = round(old_orig - amount, 2)
                    orig_id = f"C{random.randint(1000000, 9999999)}"
                    dest_id = f"C{random.randint(1000000, 9999999)}"
                    step = random.randint(9, 18)

                elif rand_val < 0.93:
                    # High Risk Account Drain at Night
                    txn_type = random.choice(["TRANSFER", "CASH_OUT"])
                    amount = round(random.uniform(25000.0, 98000.0), 2)
                    old_orig = amount
                    new_orig = 0.0
                    orig_id = f"C{random.randint(1000000, 9999999)}"
                    dest_id = f"C{random.randint(1000000, 9999999)}"
                    step = random.randint(1, 5)

                else:
                    # Circular Mule Ring Transfer
                    txn_type = "TRANSFER"
                    orig_id = mule_cycle_pool[cycle_idx % len(mule_cycle_pool)]
                    dest_id = mule_cycle_pool[(cycle_idx + 1) % len(mule_cycle_pool)]
                    cycle_idx += 1
                    amount = round(random.uniform(15000.0, 50000.0), 2)
                    old_orig = amount + 500.0
                    new_orig = 500.0
                    step = 3

                txn_obj = TransactionCreate(
                    step=step,
                    type=txn_type,
                    amount=amount,
                    name_orig=orig_id,
                    oldbalance_orig=old_orig,
                    newbalance_orig=new_orig,
                    name_dest=dest_id,
                    oldbalance_dest=random.uniform(0, 5000),
                    newbalance_dest=random.uniform(0, 5000) + amount,
                    location_city=city,
                    location_country=country,
                    latitude=lat,
                    longitude=lon,
                    ip_address=ip
                )

                eval_result = self.engine.evaluate_transaction(txn_obj)
                
                payload = {
                    "event": "NEW_TRANSACTION",
                    "timestamp": datetime_str(),
                    "transaction": {
                        "transaction_id": eval_result["transaction_id"],
                        "type": txn_obj.type,
                        "amount": txn_obj.amount,
                        "name_orig": txn_obj.name_orig,
                        "name_dest": txn_obj.name_dest,
                        "risk_score": eval_result["risk_score"],
                        "risk_percentage": eval_result["risk_percentage"],
                        "decision": eval_result["decision"],
                        "location_city": city,
                        "location_country": country,
                        "flag_reasons": eval_result["flag_reasons"],
                        "impossible_travel": eval_result.get("impossible_travel_flag", False),
                        "mule_cycle": eval_result.get("mule_cycle_detected", False)
                    }
                }

                await self.broadcast(payload)
                await asyncio.sleep(random.uniform(0.6, 1.2))

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[STREAM] Error: {e}")
                await asyncio.sleep(1.0)


def datetime_str():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")


stream_manager = StreamManager()

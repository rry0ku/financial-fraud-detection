"""
Behavioral Velocity & Impossible Travel Geo-Engine.
Tracks sliding-window transaction velocities per account and detects impossible geo-speed anomalies.
"""

import time
import math
from typing import Dict, Any, Tuple, Optional, List
from collections import defaultdict, deque
import threading


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance between two GPS coordinates using Haversine formula.
    """
    R = 6371.0  # Earth's radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class VelocityGeoEngine:
    """
    In-memory sliding-window velocity tracker and geo-velocity detector.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VelocityGeoEngine, cls).__new__(cls)
                cls._instance._init_storage()
            return cls._instance

    def _init_storage(self):
        # account_id -> deque of (timestamp, amount, lat, lon, city)
        self.history = defaultdict(deque)
        # account_id -> last_known_location: (timestamp, lat, lon, city)
        self.last_location: Dict[str, Tuple[float, float, float, str]] = {}

    def record_and_evaluate(
        self,
        account_id: str,
        amount: float,
        timestamp: Optional[float] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records the transaction and calculates rolling window velocity metrics and geo-velocity anomalies.
        """
        current_time = timestamp or time.time()
        
        with self._lock:
            events = self.history[account_id]
            
            # Prune events older than 1 hour (3600 seconds)
            cutoff_1h = current_time - 3600
            while events and events[0][0] < cutoff_1h:
                events.popleft()

            # Calculate 1m, 5m, 1h stats
            cutoff_1m = current_time - 60
            cutoff_5m = current_time - 300

            count_1m, sum_1m = 0, 0.0
            count_5m, sum_5m = 0, 0.0
            count_1h, sum_1h = 0, 0.0

            for t, amt, _, _, _ in events:
                count_1h += 1
                sum_1h += amt
                if t >= cutoff_5m:
                    count_5m += 1
                    sum_5m += amt
                if t >= cutoff_1m:
                    count_1m += 1
                    sum_1m += amt

            # Geo-Velocity / Impossible Travel Analysis
            geo_velocity_kmh = 0.0
            impossible_travel = False
            prev_location_str = "None"
            distance_km = 0.0

            if lat is not None and lon is not None:
                if account_id in self.last_location:
                    prev_t, prev_lat, prev_lon, prev_city = self.last_location[account_id]
                    time_diff_hours = (current_time - prev_t) / 3600.0
                    
                    if time_diff_hours > 0.0001:  # At least ~0.3 seconds elapsed
                        distance_km = haversine_distance_km(prev_lat, prev_lon, lat, lon)
                        geo_velocity_kmh = distance_km / time_diff_hours
                        prev_location_str = prev_city or f"({prev_lat:.2f}, {prev_lon:.2f})"
                        
                        # If speed exceeds commercial jet cruising speed (~900 km/h) over non-trivial distance (>50 km)
                        if geo_velocity_kmh > 900.0 and distance_km > 50.0:
                            impossible_travel = True

                # Update last known location
                self.last_location[account_id] = (current_time, lat, lon, city or "Unknown")

            # Append current event
            events.append((current_time, amount, lat or 0.0, lon or 0.0, city or "Unknown"))

            # Risk assessment based on velocity
            velocity_risk_boost = 0.0
            reasons = []

            if count_5m >= 4:
                velocity_risk_boost += 0.25
                reasons.append(f"High Velocity Surge: {count_5m} transactions in under 5 minutes")

            if sum_5m > 50000.0:
                velocity_risk_boost += 0.20
                reasons.append(f"Rapid Capital Outflow: ${sum_5m:,.2f} moved in 5 minutes")

            if impossible_travel:
                velocity_risk_boost += 0.45
                reasons.append(f"Impossible Travel Anomaly: {distance_km:,.1f} km traversed at {geo_velocity_kmh:,.0f} km/h from {prev_location_str}")

            return {
                "count_1m": count_1m + 1,
                "sum_1m": round(sum_1m + amount, 2),
                "count_5m": count_5m + 1,
                "sum_5m": round(sum_5m + amount, 2),
                "count_1h": count_1h + 1,
                "sum_1h": round(sum_1h + amount, 2),
                "geo_velocity_kmh": round(geo_velocity_kmh, 1),
                "distance_km": round(distance_km, 1),
                "impossible_travel": impossible_travel,
                "prev_location": prev_location_str,
                "velocity_risk_boost": round(velocity_risk_boost, 3),
                "velocity_reasons": reasons
            }


velocity_engine = VelocityGeoEngine()

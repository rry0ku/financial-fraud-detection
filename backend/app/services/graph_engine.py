"""
Graph Analytics & Money Mule Ring Detector.
Uses directed network graph algorithms to detect circular layering (wash trading)
and mule aggregator hub accounts.
"""

import threading
from typing import Dict, Any, List, Set, Tuple
import networkx as nx


class FraudGraphEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(FraudGraphEngine, cls).__new__(cls)
                cls._instance._init_graph()
            return cls._instance

    def _init_graph(self):
        self.G = nx.DiGraph()
        self.max_nodes = 200  # Keep active graph responsive and informative
        self.cycle_edges: Set[Tuple[str, str]] = set()
        self.mule_nodes: Set[str] = set()

    def sync_from_database(self, db_session):
        """
        Synchronizes existing transactions from the database into the in-memory directed graph.
        """
        from backend.app.models.transaction import TransactionRecord
        with self._lock:
            records = db_session.query(TransactionRecord).order_by(TransactionRecord.timestamp.asc()).limit(150).all()
            for r in records:
                self._add_edge_internal(
                    txn_id=r.transaction_id,
                    orig_id=r.name_orig,
                    dest_id=r.name_dest,
                    amount=r.amount,
                    risk_score=r.risk_score,
                    is_fraud=r.is_fraud_predicted
                )

    def _add_edge_internal(self, txn_id: str, orig_id: str, dest_id: str, amount: float, risk_score: float, is_fraud: bool):
        if not self.G.has_node(orig_id):
            self.G.add_node(orig_id, risk=risk_score, is_fraud=is_fraud, type="sender")
        else:
            self.G.nodes[orig_id]['risk'] = max(self.G.nodes[orig_id].get('risk', 0.0), risk_score)

        if not self.G.has_node(dest_id):
            self.G.add_node(dest_id, risk=risk_score, is_fraud=is_fraud, type="receiver")
        else:
            self.G.nodes[dest_id]['risk'] = max(self.G.nodes[dest_id].get('risk', 0.0), risk_score)

        self.G.add_edge(orig_id, dest_id, txn_id=txn_id, amount=amount, risk=risk_score)

        # Detect cycles
        try:
            for cycle in nx.simple_cycles(self.G):
                if len(cycle) >= 2 and len(cycle) <= 6:
                    for i in range(len(cycle)):
                        u = cycle[i]
                        v = cycle[(i + 1) % len(cycle)]
                        self.cycle_edges.add((u, v))
                        self.mule_nodes.add(u)
                        self.mule_nodes.add(v)
        except Exception:
            pass

        # Detect mule hubs
        in_deg = self.G.in_degree(dest_id)
        out_deg = self.G.out_degree(dest_id)
        if (in_deg >= 3 and out_deg >= 1) or (in_deg >= 2 and out_deg >= 2):
            self.mule_nodes.add(dest_id)

    def add_transaction(
        self,
        txn_id: str,
        orig_id: str,
        dest_id: str,
        amount: float,
        risk_score: float,
        is_fraud: bool
    ) -> Dict[str, Any]:
        """
        Inserts transaction edge into graph, analyzes graph metrics, and returns risk signals.
        """
        with self._lock:
            # Maintain active sliding graph window if node count exceeds limit
            if self.G.number_of_nodes() > self.max_nodes:
                nodes_by_degree = sorted(self.G.degree(), key=lambda x: x[1])
                for node, _ in nodes_by_degree[:20]:
                    if node not in [orig_id, dest_id] and node not in self.mule_nodes:
                        self.G.remove_node(node)

            self._add_edge_internal(txn_id, orig_id, dest_id, amount, risk_score, is_fraud)

            # Cycle Check specifically for this transaction
            cycle_detected = (orig_id, dest_id) in self.cycle_edges
            in_deg = self.G.in_degree(dest_id)
            out_deg = self.G.out_degree(dest_id)
            is_mule = dest_id in self.mule_nodes or orig_id in self.mule_nodes

            # Graph Risk Assessment
            graph_risk_boost = 0.0
            reasons = []

            if cycle_detected:
                graph_risk_boost += 0.40
                reasons.append("Money Mule Ring: Circular transaction layering loop detected")

            if is_mule:
                graph_risk_boost += 0.25
                reasons.append(f"Mule Aggregator Hub: High fan-in/fan-out connectivity (In: {in_deg}, Out: {out_deg})")

            return {
                "cycle_detected": cycle_detected,
                "is_mule_node": is_mule,
                "in_degree": in_deg,
                "out_degree": out_deg,
                "graph_risk_boost": round(graph_risk_boost, 3),
                "graph_reasons": reasons
            }

    def get_cytoscape_data(self) -> Dict[str, Any]:
        """
        Exports the current transaction graph into Cytoscape.js compatible elements.
        """
        with self._lock:
            nodes = []
            edges = []

            try:
                pagerank = nx.pagerank(self.G, alpha=0.85) if len(self.G) > 0 else {}
            except Exception:
                pagerank = {}

            for node, attrs in self.G.nodes(data=True):
                is_mule = node in self.mule_nodes
                node_risk = attrs.get('risk', 0.1)
                pr_score = pagerank.get(node, 0.05)
                
                nodes.append({
                    "data": {
                        "id": node,
                        "label": node,
                        "risk": round(node_risk, 3),
                        "is_mule": is_mule,
                        "is_fraud": attrs.get('is_fraud', False) or node_risk > 0.75,
                        "pagerank": round(pr_score * 100, 2),
                        "in_degree": self.G.in_degree(node),
                        "out_degree": self.G.out_degree(node)
                    }
                })

            for u, v, attrs in self.G.edges(data=True):
                is_cycle = (u, v) in self.cycle_edges
                edges.append({
                    "data": {
                        "id": f"{u}_{v}_{attrs.get('txn_id', '')}",
                        "source": u,
                        "target": v,
                        "amount": attrs.get('amount', 0.0),
                        "risk": attrs.get('risk', 0.0),
                        "is_cycle": is_cycle,
                        "txn_id": attrs.get('txn_id', 'N/A')
                    }
                })

            return {
                "nodes": nodes,
                "edges": edges,
                "summary": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "mule_hubs_count": len(self.mule_nodes),
                    "cycle_loops_count": len(self.cycle_edges)
                }
            }


graph_engine = FraudGraphEngine()

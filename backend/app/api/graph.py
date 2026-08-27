"""
Money Mule Network Graph Endpoints.
"""

from fastapi import APIRouter
from backend.app.services.graph_engine import graph_engine

router = APIRouter(prefix="/graph", tags=["Graph Network"])


@router.get("")
def get_fraud_graph():
    """
    Returns the dynamic Cytoscape.js network topology, mule hubs, and circular cycles.
    """
    return graph_engine.get_cytoscape_data()

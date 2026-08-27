"""
FastAPI Main Application Entry Point.
Provides RESTful APIs and serves the interactive Web Dashboard.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api import health, predict, transactions, analytics, graph, drift, hitl, sar, stream, rules, redteam, batch, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database & Graph Engine on Startup
    init_db()
    from backend.app.core.database import SessionLocal
    from backend.app.services.graph_engine import graph_engine
    db = SessionLocal()
    try:
        graph_engine.sync_from_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="AI-Based Financial Fraud Detection Platform",
    description="End-to-End Cybersecurity, Network Graph, XAI & Machine Learning Transaction Risk Scoring Engine",
    version="2.0.0",
    lifespan=lifespan
)

# Mount API Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(predict.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(graph.router, prefix=settings.API_V1_STR)
app.include_router(drift.router, prefix=settings.API_V1_STR)
app.include_router(hitl.router, prefix=settings.API_V1_STR)
app.include_router(sar.router, prefix=settings.API_V1_STR)
app.include_router(rules.router, prefix=settings.API_V1_STR)
app.include_router(redteam.router, prefix=settings.API_V1_STR)
app.include_router(batch.router, prefix=settings.API_V1_STR)
app.include_router(system.router, prefix=settings.API_V1_STR)
app.include_router(stream.router)

# Serve Frontend Static Assets
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend_root():
        return FileResponse(os.path.join(frontend_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

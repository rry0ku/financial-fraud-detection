"""
WebSocket Real-Time Live Streaming Endpoint.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.services.stream_service import stream_manager

router = APIRouter(tags=["Live Stream WebSocket"])


@router.websocket("/ws/live-stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    await stream_manager.connect(websocket)
    try:
        while True:
            # Keep connection open and accept optional client commands
            data = await websocket.receive_text()
            if data == "PING":
                await websocket.send_text("PONG")
    except WebSocketDisconnect:
        stream_manager.disconnect(websocket)
    except Exception:
        stream_manager.disconnect(websocket)

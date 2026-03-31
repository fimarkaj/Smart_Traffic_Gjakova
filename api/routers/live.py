"""
live.py — WebSocket endpoint. Streams live frames + stats to all connected clients.
"""
import asyncio
import base64
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/live", tags=["live"])


class ConnectionManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)
        logger.info(f"WS client connected. Total: {len(self._connections)}")

    def disconnect(self, ws: WebSocket):
        self._connections.remove(ws)
        logger.info(f"WS client disconnected. Total: {len(self._connections)}")

    async def broadcast(self, data: dict):
        dead = []
        for ws in self._connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            try:
                self._connections.remove(ws)
            except ValueError:
                pass


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # The detector writes to shared state; we just read and forward
            from main import shared_state
            frame = shared_state.get_latest()

            if frame is not None:
                payload = {
                    "type":             "frame",
                    "timestamp":        frame.timestamp,
                    "frame":            base64.b64encode(frame.jpeg_bytes).decode(),
                    "roi_counts":       frame.roi_counts,
                    "crossing_totals":  frame.crossing_totals,
                    "new_crossings":    frame.new_crossings,
                    "overall_crossings":  frame.overall_crossings,
                    "unique_crossers":    frame.unique_crossers,
                    "estimated_vehicles": frame.estimated_vehicles,
                    "global_unique":      frame.global_unique,
                    "total_cars":         frame.total_cars,
                    "camera_health":    frame.camera_health,
                }
                try:
                    await ws.send_json(payload)
                except WebSocketDisconnect:
                    break
            else:
                # No frame yet — send heartbeat
                try:
                    await ws.send_json({"type": "heartbeat"})
                except WebSocketDisconnect:
                    break

            await asyncio.sleep(0.1)   # ~10fps to frontend

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}")
    finally:
        manager.disconnect(ws)

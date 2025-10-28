"""WebSocket handlers for real-time updates."""

import asyncio
import json
from datetime import datetime
from typing import Set

from fastapi import APIRouter, WebSocketDisconnect, WebSocketException, status, websockets

from database import get_prodlens_store

router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active connections
active_connections: Set[websockets.WebSocket] = set()


@router.websocket("/ws/metrics")
async def websocket_metrics_endpoint(websocket: websockets.WebSocket):
    """WebSocket endpoint for real-time metrics updates.

    Clients can connect and receive periodic metric updates.
    """
    await websocket.accept()
    active_connections.add(websocket)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to metrics stream",
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Keep connection alive and send periodic updates
        while True:
            # Receive any client messages (for heartbeat/keep-alive)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data:
                    client_msg = json.loads(data)
                    if client_msg.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat(),
                        })
            except asyncio.TimeoutError:
                # No message received in 30 seconds, send metrics update
                pass

            # Send metrics update
            try:
                store = get_prodlens_store()
                from prodlens.metrics import ReportGenerator

                generator = ReportGenerator(store)
                from datetime import timedelta

                since_date = datetime.utcnow().date() - timedelta(days=7)
                report = generator.generate_report(
                    repo="",
                    since=since_date,
                )

                # Send metrics to client
                await websocket.send_json({
                    "type": "metrics_update",
                    "data": {
                        "ai_interaction_velocity": report.get("ai_interaction_velocity", 0),
                        "acceptance_rate": report.get("acceptance_rate", 0),
                        "error_rate": report.get("error_rate", 0),
                        "token_efficiency": report.get("token_efficiency", 0),
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                })

                store.close()

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error fetching metrics: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat(),
                })

            # Wait before next update
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        active_connections.discard(websocket)
    except Exception as e:
        active_connections.discard(websocket)
        raise WebSocketException(code=status.WS_1011_SERVER_ERROR, reason=str(e))


@router.websocket("/ws/sessions")
async def websocket_sessions_endpoint(websocket: websockets.WebSocket):
    """WebSocket endpoint for real-time session updates.

    Clients can connect and receive new session events.
    """
    await websocket.accept()
    active_connections.add(websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to sessions stream",
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Keep track of last check timestamp
        last_check = datetime.utcnow()

        while True:
            try:
                # Receive client messages (heartbeat)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data:
                    client_msg = json.loads(data)
                    if client_msg.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat(),
                        })
            except asyncio.TimeoutError:
                pass

            # Check for new sessions
            try:
                store = get_prodlens_store()
                df = store.sessions_dataframe()

                if not df.empty:
                    # Get sessions newer than last check
                    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                    new_sessions = df[df["timestamp"] > last_check]

                    if not new_sessions.empty:
                        # Send new sessions
                        for _, row in new_sessions.iterrows():
                            await websocket.send_json({
                                "type": "new_session",
                                "data": {
                                    "session_id": str(row.get("session_id", "")),
                                    "developer_id": row.get("developer_id"),
                                    "model": row.get("model"),
                                    "tokens": int(
                                        row.get("tokens_in", 0) + row.get("tokens_out", 0)
                                    ),
                                    "cost_usd": float(row.get("cost_usd", 0)),
                                    "accepted": bool(row.get("accepted_flag", False)),
                                },
                                "timestamp": datetime.utcnow().isoformat(),
                            })

                    last_check = datetime.utcnow()

                store.close()

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error fetching sessions: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat(),
                })

            await asyncio.sleep(10)

    except WebSocketDisconnect:
        active_connections.discard(websocket)
    except Exception as e:
        active_connections.discard(websocket)
        raise WebSocketException(code=status.WS_1011_SERVER_ERROR, reason=str(e))


async def broadcast_message(message: dict) -> None:
    """Broadcast a message to all connected WebSocket clients.

    Args:
        message: JSON-serializable message to broadcast
    """
    disconnected = set()

    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.add(connection)

    # Clean up disconnected clients
    for conn in disconnected:
        active_connections.discard(conn)


import pandas as pd

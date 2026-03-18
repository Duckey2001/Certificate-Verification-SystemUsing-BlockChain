"""Standalone script to exercise notification/event broadcasting.

This connects to the FastAPI app using TestClient websockets, then creates a dummy
AuditEvent and verifies that a message is received through the websocket.  It
also includes a simpler broadcast-to-manager check so you can run it against a
running server or offline.

Usage:
    python notification_test.py

"""

import asyncio
import os
import sys
from pprint import pprint

# Make sure the backend package is importable
sys.path.insert(0, os.getcwd())

from fastapi.testclient import TestClient
from backend.main import app
from backend.api import events
from database import SessionLocal


def run_ws_test():
    """Use TestClient to open a websocket and trigger a broadcast."""
    with TestClient(app) as client:
        with client.websocket_connect("/api/events/ws") as ws:
            print("WebSocket connected, creating audit event...")
            db = SessionLocal()
            # create an event which also schedules a broadcast
            event = events.create_audit_event(
                db,
                event_type="test_notification",
                payload={"text": "This is a test"},
            )
            print("Waiting for message from server...")
            msg = ws.receive_json(timeout=5)
            print("Received message from websocket:")
            pprint(msg)


def run_manager_test():
    """Directly broadcast via the NotificationManager (no server required)."""
    print("Broadcasting directly through NotificationManager...")
    async def coro():
        await events.manager.broadcast({"type": "manager_test", "hello": "world"})
    asyncio.run(coro())
    print("Manager broadcast completed (no recipients unless clients connected)")


def main():
    print("== Notification test script ==")
    run_ws_test()
    run_manager_test()


if __name__ == "__main__":
    main()

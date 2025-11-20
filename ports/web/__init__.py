"""
Input ports - API entry points (REST, WebSocket, etc.)
"""

from .fastapi_adapter import app

__all__ = ["app"]

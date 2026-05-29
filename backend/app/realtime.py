from typing import Any

import socketio
from fastapi import FastAPI

from backend.app.core.config import Settings


def create_socketio_server(settings: Settings) -> socketio.AsyncServer:
    sio = socketio.AsyncServer(
        async_mode="asgi",
        cors_allowed_origins=settings.cors_origins,
    )

    @sio.event
    async def connect(sid: str, environ: dict[str, Any], auth: Any) -> None:
        await sio.emit("socket:ready", {"sid": sid}, to=sid)

    @sio.event
    async def disconnect(sid: str) -> None:
        return None

    return sio


def attach_socketio(app: FastAPI, settings: Settings) -> socketio.AsyncServer:
    sio = create_socketio_server(settings)
    app.state.socketio = sio
    return sio


def create_asgi_app(app: FastAPI, settings: Settings) -> socketio.ASGIApp:
    sio = attach_socketio(app, settings)
    return socketio.ASGIApp(
        sio,
        other_asgi_app=app,
        socketio_path="dashboard.io",
    )

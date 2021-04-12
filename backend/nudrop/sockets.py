
import asyncio
from typing import Dict, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.tasks = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    def disconnect(self, websocket: WebSocket):
        for k,v in self.active_connections.items():
            if v == websocket:
                del self.active_connections[k]

    def register(self, sid: str, socket: WebSocket):
        self.active_connections[str(sid)] = socket

    def add_task(self, task):
        self.tasks.append(task) 

    async def clear_tasks(self):
        while True:
            await asyncio.sleep(1)
            # print("my tasks", self.tasks)
            for t in self.tasks:
                await self.send_personal_data(
                    t["task"],
                    t["ws"]
                )
            self.tasks = []

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_personal_data(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

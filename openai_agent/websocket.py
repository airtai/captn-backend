from typing import Any

from openai_agent.connection_manager import ConnectionManager


class CustomWebSocket:
    def __init__(self, manager: ConnectionManager, websocket: Any) -> None:
        self.manager = manager
        self.websocket = websocket

    async def send(self, message: str) -> None:
        await self.manager.send_personal_message(message, self.websocket)  # type: ignore

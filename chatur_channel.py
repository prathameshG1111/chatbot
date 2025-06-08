from typing import Text, Dict, Any, Optional, Callable, Awaitable
from rasa.core.channels.channel import InputChannel, OutputChannel, UserMessage
from starlette.websockets import WebSocket
from rasa.shared.utils.io import DEFAULT_ENCODING
import asyncio
import json

class CustomSocketOutput(OutputChannel):
    @classmethod
    def name(cls) -> Text:
        return "custom_websocket"

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def send_text_message(self, recipient_id: Text, text: Text, **kwargs: Any) -> None:
        await self.websocket.send_text(text)


class CustomSocketInput(InputChannel):
    @classmethod
    def name(cls) -> Text:
        return "custom_websocket"

    async def _extract_sender(self, websocket: WebSocket) -> Text:
        return "user"

    async def _extract_message(self, websocket: WebSocket) -> Optional[Text]:
        data = await websocket.receive_text()
        message = json.loads(data)
        return message.get("message")

    async def _handle_message(
        self,
        on_new_message: Callable[[UserMessage], Awaitable[Any]],
        websocket: WebSocket,
    ) -> None:
        sender_id = await self._extract_sender(websocket)
        text = await self._extract_message(websocket)
        if text:
            output_channel = CustomSocketOutput(websocket)
            user_message = UserMessage(text, output_channel, sender_id)
            await on_new_message(user_message)

    def blueprint(self, on_new_message: Callable[[UserMessage], Awaitable[Any]]):
        from fastapi import APIRouter, WebSocket

        router = APIRouter()

        @router.websocket("/websocket")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    await self._handle_message(on_new_message, websocket)
            except Exception:
                pass

        return router

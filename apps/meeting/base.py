"""
This module defines the
Base Consumer class.
This class acts as the parent of both
consumer classes in `consumers.py`
"""

import json
from typing import Any

from channels.generic.websocket import AsyncWebsocketConsumer


class BaseMeetingConsumer(AsyncWebsocketConsumer):
    """Base class for meeting consumers with shared functionality"""

    def __init__(self, *args: tuple[Any], **kwargs: dict[str, Any]):
        """
        Additional Params:
        group_name - The name of the group that the consumer belongs to.
        access_code - The access_code of the meeting.
        """
        super().__init__(*args, **kwargs)
        self.group_name: str = ""  # Filled manually in `consumers.py`
        self.access_code: str = ""  # Filled manually in `consumers.py`

    """
    Below are the instance methods 
    for THIS class
    """

    def _get_url_route(self) -> dict[str, Any] | None:
        """Get URL route from scope"""
        return self.scope.get("url_route")

    async def _close_with_log(self, message: str, code: int = 1000) -> None:
        """Close connection with logging"""
        print(message)
        await self.close(code=code)

    async def _send_json(self, data: dict[str, Any]) -> None:
        """
        Send JSON data to client
        `Automatically converts data to JSON format`
        """
        await self.send(text_data=json.dumps(data))

    async def disconnect(self, code: int) -> None:
        """Clean up on disconnect"""
        if hasattr(self, "group_name") and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

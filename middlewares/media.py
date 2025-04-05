import asyncio

from aiogram import BaseMiddleware, types
from typing import Union, Callable, Any, Awaitable


class MediaMiddleware(BaseMiddleware):
    """This middleware is for capturing media groups."""

    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        self.latency = latency

    async def __call__(
            self,
            handler: Callable[[types.Message, dict[str, Any]], Awaitable[Any]],
            message: types.Message,
            data: dict[str, Any]
    ) -> Any:

        if not message.media_group_id:

            if message.photo or message.video:
                data["album"] = [message]

            else:
                data["album"] = []

            await handler(message, data)
            return

        try:
            self.album_data[message.media_group_id].append(message)

        except KeyError:
            self.album_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)

            data['_is_last'] = True
            data["album"] = self.album_data[message.media_group_id]
            await handler(message, data)

        if message.media_group_id and data.get("_is_last"):
            del self.album_data[message.media_group_id]
            del data['_is_last']

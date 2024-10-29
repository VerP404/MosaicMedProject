from channels.generic.websocket import AsyncWebsocketConsumer
import json


class TelevisionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("television_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("television_group", self.channel_name)

    async def send_update(self, event):
        data = event['data']
        await self.send(text_data=json.dumps(data))

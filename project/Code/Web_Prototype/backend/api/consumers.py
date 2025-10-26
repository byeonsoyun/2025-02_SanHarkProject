import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # 연결 직후 간단 알림 메시지(옵션)
        await self.send(text_data=json.dumps({"message": "WebSocket 연결됨 (서버)" }))

    async def disconnect(self, close_code):
        # 연결 종료 시 처리(필요하면)
        pass

    async def receive(self, text_data):
        # 클라이언트가 보낸 JSON 받기 (예: {"message": "안녕"})
        data = json.loads(text_data)
        msg = data.get("message", "")
        # 받은 메시지를 다시 돌려줌 (echo)
        await self.send(text_data=json.dumps({"message": f"echo: {msg}"}))

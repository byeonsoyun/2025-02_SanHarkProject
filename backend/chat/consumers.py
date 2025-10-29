import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("WebSocket 연결 성공")
        await self.send(text_data=json.dumps({"message": "WebSocket 연결 성공!"}))

    async def receive(self, text_data):
        print("수신 데이터:", text_data)
        try:
            data = json.loads(text_data)
            msg = data.get("message", "")
        except Exception as e:
            print("JSON 처리 에러:", e)
            msg = "에러 발생"
        await self.send(text_data=json.dumps({"message": f"서버 응답: {msg}"}))

    async def disconnect(self, close_code):
        print("WebSocket 연결 종료:", close_code)

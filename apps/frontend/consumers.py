import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PollConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.poll_id = self.scope['url_route']['kwargs']['poll_id']
        self.group_name = 'poll_%s' % self.poll_id

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'message',
                'message': message
            }
        )

    # Receive message from group
    async def message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    # Receive new question from group
    async def new_question(self, event):
        question = event['question']
        answers = event['answers']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'question': question, 'answers': answers
        }))

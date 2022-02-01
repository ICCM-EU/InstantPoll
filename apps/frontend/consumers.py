import json
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.backend.logic import Logic
from asgiref.sync import sync_to_async

class PollConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.poll_id = self.scope['url_route']['kwargs']['poll_id']
        self.group_name = 'poll_%s' % self.poll_id

        # work with session
        if not 'voter_token' in self.scope["session"]:
            self.voter_token = self.create_voter_token(self.poll_id)
            self.scope["session"]['voter_token'] = self.voter_token
        else:
            self.voter_token =  self.scope["session"]['voter_token']
        print('voter token: %s' % (self.voter_token,))

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

    @sync_to_async
    def create_voter_token(self, poll_id):
        return Logic().create_voter_token(poll_id)

    @sync_to_async
    def do_refresh_question(self, poll_id):
        Logic().refresh_question(poll_id)

    @sync_to_async
    def do_refresh_result(self, poll_id):
        Logic().refresh_result(poll_id)

    @sync_to_async
    def do_process_answer(self, voter_token, poll_id, answer_id, message):
        Logic().process_answer(voter_token, poll_id, answer_id, message)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type = text_data_json['type']
        message = text_data_json['message']
        print('receive ' + type + ' - ' + message + ' for poll id ' + self.poll_id)

        if type == 'init_projector':
            await self.do_refresh_result(self.poll_id)

        if type == 'init':
            await self.do_refresh_question(self.poll_id)

        elif type == 'answer':
            await self.do_process_answer(self.voter_token, self.poll_id, text_data_json['answer_id'], message)

    # Send new question to group
    async def new_questions(self, event):
        questions = event['questions']
        answers = event['answers']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_questions',
            'questions': questions, 'answers': answers
        }))

    # Sending question again to group
    async def refresh_questions(self, event):
        questions = event['questions']
        answers = event['answers']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'refresh_questions',
            'questions': questions, 'answers': answers
        }))

    # Sending results to group
    async def update_results(self, event):
        questions = event['questions']
        answers = event['answers']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'update_results',
            'questions': questions, 'answers': answers
        }))

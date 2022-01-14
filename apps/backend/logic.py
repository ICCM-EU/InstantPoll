from django.db.models import Q
from apps.core.models import Event, Poll, Question, Answer, Voter, Vote
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Logic:
    def get_current_question(self, poll_id):
        poll = Poll.objects.get(id=poll_id)
        question = Question.objects.filter(poll=poll, display_question=True).first()
        return question

    def refresh_question(self, poll_id):
        question = self.get_current_question(poll_id)
        self.send_question('refresh_question', question)

    def refresh_result(self, poll_id):
        question = self.get_current_question(poll_id)
        self.send_question('update_results', question)

    def send_question(self, msgtype, question):
        answers = Answer.objects.filter(Q(question=question))
        answer_list = []
        for answer in answers:
            votes = Vote.objects.filter(question=question, answer=answer)
            # TODO freetext in votes
            answer_list.append({'answer': answer.answer, 'id': answer.id, 'votes': votes.count()})

        group_name = 'poll_%s' % question.poll.id
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {'type': msgtype, 'question': question.question, 'answers': answer_list}
        )

    def get_voter(self, event, voter_token):
        voter = Voter.objects.filter(token = voter_token, event = event)
        if voter.count() == 1:
            return voter.first()
        voter = Voter(token = voter_token)
        voter.event = event
        voter.save()
        return voter

    def process_answer(self, voter_token, poll_id, answer_id, message):
        poll = Poll.objects.get(id=poll_id)
        question = self.get_current_question(poll_id)
        answer = Answer.objects.filter(id=answer_id).first()
        if question != answer.question:
            return
        voter = self.get_voter(poll.event, voter_token)
        self.apply_vote(voter, question, answer, message)
        self.send_question('update_results', question)

    def apply_vote(self, voter, question, answer, message):
        vote = Vote.objects.filter(voter = voter, question=question)
        if vote.count() == 0:
            vote = Vote(question = question, voter = voter)
        else:
            vote = vote.first()
        vote.answer = answer
        if answer.free_text and message is not None:
            vote.message = message
        vote.save()

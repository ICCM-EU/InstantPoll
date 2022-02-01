import uuid
from django.db.models import Q
from apps.core.models import Event, Poll, Question, Answer, Voter, Vote
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Logic:

    # this will raise an exception if the event id does not belong to the user in the request
    def get_our_event(self, request, id):
        event = Event.objects.get(id=id)
        if event.user != request.user:
            raise Exception('invalid access to event of other user')
        return event

    def get_selected_event(self, request):
        if 'event_id' in request.session:
            event = Logic().get_our_event(request, request.session['event_id'])
            return event
        return None

    def get_selected_poll(self, request):
        if 'poll_id' in request.session and request.session['poll_id'] is not None:
            poll = Poll.objects.get(id=request.session['poll_id'])
            event = Logic().get_our_event(request, poll.event.id)
            return poll
        return None

    def create_voter_token(self, poll_id):
        poll = Poll.objects.get(id=poll_id)
        return ("%s_%s" % (poll.event.slug, uuid.uuid4()))

    def get_current_questions(self, poll):
        question = Question.objects.filter(poll=poll, display_question=True).all()
        return question

    def refresh_question(self, poll_id):
        poll = Poll.objects.get(id=poll_id)
        questions = self.get_current_questions(poll_id)
        self.send_questions(poll_id, 'refresh_questions', questions)

    def refresh_result(self, poll_id):
        poll = Poll.objects.get(id=poll_id)
        questions = self.get_current_questions(poll)
        self.send_questions(poll_id, 'update_results', questions)

    def send_questions(self, poll_id, msgtype, questions):
        if questions is None:
            group_name = 'poll_%s' % poll_id
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {'type': msgtype, 'message': 'Please wait', 'question': {}, 'answers': {}})
            return

        poll = Poll.objects.get(id=poll_id)

        answer_list = []
        question_list = []
        for question in questions:
            answers = Answer.objects.filter(Q(question=question)).order_by('id')
            for answer in answers:
                if poll.resultsmode == 'IM': # immediate
                    votes = Vote.objects.filter(question=question, answer=answer)
                    votecount = votes.count()
                elif poll.resultsmode == 'PR': # private
                    votecount = -1
                answer_list.append({'question_id': question.id, 'answer': answer.answer, 'id': answer.id, 'free_text': answer.free_text, 'votes': votecount})
            question_list.append({'id': question.id, 'description': question.question})

        # TODO: show number of voters, independent of vote
        group_name = 'poll_%s' % question.poll.id
        channel_layer = get_channel_layer()
        # TODO: support multiple questions at once
        async_to_sync(channel_layer.group_send)(
            group_name,
            {'type': msgtype, 'questions': question_list, 'answers': answer_list}
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
        questions = self.get_current_questions(poll)
        answer = Answer.objects.filter(id=answer_id).first()
        if answer.question not in questions:
            return
        voter = self.get_voter(poll.event, voter_token)
        self.apply_vote(voter, answer.question, answer, message)
        self.send_questions(poll_id, 'update_results', questions)

    def get_selected_answers(self, voter, questions):
        result = []
        for question in questions:
            votes  = Vote.objects.filter(question = question, voter = voter).all()
            for vote in votes:
                result.append({'id': vote.answer_id, 'free_text': vote.free_text})
        return result

    def apply_vote(self, voter, question, answer, message):
        vote = Vote.objects.filter(voter = voter, question=question)
        if vote.count() == 0:
            vote = Vote(question = question, voter = voter)
        elif answer.free_text:
            vote = vote.first()
        elif question.allow_multiple_answers:
            # do we have such an answer already? then revoke it
            vote = Vote.objects.filter(question = question, voter = voter, answer = answer)
            if vote.count() > 0:
                vote.first().delete()
                return
            else:
                vote = Vote(question = question, voter = voter)
        else:
            vote = vote.first()
            # do we have such an answer already? then revoke it
            if vote.answer == answer:
                vote.delete()
                return

        vote.answer = answer
        if answer.free_text and message is not None:
            vote.free_text = message
        vote.save()

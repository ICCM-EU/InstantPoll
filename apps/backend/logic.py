from django.db.models import Q
from apps.core.models import Answer, Event, Poll, Question, Answer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Logic:
    def get_current_question(self, poll_id):
        poll = Poll.objects.get(id=poll_id)
        question = Question.objects.filter(poll=poll).filter(display_question=True).first()
        return question

    def send_question(self, msgtype, question):
        answers = Answer.objects.filter(Q(question=question))
        answer_list = []
        for answer in answers:
            answer_list.append(answer.answer)

        group_name = 'poll_%s' % question.poll.id
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {'type': msgtype, 'question': question.question, 'answers': answer_list}
        )

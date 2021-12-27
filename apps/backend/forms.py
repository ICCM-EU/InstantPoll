from django import forms
import datetime
from apps.core.models import Event, Poll, Question, Answer


class EventForm(forms.ModelForm):
    # we are changing the password to UNCHANGED, so it is safe
    password = forms.CharField(widget=forms.PasswordInput(render_value=True))
    class Meta:
        model = Event
        fields = "__all__"


class PollForm(forms.ModelForm):

    class Meta:
        model = Poll
        fields = ("name", "slug", "active",)


class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question
        fields = ("question",)

class AnswerForm(forms.ModelForm):

    class Meta:
        model = Answer
        fields = ("answer",)
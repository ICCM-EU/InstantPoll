from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import hashers
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db import transaction
from django.db.models import Q
from apps.backend.forms import EventForm, PollForm, QuestionForm, AnswerForm
from apps.backend.logic import Logic
from apps.core.models import Answer, Event, Poll, Question, Answer

@login_required
@staff_member_required
def events(request):
    events = Event.objects.filter()
    return render(request,"events.html", {'events':events})

@login_required
@staff_member_required
def event_add(request):
    if request.method == "POST":

        values = request.POST.copy()
        if values['password']:
            values['password'] = hashers.make_password(values['password'])

        form = EventForm(values)

        if form.is_valid():
            try:
                form.save()
                return redirect('/events')
            except:
                raise

    else:
        form = EventForm()

    return render(request,'event.html',{'form':form})


@login_required
@staff_member_required
def event_edit(request, id):
    if request.method == "POST":
        event = Event.objects.get(id=id)

        values = request.POST.copy()
        if values['password']:
            if values['password'] == 'UNCHANGED':
                values['password'] = event.password
            else:
                values['password'] = hashers.make_password(values['password'])

        form = EventForm(values, instance = event)
        if form.is_valid():
            form.save()
            return redirect("/events")
        return render(request, 'event.html', {'form': form})

    else:
        event = Event.objects.get(id=id)
        event.password = 'UNCHANGED'
        form = EventForm(None, instance = event)
        return render(request,'event.html', {'form': form})


@login_required
@staff_member_required
def event_select(request, id):
    # TODO make sure we only select an event that belongs to us???
    request.session['event_id'] = id
    request.session['poll_id'] = None
    return redirect("/polls")


def get_selected_event(request):
    if 'event_id' in request.session:
        event = Event.objects.get(id=request.session['event_id'])
        return event
    return None


@login_required
@staff_member_required
def polls(request):

    event = get_selected_event(request)
    polls = Poll.objects.filter(event = event)
    return render(request,"polls.html", {'polls':polls, 'event': event})


@login_required
@staff_member_required
def poll_add(request):

    event = get_selected_event(request)
    if not event:
        return redirect('/polls')

    if request.method == "POST":

        form = PollForm(request.POST)

        if form.is_valid():
            try:
                # enforce the selected event
                form.instance.event = event
                form.save()
                return redirect('/polls')
            except:
                raise

    else:
        form = PollForm()

    return render(request,'poll.html',{'form':form})


@login_required
@staff_member_required
def poll_edit(request, id):
    if request.method == "POST":
        poll = Poll.objects.get(id=id)

        form = PollForm(request.POST, instance = poll)
        if form.is_valid():
            form.save()
            return redirect("/polls")
        return render(request, 'poll.html', {'form': form})

    else:
        poll = Poll.objects.get(id=id)
        form = PollForm(None, instance = poll)
        return render(request,'poll.html', {'form': form})


@login_required
@staff_member_required
def poll_select(request, id):
    request.session['poll_id'] = id
    return redirect("/questions")


def get_selected_poll(request):
    if 'poll_id' in request.session and request.session['poll_id'] is not None:
        poll = Poll.objects.get(id=request.session['poll_id'])
        return poll
    return None


@login_required
@staff_member_required
def questions(request):
    poll = get_selected_poll(request)
    questions = Question.objects.filter(poll = poll)
    for question in questions:
        question.answers = Answer.objects.filter(question=question)
    return render(request,"questions.html", {'questions':questions, 'poll': poll})


@login_required
@staff_member_required
def question_add(request):
    if request.method == "POST":

        form = QuestionForm(request.POST)

        if form.is_valid():
            try:
                form.instance.poll = get_selected_poll(request)
                form.save()
                return redirect('/questions')
            except:
                raise

    else:
        form = QuestionForm()

    return render(request,'question.html',{'form':form})


@login_required
@staff_member_required
def question_edit(request, id):
    if request.method == "POST":
        question = Question.objects.get(id=id)

        form = QuestionForm(request.POST, instance = question)
        if form.is_valid():
            form.save()
            return redirect("/questions")
        return render(request, 'question.html', {'form': form})

    else:
        question = Question.objects.get(id=id)
        form = QuestionForm(None, instance = question)
        return render(request,'question.html', {'form': form})


@login_required
@staff_member_required
@transaction.atomic
def question_activate(request, id):
    question = Question.objects.get(id=id)

    # deactivate all other questions of this poll
    otherquestions = Question.objects.filter(Q(poll=question.poll) & ~Q(id = question.id) & Q(display_question=True))
    if otherquestions.count() > 0:
        for otherquestion in otherquestions.all():
            otherquestion.display_question = False
            otherquestion.voting_active = False
            otherquestion.display_result = False
            otherquestion.save()

    # activate this question
    question.display_question = True
    question.voting_active = True
    question.display_result = True
    question.save()

    Logic().send_question('new_question', question)
    return redirect("/questions")


@login_required
@staff_member_required
def answer_add(request, question_id):
    # TODO check: is this a question in my event???

    if request.method == "POST":

        form = AnswerForm(request.POST)

        if form.is_valid():
            try:
                form.instance.question = Question.objects.get(id=question_id)
                form.save()
                return redirect('/questions')
            except:
                raise

    else:
        form = AnswerForm()

    return render(request,'answer.html',{'form':form, 'question_id': question_id})

@login_required
@staff_member_required
def answer_edit(request, id):
    if request.method == "POST":
        answer = Answer.objects.get(id=id)

        form = AnswerForm(request.POST, instance = answer)
        if form.is_valid():
            form.save()
            return redirect("/questions")
        return render(request, 'answer.html', {'form': form})

    else:
        answer = Answer.objects.get(id=id)
        form = AnswerForm(None, instance = answer)
        return render(request,'answer.html', {'form': form})

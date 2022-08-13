import uuid
from django.shortcuts import render, redirect
from django.contrib.auth import hashers
from django.http import JsonResponse
from apps.core.models import Event, Poll, Question, Answer
from apps.backend.logic import Logic


def home(request):

    if request.user.is_authenticated:
        return redirect('/events')

    entered = False
    if 'entered_event' in request.session:
        entered = request.session['entered_event']
    if entered:
        event_id  = request.session['event_id']
        return enter_event(request, event_id)
    else:
        events = Event.objects
        if events.count() == 1:
            return enter_event(request, events.first().slug)
    return enter_event(request, None)


def enter_event(request, event_slug):

    event = None
    if event_slug:
        event = Event.objects.filter(slug=event_slug).first()
    if not event:
        return render(request, "enter.html", {'message':'Please specify event'})

    entered = False

    if request.method == "POST":
        # check if the password is right
        if hashers.check_password(request.POST['password'], event.password):
            request.session['event_id'] = event.id
            request.session['entered_event'] = True
            if not 'voter_token' in request.session:
                request.session['voter_token'] = "%s_%s" % (event.slug, uuid.uuid4())
            elif not request.session['voter_token'].startswith(event.slug):
                    request.session['voter_token'] = "%s_%s" % (event.slug, uuid.uuid4())

    if 'entered_event' in request.session:
        entered = request.session['entered_event']
        event_id  = request.session['event_id']
        if event_id != event.id:
            raise Exception('invalid event')

    if entered:
        # if there is only one active poll, then select that
        polls = Poll.objects.filter(event = event, active=True)
        if polls.count() == 1:
            return show_poll(request, polls.first())
        else:
            return show_polls(request, event, polls)
    else:
        return render(request,"enter.html", {'event': event})

def show_poll_by_slug(request, event_slug, poll_slug):
    if event_slug:
        event = Event.objects.filter(slug=event_slug).first()
    if not event:
        return render(request, "enter.html", {'message':'Please specify event'})

    entered = False
    if 'entered_event' in request.session:
        entered = request.session['entered_event']
        event_id  = request.session['event_id']
        if event_id != event.id:
            raise Exception('invalid event')

    if entered:
        polls = Poll.objects.filter(event = event, slug = poll_slug, active=True)
        if polls.count() == 1:
            return show_poll(request, polls.first())
        else:
            return show_polls(request, event, polls)
    else:
        return render(request,"enter.html", {'event': event})

def show_poll(request, poll):
    # get the current question
    questions = Question.objects.filter(poll = poll).filter(display_question = True)
    question = questions.first()
    answers = Answer.objects.filter(question=question).order_by('order').all()
    voter_token =  request.session['voter_token']
    selected_answers = Logic().get_selected_answers(Logic().get_voter(poll.event, voter_token), questions)

    selected_answers_ids = ''
    for selected_answer in selected_answers:
        selected_answers_ids += str(selected_answer['id']) + ','

    return render(request,"frontend/poll.html", {'poll': poll, 'question': question, 'answers': answers, 'selected_answers_ids': selected_answers_ids})

def show_polls(request, event, polls):
    return render(request,"frontend/polls.html", {'event': event, 'polls': polls})

def selected_answers(request, poll_id):
    voter_token =  request.session['voter_token']
    poll = Poll.objects.get(id=poll_id)
    # get the current question(s)
    questions = Question.objects.filter(poll = poll).filter(display_question = True).all()
    answers = Logic().get_selected_answers(Logic().get_voter(poll.event, voter_token), questions)
    return JsonResponse({'selected_answers':answers})
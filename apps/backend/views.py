from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import hashers
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
import xlwt
from apps.backend.forms import EventForm, PollForm, QuestionForm, AnswerForm
from apps.backend.logic import Logic
from apps.core.models import Answer, Event, Poll, Question, Answer, Vote

@login_required
def events(request):
    events = Event.objects.filter(user=request.user)
    return render(request,"events.html", {'events':events})

@login_required
def event_add(request):
    if request.method == "POST":

        values = request.POST.copy()
        if values['password']:
            values['password'] = hashers.make_password(values['password'])

        form = EventForm(values)

        if form.is_valid():
            try:
                form.instance.user = request.user
                form.save()
                return redirect('/events')
            except:
                raise

    else:
        form = EventForm()

    return render(request,'event.html',{'form':form})


@login_required
def event_edit(request, id):
    event = Logic().get_our_event(request, id)

    if request.method == "POST":
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
        event.password = 'UNCHANGED'
        form = EventForm(None, instance = event)
        return render(request,'event.html', {'form': form})


@login_required
def event_select(request, id):
    event = Logic().get_our_event(request, id)
    request.session['event_id'] = event.id
    request.session['poll_id'] = None
    return redirect("/polls")


@login_required
def polls(request):
    event = Logic().get_selected_event(request)
    polls = Poll.objects.filter(event = event).order_by('-id')
    return render(request,"polls.html", {'polls':polls, 'event': event})


@login_required
def poll_add(request):

    event = Logic().get_selected_event(request)
    if not event:
        return redirect('/polls')

    if request.method == "POST":

        form = PollForm(request.POST)

        if form.is_valid():
            try:
                # enforce the selected event
                form.instance.event = event
                form.save()
                request.session['poll_id'] = form.instance.id
                return redirect('/questions')
            except:
                raise

    else:
        form = PollForm()

    return render(request,'poll.html',{'form':form})


@login_required
def poll_edit(request, id):
    if request.method == "POST":
        poll = Poll.objects.get(id=id)
        event = Logic().get_our_event(request, poll.event.id)

        form = PollForm(request.POST, instance = poll)
        if form.is_valid():
            form.save()
            return redirect("/questions")
        return render(request, 'poll.html', {'form': form})

    else:
        poll = Poll.objects.get(id=id)
        form = PollForm(None, instance = poll)
        return render(request,'poll.html', {'form': form})


@login_required
def poll_clone(request, id):
    poll = Poll.objects.get(id=id)
    event = Logic().get_our_event(request, poll.event.id)

    newpoll = Poll.objects.get(id=id)
    newpoll.id = None
    newpoll.name = poll.name + ' (clone)'
    newpoll.slug = poll.slug + '_clone'
    newpoll.active = False
    newpoll.save()

    questions = Question.objects.filter(poll = poll).order_by('id')

    for question in questions:
        newqust = Question.objects.get(id=question.id)
        newqust.id = None
        newqust.poll = newpoll
        newqust.save()

        answers = Answer.objects.filter(question=question).order_by('id')
        for answer in answers:
            newansw = Answer.objects.get(id=answer.id)
            newansw.id = None
            newansw.question = newqust
            newansw.save()

    request.session['poll_id'] = newpoll.id
    return redirect("/polls/edit/" + str(newpoll.id))


@login_required
def poll_delete(request, id):
    poll = Poll.objects.get(id=id)
    event = Logic().get_our_event(request, poll.event.id)
    poll.delete()
    return redirect("/polls")


@login_required
def poll_select(request, id):
    poll = Poll.objects.get(id=id)
    event = Logic().get_our_event(request, poll.event.id)
    request.session['poll_id'] = poll.id
    return redirect("/questions")


@login_required
def questions(request):
    poll = Logic().get_selected_poll(request)
    questions = Question.objects.filter(poll = poll).order_by('id')
    for question in questions:
        question.answers = Answer.objects.filter(question=question).order_by('id')
    return render(request,"questions.html", {'questions':questions, 'poll': poll, 'title': poll.name})


@login_required
def question_add(request):
    if request.method == "POST":

        form = QuestionForm(request.POST)

        if form.is_valid():
            try:
                form.instance.poll = Logic().get_selected_poll(request)
                # in survey mode: by default enable all questions
                if form.instance.poll.pollmode == 'SU':
                    form.instance.display_question = True
                form.save()
                return redirect('/questions')
            except:
                raise

    else:
        form = QuestionForm()

    return render(request,'question.html',{'form':form})


@login_required
def question_edit(request, id):
    question = Question.objects.get(id=id)
    event = Logic().get_our_event(request, question.poll.event.id)

    if request.method == "POST":
        form = QuestionForm(request.POST, instance = question)
        if form.is_valid():
            form.save()
            return redirect("/questions")
        return render(request, 'question.html', {'form': form})

    else:
        form = QuestionForm(None, instance = question)
        return render(request,'question.html', {'form': form})


@login_required
def question_delete(request, id):
    question = Question.objects.get(id=id)
    event = Logic().get_our_event(request, question.poll.event.id)
    question.delete()
    return redirect("/questions")


@login_required
@transaction.atomic
def question_activate(request, id):

    question = Question.objects.get(id=id)
    event = Logic().get_our_event(request, question.poll.event.id)

    # poll.pollmode = PO: only one question active at the same time
    if question.poll.pollmode == 'PO':
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

    questions = Question.objects.filter(poll=question.poll, display_question=True)

    Logic().send_questions(question.poll.id, 'new_questions', questions)
    return redirect("/questions")


@login_required
def answer_add(request, question_id):
    question = Question.objects.get(id=question_id)
    event = Logic().get_our_event(request, question.poll.event.id)

    if request.method == "POST":

        form = AnswerForm(request.POST)

        if form.is_valid():
            try:
                form.instance.question = question
                form.save()
                return redirect('/questions')
            except:
                raise

    else:
        form = AnswerForm()

    return render(request,'answer.html',{'form':form, 'question_id': question_id})

@login_required
def answer_edit(request, id):
    answer = Answer.objects.get(id=id)
    event = Logic().get_our_event(request, answer.question.poll.event.id)
    if request.method == "POST":

        form = AnswerForm(request.POST, instance = answer)
        if form.is_valid():
            form.save()
            return redirect("/questions")
        return render(request, 'answer.html', {'form': form})

    else:
        form = AnswerForm(None, instance = answer)
        return render(request,'answer.html', {'form': form})


@login_required
def answer_delete(request, id):
    answer = Answer.objects.get(id=id)
    event = Logic().get_our_event(request, answer.question.poll.event.id)
    answer.delete()
    return redirect("/questions")


@login_required
def view_result(request, id):

    poll = Poll.objects.get(id=id)
    event = Logic().get_our_event(request, poll.event.id)

    # display result of current poll
    return render(request,'projector.html', 
        {'poll': poll,
        'title': ' Projector - ' + poll.name,
        'fullscreen': True})


@login_required
def view_question_result(request, id):

    question = Question.objects.get(id=id)
    event = Logic().get_our_event(request, question.poll.event.id)
    answers = Answer.objects.filter(Q(question=question))
    answer_list = []
    total_votes = 0
    for answer in answers:
        votes = Vote.objects.filter(question=question, answer=answer)
        # TODO freetext in votes
        answer_list.append({'answer': answer.answer, 'id': answer.id, 'votes': votes.count()})
        total_votes += votes.count()

    # display result of selected question
    return render(request,'result.html',
        {'question': question,
        'answers': answer_list,
        'total_votes': total_votes,
        'title': question.question,
        'fullscreen': True})

def export_poll(wb, poll):
    questions = Question.objects.filter(poll = poll).order_by('id')

    # export result of this poll
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="poll_'+poll.slug+'.xlsx"'

    ws = wb.add_sheet('results for poll ' + poll.slug)

    # header
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    ws.write(row_num, 0, poll.name, font_style)
    row_num += 2

    columns = ['Question', 'Answer', 'Count']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    row_num += 1

    # body
    font_style = xlwt.XFStyle()

    for question in questions:
        row_num += 1
        ws.write(row_num, 0, question.question, font_style)
        row_num += 1
        answers = Answer.objects.filter(Q(question=question)).order_by('id')
        total_votes = 0
        for answer in answers:
            votes = Vote.objects.filter(question=question, answer=answer)
            if not answer.free_text:
                total_votes += votes.count()
                ws.write(row_num, 1, answer.answer, font_style)
                ws.write(row_num, 2, votes.count(), font_style)
                row_num += 1
            else:
                for vote in votes.all():
                    if vote.free_text:
                        total_votes += 1
                        ws.write(row_num, 1, vote.free_text, font_style)
                        row_num += 1
                row_num += 1
        ws.write(row_num, 0, 'Total votes', font_style)
        ws.write(row_num, 1, total_votes, font_style)
        row_num += 2


# export result of current poll
@login_required
def poll_export_result(request, id):

    poll = Poll.objects.get(id=id)
    event = Logic().get_our_event(request, poll.event.id)

    wb = xlwt.Workbook(encoding='utf-8')
    export_poll(wb, poll)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="poll_'+poll.slug+'.xlsx"'
    wb.save(response)
    return response

# export results of all poll in this event
@login_required
def event_export_result(request, id):

    event = Logic().get_our_event(request, id)

    polls = Poll.objects.filter(event = event).order_by('-id')
    wb = xlwt.Workbook(encoding='utf-8')

    for poll in polls:
        export_poll(wb, poll)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="poll_'+event.slug+'.xlsx"'
    wb.save(response)
    return response

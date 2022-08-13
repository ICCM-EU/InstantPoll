from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

class Event(models.Model):

    class Meta:
        db_table = "core_event"

    user = models.ForeignKey(
        User,
        null=False, blank=False, default=None,
        on_delete=models.CASCADE,
    )
    name = models.CharField(_("name"), max_length=250)
    slug = models.CharField(_("slug"), max_length=50)
    password = models.CharField(_("password"), max_length=250)


class Poll(models.Model):

    class Meta:
        db_table = "core_poll"

    event = models.ForeignKey(
        Event,
        null=False, blank=False, default=None,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_list",
    )

    name = models.CharField(_("name"), max_length=250)
    slug = models.CharField(_("slug"), max_length=50)
    active = models.BooleanField(_("active"), default=False)

    class PollMode(models.TextChoices):
        SURVEY = 'SU', _('Survey: show all questions at once')
        POLL = 'PO', _('Poll: only show one active question')

    pollmode = models.CharField(
        max_length=2,
        choices=PollMode.choices,
        default=PollMode.POLL,
    )

    class ResultsMode(models.TextChoices):
        IMMEDIATE = 'IM', _('Immediately during voting')
        AFTER = 'AF', _('After voting is done')
        PRIVATE = 'PR', _('Private: do not show votes to voters')

    resultsmode = models.CharField(
        max_length=2,
        choices=ResultsMode.choices,
        default=ResultsMode.IMMEDIATE,
    )

class Question(models.Model):

    class Meta:
        db_table = "core_question"

    poll = models.ForeignKey(
        Poll,
        null=False, blank=False, default=None,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_list",
    )

    question = models.CharField(_("question"), max_length=250)
    display_question = models.BooleanField(_("display question"), default=False)
    voting_active = models.BooleanField(_("voting active"), default=False)
    display_result = models.BooleanField(_("display result"), default=False)
    # display the result as wordmap, as bar chart, as pie chart, etc...
    result_presentation_type = models.CharField(_("present as"), default='bar_chart', max_length=50)
    # allow multiple answers
    allow_multiple_answers = models.BooleanField(_("multiple answers allowed"), default=False)


class Answer(models.Model):

    class Meta:
        db_table = "core_answer"
        ordering = ('order',)

    order = models.IntegerField(_("Order"), default = 0)

    question = models.ForeignKey(
        Question,
        null=False, blank=False, default=None,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_list",
    )

    answer = models.CharField(_("Answer"), max_length=2500)
    free_text = models.BooleanField(_("free text"), default=False)

    def save(self, *args, **kwargs):
        # move this answer to the end
        if self.pk is None:
            last_answer = Answer.objects.filter(Q(question = self.question), ~Q(id = self.id)).order_by('order').last()
            if last_answer:
                self.order = last_answer.order + 1

        super(Answer, self).save(*args, **kwargs)


    def move(self, up_or_down):
        other_answers = Answer.objects.filter(Q(question = self.question), ~Q(id = self.id))
        need_to_move = False

        # are there answers at the same order or ahead in that direction?
        for answer in other_answers:
            if up_or_down == 1: # move down the list
                if answer.order >= self.order:
                    need_to_move = True
            elif up_or_down == -1: # move up the list
                if answer.order <= self.order:
                    need_to_move = True
        if not need_to_move:
            return False
        # need to jump deleted items
        while True:
            for answer in other_answers:
                if answer.order == self.order:
                    break
            self.order += up_or_down
        self.order += up_or_down
        self.save()
        for answer in other_answers:
            if up_or_down == 1: # move down the list
                if answer.order >= self.order:
                    answer.order -= 1
            elif up_or_down == -1: # move up the list
                if answer.order <= self.order:
                    answer.order += 1
            answer.save()
        return True


class Voter(models.Model):
    class Meta:
        db_table = "core_voter"

    identification = models.CharField(_("identification"), max_length=250)
    token = models.CharField(_("token"), max_length=250)

    event = models.ForeignKey(
        Event,
        null=False, blank=False, default=None,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_list",
    )


class Vote(models.Model):

    class Meta:
        db_table = "core_vote"

    question = models.ForeignKey(
        Question,
        null=False, blank=False, default=None,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_list",
    )

    answer = models.ForeignKey(
        Answer,
        null=False, blank=False, default=None,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_list",
    )

    voter = models.ForeignKey(
        Voter,
        null=False, blank=False, default=None,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_list",
    )

    free_text = models.CharField(_("free text"), max_length=250, null=True)
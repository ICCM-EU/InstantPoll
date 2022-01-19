from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import User
from django.db import models
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

    question = models.ForeignKey(
        Question,
        null=False, blank=False, default=None,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_list",
    )

    answer = models.CharField(_("Answer"), max_length=250)
    free_text = models.BooleanField(_("free text"), default=False)


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
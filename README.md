About
=====

InstantPoll is an application written in Python using the Django framework.

Its purpose is to allow voting during a conference on distinct questions that come up during a presentation.
There is also a survey mode where the voters can answer multiple questions on one page.

Development environment
=======================

This works on Fedora 35:

Initialise development installation, with sqlite database:

    make quickstart

Start Redis container with podman on port 6379:

    make start_redis

Start the server:

    make runserver

Visit the website on http://localhost:8000

User is `admin`, with password `admin`.

Production environment
======================

For an Ansible script for setting up a production environment, have a look at https://github.com/tpokorra/Hostsharing-Ansible-InstantPoll/

Usage
=====

The admin user can create events, polls, questions and answers.

Normal users don't register, but use the password for the event that they visit, and they can vote on active polls.

A poll can either be in poll mode, with only one active question, or in survey mode, with multiple questions on one page that can be answered at the same time.

Results can either be displayed to the audience while voting, or after the vote has been closed, or not at all.
"""instantquestion URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from apps.backend import views as backend_views
from apps.frontend import views as frontend_views

urlpatterns = [
    # Django urls
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('django_registration.backends.activation.urls')),

    # Backend
    path('backend/', backend_views.events),
    path('events', backend_views.events),
    path('events/add', backend_views.event_add),
    path('events/select/<int:id>', backend_views.event_select),
    path('events/edit/<int:id>', backend_views.event_edit),
    path('events/export/<int:id>', backend_views.event_export_result),
    path('polls', backend_views.polls),
    path('polls/add', backend_views.poll_add),
    path('polls/select/<int:id>', backend_views.poll_select),
    path('polls/edit/<int:id>', backend_views.poll_edit),
    path('polls/clone/<int:id>', backend_views.poll_clone),
    path('polls/delete/<int:id>', backend_views.poll_delete),
    path('polls/view/<int:id>', backend_views.view_result),
    path('polls/export/<int:id>', backend_views.poll_export_result),
    path('questions', backend_views.questions),
    path('questions/add', backend_views.question_add),
    path('questions/edit/<int:id>', backend_views.question_edit),
    path('questions/delete/<int:id>', backend_views.question_delete),
    path('questions/activate/<int:id>', backend_views.question_activate),
    path('questions/view/<int:id>', backend_views.view_question_result),
    path('questions/<int:question_id>/addanswer', backend_views.answer_add),
    path('answers/edit/<int:id>', backend_views.answer_edit),
    path('answers/delete/<int:id>', backend_views.answer_delete),

    # Frontend
    path('', frontend_views.home),
    path('<str:event_slug>', frontend_views.enter_event),
    path('<str:event_slug>/poll/<str:poll_slug>', frontend_views.show_poll_by_slug),
    path('selected_answers/<int:poll_id>', frontend_views.selected_answers),
]
